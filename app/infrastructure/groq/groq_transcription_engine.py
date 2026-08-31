from __future__ import annotations

import os
import shutil
import threading
from collections.abc import Callable
from pathlib import Path

from app.domain.transcription_segment import TranscriptionSegment
from app.infrastructure.audio.flac_chunker import FlacChunker, FlacChunkerError, FlacChunkingCancelled
from app.infrastructure.groq.groq_usage_tracker import GroqUsageTracker
from app.infrastructure.system.app_paths import AppPaths


class GroqTranscriptionError(RuntimeError):
    pass


class GroqTranscriptionCancelled(RuntimeError):
    pass


class GroqTranscriptionEngine:
    MODEL = "whisper-large-v3"

    def __init__(self, chunker: FlacChunker | None = None, usage_tracker: GroqUsageTracker | None = None) -> None:
        self._chunker = chunker or FlacChunker()
        self._usage_tracker = usage_tracker or GroqUsageTracker()

    def transcribe(
        self,
        audio_path: Path,
        language_code: str | None,
        api_key: str | None,
        status_callback: Callable[[str], None],
        progress_callback: Callable[[int], None],
        cancel_event: threading.Event,
        duration: float | None = None,
        segment_callback: Callable[[list[TranscriptionSegment]], None] | None = None,
    ) -> tuple[list[TranscriptionSegment], str | None]:
        key = str(api_key or os.environ.get("GROQ_API_KEY", "")).strip()
        if not key:
            raise GroqTranscriptionError("Configura una API key de Groq para usar el perfil Online.")
        try:
            import groq
            from groq import Groq
        except ImportError as exc:
            raise GroqTranscriptionError("Falta el cliente de Groq. Reinicia AudiTo después de instalar las dependencias.") from exc

        if cancel_event.is_set():
            raise GroqTranscriptionCancelled()

        temp_root = AppPaths.temp_dir()
        chunks = []
        work_dir: Path | None = None
        try:
            chunks = self._chunker.prepare(
                audio_path,
                temp_root,
                cancel_event,
                status_callback,
                progress_callback,
                duration,
            )
            work_dir = chunks[0].path.parent
            client = Groq(api_key=key, timeout=120.0, max_retries=2)
            segments: list[TranscriptionSegment] = []
            detected_language: str | None = None
            total_chunks = len(chunks)
            previous_prompt: str | None = None
            for index, chunk in enumerate(chunks):
                if cancel_event.is_set():
                    raise GroqTranscriptionCancelled()
                status_callback("GROQ_TRANSCRIBING")
                request = {
                    "model": self.MODEL,
                    "response_format": "verbose_json",
                    "timestamp_granularities": ["segment"],
                    "temperature": 0.0,
                }
                if language_code:
                    request["language"] = language_code
                if previous_prompt:
                    request["prompt"] = previous_prompt
                try:
                    with chunk.path.open("rb") as audio_file:
                        request["file"] = (chunk.path.name, audio_file.read())
                        raw_response = client.audio.transcriptions.with_raw_response.create(**request)
                        response = raw_response.parse()
                    self._usage_tracker.record_success(
                        key,
                        max(0.0, chunk.end_seconds - chunk.start_seconds),
                        raw_response.headers,
                    )
                except groq.AuthenticationError as exc:
                    raise GroqTranscriptionError("La API key de Groq no es válida o fue rechazada.") from exc
                except groq.RateLimitError as exc:
                    raise GroqTranscriptionError("Se alcanzó el límite gratuito de Groq. Espera a que se renueve la cuota e inténtalo nuevamente.") from exc
                except groq.APIConnectionError as exc:
                    raise GroqTranscriptionError("No se pudo conectar con Groq. Revisa tu conexión a Internet e inténtalo nuevamente.") from exc
                except groq.BadRequestError as exc:
                    raise GroqTranscriptionError("Groq rechazó el audio preparado. Revisa que el archivo sea válido e inténtalo nuevamente.") from exc
                except groq.APIStatusError as exc:
                    if getattr(exc, "status_code", None) == 413:
                        raise GroqTranscriptionError("El archivo preparado supera el límite permitido por Groq.") from exc
                    raise GroqTranscriptionError("Groq no pudo completar la transcripción en este momento. Inténtalo nuevamente.") from exc
                except Exception as exc:
                    raise GroqTranscriptionError("No se pudo completar la transcripción online con Groq.") from exc

                if cancel_event.is_set():
                    raise GroqTranscriptionCancelled()
                response_language = getattr(response, "language", None)
                if response_language and not detected_language:
                    detected_language = str(response_language)
                response_segments = getattr(response, "segments", None) or []
                chunk_segments: list[TranscriptionSegment] = []
                for raw_segment in response_segments:
                    start = self._field(raw_segment, "start", 0.0)
                    end = self._field(raw_segment, "end", start)
                    text = str(self._field(raw_segment, "text", "") or "").strip()
                    if not text:
                        continue
                    chunk_segments.append(
                        TranscriptionSegment(
                            float(start) + chunk.start_seconds,
                            float(end) + chunk.start_seconds,
                            text,
                        )
                    )
                response_text = str(getattr(response, "text", "") or "").strip()
                if not chunk_segments and response_text:
                    chunk_segments.append(TranscriptionSegment(chunk.start_seconds, chunk.end_seconds, response_text))
                segments.extend(chunk_segments)
                if segment_callback is not None and chunk_segments:
                    segment_callback(chunk_segments)
                if response_text:
                    words = response_text.split()
                    previous_prompt = " ".join(words[-60:])
                progress_callback(min(95, 15 + int(((index + 1) / total_chunks) * 80)))
            return segments, detected_language
        except FlacChunkingCancelled as exc:
            raise GroqTranscriptionCancelled() from exc
        except FlacChunkerError as exc:
            raise GroqTranscriptionError(str(exc)) from exc
        finally:
            if work_dir is None and chunks:
                work_dir = chunks[0].path.parent
            if work_dir is not None:
                shutil.rmtree(work_dir, ignore_errors=True)

    def _field(self, value, name: str, default):
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)
