from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.application.overlap_merge_service import OverlapMergeService
from app.application.transcription_guard import TranscriptionGuard
from app.constants import LIVE_CHUNK_SECONDS, LIVE_INITIAL_SECONDS, LIVE_OVERLAP_SECONDS
from app.domain.transcription_job import TranscriptionJob
from app.domain.transcription_segment import TranscriptionSegment
from app.infrastructure.audio.live_audio_buffer import LiveAudioBuffer
from app.infrastructure.exporters.txt_exporter import TxtExporter
from app.infrastructure.system.app_paths import AppPaths
from app.infrastructure.whisper.faster_whisper_engine import FasterWhisperEngine


class LiveTranscriptionError(RuntimeError):
    pass


@dataclass(frozen=True)
class LiveProcessResult:
    start_seconds: float
    end_seconds: float
    appended_segments: int


class LiveTranscriptionService:
    def __init__(
        self,
        job: TranscriptionJob,
        output_dir: Path,
        buffer: LiveAudioBuffer,
        engine: FasterWhisperEngine | None = None,
        exporter: TxtExporter | None = None,
        merge_service: OverlapMergeService | None = None,
    ) -> None:
        self._job = job
        self._buffer = buffer
        self._engine = engine or FasterWhisperEngine()
        self._exporter = exporter or TxtExporter()
        self._merge_service = merge_service or OverlapMergeService()
        self._logger = logging.getLogger(__name__)
        self._final_path = self._exporter.unique_output_path(output_dir, job.input_path)
        self._partial_path = self._exporter.start(job, self._final_path)
        self._confirmed_until = 0.0
        self._confirmed_tail: list[TranscriptionSegment] = []

    @property
    def final_path(self) -> Path:
        return self._final_path

    @property
    def partial_path(self) -> Path:
        return self._partial_path

    @property
    def confirmed_until(self) -> float:
        return self._confirmed_until

    def process_available(self, force: bool, status_callback: Callable[[str], None]) -> LiveProcessResult | None:
        available_end = self._buffer.end_seconds
        pending = available_end - self._confirmed_until
        threshold = LIVE_INITIAL_SECONDS if self._confirmed_until <= 0 else LIVE_CHUNK_SECONDS
        if not force and pending < threshold:
            return None
        if force and pending < 0.2:
            return None
        requested_start = self._confirmed_until - LIVE_OVERLAP_SECONDS if self._confirmed_until > 0 else 0.0
        if self._buffer.overflowed and requested_start < self._buffer.start_seconds - 0.05:
            raise LiveTranscriptionError("La transcripción en vivo se atrasó demasiado. La grabación continúa y el audio completo se conserva.")
        snapshot = self._buffer.snapshot(max(0.0, requested_start), available_end)
        if not snapshot.pcm or snapshot.end_seconds - snapshot.start_seconds < 0.2:
            return None
        temporary = AppPaths.temp_dir() / f"live_{uuid.uuid4().hex}.wav"
        try:
            snapshot.write_wav(temporary)
            segments, detected_language = self._engine.transcribe(
                temporary,
                self._job.model_profile,
                self._job.language_code,
                status_callback,
            )
            guard = TranscriptionGuard()
            cleaned_segments: list[TranscriptionSegment] = []
            for segment in segments:
                text = guard.clean_segment(segment.text)
                if not text:
                    self._logger.warning("Segmento repetitivo descartado en vivo: start=%.2f end=%.2f", segment.start + snapshot.start_seconds, segment.end + snapshot.start_seconds)
                    continue
                cleaned_segments.append(
                    TranscriptionSegment(
                        segment.start + snapshot.start_seconds,
                        segment.end + snapshot.start_seconds,
                        guard.finalize_segment(text),
                    )
                )
            merged = self._merge_service.merge(
                self._confirmed_tail,
                cleaned_segments,
                self._confirmed_until,
                LIVE_OVERLAP_SECONDS,
            )
            for segment in merged:
                self._exporter.append_segment(self._partial_path, segment)
            self._confirmed_tail = (self._confirmed_tail + merged)[-8:]
            self._confirmed_until = snapshot.end_seconds
            self._buffer.release_before(max(0.0, self._confirmed_until - LIVE_OVERLAP_SECONDS))
            if detected_language:
                self._logger.info("Idioma detectado en vivo: %s", detected_language)
            return LiveProcessResult(snapshot.start_seconds, snapshot.end_seconds, len(merged))
        except LiveTranscriptionError:
            raise
        except Exception as exc:
            self._logger.exception("Error en transcripción progresiva")
            raise LiveTranscriptionError(str(exc)) from exc
        finally:
            temporary.unlink(missing_ok=True)

    def finish(self, duration: float) -> Path:
        self._exporter.update_duration(self._partial_path, duration)
        self._exporter.finish(self._partial_path, self._final_path)
        self._logger.info("Transcripción progresiva finalizada: output=%s duration=%.2f", self._final_path, duration)
        return self._final_path

    def discard_output(self) -> None:
        self._exporter.discard(self._partial_path, self._final_path)
