from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path

from app.application.transcription_guard import TranscriptionGuard
from app.domain.transcription_job import TranscriptionJob
from app.domain.transcription_result import TranscriptionResult
from app.domain.transcription_segment import TranscriptionSegment
from app.infrastructure.exporters.txt_exporter import TxtExporter
from app.infrastructure.groq.groq_transcription_engine import GroqTranscriptionCancelled, GroqTranscriptionEngine
from app.infrastructure.whisper.faster_whisper_engine import FasterWhisperEngine


class TranscriptionCancelled(RuntimeError):
    pass


class TranscriptionService:
    def __init__(
        self,
        engine: FasterWhisperEngine | None = None,
        exporter: TxtExporter | None = None,
        online_engine: GroqTranscriptionEngine | None = None,
    ) -> None:
        self._engine = engine or FasterWhisperEngine()
        self._online_engine = online_engine or GroqTranscriptionEngine()
        self._exporter = exporter or TxtExporter()
        self._logger = logging.getLogger(__name__)

    def transcribe_job(
        self,
        job: TranscriptionJob,
        output_dir: Path,
        cancel_event: threading.Event,
        progress_callback: Callable[[int], None],
        status_callback: Callable[[str], None],
        output_name: str | None = None,
        timestamps_enabled: bool = True,
        groq_api_key: str | None = None,
    ) -> TranscriptionResult:
        if cancel_event.is_set():
            raise TranscriptionCancelled("Transcripción cancelada")
        final_path = self._exporter.unique_output_path(output_dir, job.input_path, output_name)
        job.output_path = final_path
        status_callback("Preparando audio")
        partial_path = self._exporter.start(job, final_path, timestamps_enabled)
        guard = TranscriptionGuard()
        segment_count = 0
        filtered_count = 0
        detected_language = None
        last_progress = 0

        def report_progress(value: int) -> None:
            nonlocal last_progress
            normalized = max(0, min(100, int(value)))
            if normalized < last_progress:
                return
            last_progress = normalized
            progress_callback(normalized)

        def process_segment(segment: TranscriptionSegment, update_progress: bool) -> None:
            nonlocal segment_count, filtered_count
            if cancel_event.is_set():
                raise TranscriptionCancelled("Transcripción cancelada")
            original_text = segment.text
            text = guard.clean_segment(original_text)
            if original_text and not text:
                filtered_count += 1
                self._logger.warning("Segmento repetitivo descartado: input=%s start=%.2f end=%.2f", job.input_path, segment.start, segment.end)
            elif text:
                if text != " ".join(original_text.split()):
                    filtered_count += 1
                    self._logger.warning("Repetición interna reducida: input=%s start=%.2f end=%.2f", job.input_path, segment.start, segment.end)
                cleaned = TranscriptionSegment(segment.start, segment.end, text)
                self._exporter.append_segment(partial_path, cleaned)
            segment_count += 1
            if update_progress and job.duration and job.duration > 0:
                report_progress(min(99, int((segment.end / job.duration) * 100)))

        def process_online_segments(segments: list[TranscriptionSegment]) -> None:
            for segment in segments:
                process_segment(segment, False)

        try:
            if cancel_event.is_set():
                raise TranscriptionCancelled("Transcripción cancelada")
            if job.online:
                try:
                    _, detected_language = self._online_engine.transcribe(
                        job.input_path,
                        job.language_code,
                        groq_api_key,
                        status_callback,
                        report_progress,
                        cancel_event,
                        job.duration,
                        process_online_segments,
                    )
                except GroqTranscriptionCancelled as exc:
                    raise TranscriptionCancelled("Transcripción cancelada") from exc
            else:
                segments, detected_language = self._engine.transcribe(
                    job.input_path,
                    job.model_profile,
                    job.language_code,
                    status_callback,
                )
                if cancel_event.is_set():
                    raise TranscriptionCancelled("Transcripción cancelada")
                for segment in segments:
                    process_segment(segment, True)
            if cancel_event.is_set():
                raise TranscriptionCancelled("Transcripción cancelada")
            status_callback("Guardando")
            self._exporter.finish(partial_path, final_path)
            report_progress(100)
            self._logger.info(
                "Transcripción completada: input=%s output=%s segments=%s filtered=%s online=%s",
                job.input_path,
                final_path,
                segment_count,
                filtered_count,
                job.online,
            )
            return TranscriptionResult(final_path, job.duration, detected_language, segment_count)
        except TranscriptionCancelled:
            try:
                self._exporter.flush(partial_path)
            except Exception:
                self._logger.exception("No fue posible vaciar el bloque pendiente al cancelar %s", job.input_path)
            self._logger.info("Transcripción cancelada: input=%s partial=%s", job.input_path, partial_path)
            raise
        except Exception:
            try:
                self._exporter.flush(partial_path)
            except Exception:
                self._logger.exception("No fue posible vaciar el bloque pendiente tras el error de %s", job.input_path)
            self._logger.exception("Error transcribiendo %s", job.input_path)
            raise
