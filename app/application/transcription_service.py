from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path

from app.application.transcription_guard import TranscriptionGuard
from app.constants import TIMESTAMP_BLOCK_SECONDS
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
        guard = TranscriptionGuard()
        segment_count = 0
        filtered_count = 0
        detected_language = None
        chunk_start: float | None = None
        chunk_end: float | None = None
        chunk_text: list[str] = []

        def flush_chunk() -> None:
            nonlocal chunk_start, chunk_end, chunk_text
            if chunk_start is None or not chunk_text:
                return
            block = guard.finalize_block(" ".join(chunk_text))
            if block:
                self._exporter.append_segment(partial_path, chunk_start, block)
            chunk_start = None
            chunk_end = None
            chunk_text = []

        try:
            segments, detected_language = self._engine.transcribe(
                job.input_path,
                job.model_profile,
                job.language_code,
                status_callback,
            )
            for segment in segments:
                if cancel_event.is_set():
                    flush_chunk()
                    raise TranscriptionCancelled("Transcripción cancelada")
                start = float(segment.start)
                end = float(segment.end)
                original_text = str(segment.text).strip()
                text = guard.clean_segment(original_text)
                if original_text and not text:
                    filtered_count += 1
                    self._logger.warning("Segmento repetitivo descartado: input=%s start=%.2f end=%.2f", job.input_path, start, end)
                elif text:
                    if text != " ".join(original_text.split()):
                        filtered_count += 1
                        self._logger.warning("Repetición interna reducida: input=%s start=%.2f end=%.2f", job.input_path, start, end)
                    if chunk_start is None:
                        chunk_start = start
                    chunk_end = end
                    chunk_text.append(text)
                    if chunk_end - chunk_start >= TIMESTAMP_BLOCK_SECONDS:
                        flush_chunk()
                segment_count += 1
                if job.duration and job.duration > 0:
                    progress = min(99, int((end / job.duration) * 100))
                    progress_callback(progress)
            flush_chunk()
            if cancel_event.is_set():
                raise TranscriptionCancelled("Transcripción cancelada")
            status_callback("Guardando")
            self._exporter.finish(partial_path, final_path)
            progress_callback(100)
            self._logger.info(
                "Transcripción completada: input=%s output=%s segments=%s filtered=%s",
                job.input_path,
                final_path,
                segment_count,
                filtered_count,
            )
            return TranscriptionResult(final_path, job.duration, detected_language, segment_count)
        except TranscriptionCancelled:
            flush_chunk()
            self._logger.info("Transcripción cancelada: input=%s partial=%s", job.input_path, partial_path)
            raise
        except Exception:
            try:
                flush_chunk()
            except Exception:
                pass
            self._logger.exception("Error transcribiendo %s", job.input_path)
            raise
