from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path

from app.domain.transcription_job import TranscriptionJob
from app.domain.transcription_result import TranscriptionResult
from app.infrastructure.exporters.txt_exporter import TxtExporter
from app.infrastructure.whisper.faster_whisper_engine import FasterWhisperEngine


class TranscriptionCancelled(RuntimeError):
    pass


class TranscriptionService:
    def __init__(self, engine: FasterWhisperEngine | None = None, exporter: TxtExporter | None = None) -> None:
        self._engine = engine or FasterWhisperEngine()
        self._exporter = exporter or TxtExporter()
        self._logger = logging.getLogger(__name__)

    def transcribe_job(
        self,
        job: TranscriptionJob,
        output_dir: Path,
        cancel_event: threading.Event,
        progress_callback: Callable[[int], None],
        status_callback: Callable[[str], None],
    ) -> TranscriptionResult:
        final_path = self._exporter.unique_output_path(output_dir, job.input_path)
        job.output_path = final_path
        status_callback("Preparando audio")
        partial_path = self._exporter.start(job, final_path)
        segment_count = 0
        detected_language = None
        try:
            segments, detected_language = self._engine.transcribe(
                job.input_path,
                job.model_profile,
                job.language_code,
                status_callback,
            )
            for segment in segments:
                if cancel_event.is_set():
                    raise TranscriptionCancelled("Transcripción cancelada")
                self._exporter.append_segment(partial_path, float(segment.start), str(segment.text))
                segment_count += 1
                if job.duration and job.duration > 0:
                    progress = min(99, int((float(segment.end) / job.duration) * 100))
                    progress_callback(progress)
            if cancel_event.is_set():
                raise TranscriptionCancelled("Transcripción cancelada")
            status_callback("Guardando")
            self._exporter.finish(partial_path, final_path)
            progress_callback(100)
            self._logger.info("Transcripción completada: input=%s output=%s segments=%s", job.input_path, final_path, segment_count)
            return TranscriptionResult(final_path, job.duration, detected_language, segment_count)
        except TranscriptionCancelled:
            self._logger.info("Transcripción cancelada: input=%s partial=%s", job.input_path, partial_path)
            raise
        except Exception:
            self._logger.exception("Error transcribiendo %s", job.input_path)
            raise
