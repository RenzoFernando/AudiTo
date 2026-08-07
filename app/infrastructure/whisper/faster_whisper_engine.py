from __future__ import annotations

import gc
import logging
import os
from collections.abc import Callable, Iterator
from pathlib import Path

from app.application.model_service import ModelService
from app.domain.model_profile import ModelProfile
from app.domain.transcription_segment import TranscriptionSegment
from app.infrastructure.models.model_repository import ModelRepository, ModelRepositoryError
from app.infrastructure.whisper.whisper_config import WhisperConfig


class WhisperEngineError(RuntimeError):
    pass


class FasterWhisperEngine:
    def __init__(self, model_repository: ModelRepository | None = None, config: WhisperConfig | None = None) -> None:
        self._logger = logging.getLogger(__name__)
        self._model = None
        self._loaded_profile: ModelProfile | None = None
        self._loaded_device: str | None = None
        self._model_service = ModelService()
        self._model_repository = model_repository or ModelRepository()
        self._config = config or WhisperConfig()

    def _create_model(self, profile: ModelProfile, status_callback: Callable[[str], None]):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise WhisperEngineError("Falta Faster-Whisper. Reinicia AudiTo después de instalar las dependencias.") from exc

        try:
            model_path = self._model_repository.ensure_available(profile, status_callback)
        except ModelRepositoryError as exc:
            raise WhisperEngineError(str(exc)) from exc
        runtime = self._model_service.preferred_runtime()
        kwargs = {
            "device": runtime.device,
            "compute_type": runtime.compute_type,
            "cpu_threads": max(1, os.cpu_count() or 2),
            "num_workers": 1,
        }
        try:
            model = WhisperModel(str(model_path), **kwargs)
            return model, runtime.device
        except Exception as first_error:
            if runtime.device != "cuda":
                raise self._friendly_error(first_error) from first_error
            self._logger.exception("Falló la inicialización CUDA. Se intentará CPU.")
            status_callback("GPU no disponible. Usando CPU")
            try:
                kwargs["device"] = "cpu"
                kwargs["compute_type"] = "int8"
                model = WhisperModel(str(model_path), **kwargs)
                return model, "cpu"
            except Exception as second_error:
                raise self._friendly_error(second_error) from second_error

    def _ensure_model(self, profile: ModelProfile, status_callback: Callable[[str], None]) -> None:
        if self._model is not None and self._loaded_profile == profile:
            return
        self.release()
        model, device = self._create_model(profile, status_callback)
        self._model = model
        self._loaded_profile = profile
        self._loaded_device = device
        self._logger.info("Modelo cargado: profile=%s model=%s device=%s", profile.label, profile.model_name, device)

    def transcribe(
        self,
        audio_path: Path,
        profile: ModelProfile,
        language_code: str | None,
        status_callback: Callable[[str], None],
    ) -> tuple[Iterator[TranscriptionSegment], str | None]:
        self._ensure_model(profile, status_callback)
        status_callback("Transcribiendo")
        try:
            segments, info = self._model.transcribe(
                str(audio_path),
                **self._config.transcribe_kwargs(language_code, profile.beam_size),
            )
            return self._safe_segments(segments), getattr(info, "language", None)
        except Exception as exc:
            raise self._friendly_error(exc) from exc

    def _safe_segments(self, segments: Iterator) -> Iterator[TranscriptionSegment]:
        try:
            for segment in segments:
                yield TranscriptionSegment(float(segment.start), float(segment.end), str(segment.text).strip())
        except Exception as exc:
            raise self._friendly_error(exc) from exc

    def release(self) -> None:
        self._model = None
        self._loaded_profile = None
        self._loaded_device = None
        gc.collect()

    def _friendly_error(self, exc: Exception) -> WhisperEngineError:
        message = str(exc).lower()
        if "out of memory" in message or "bad allocation" in message or "memory" in message:
            return WhisperEngineError("No hay suficiente memoria para iniciar la transcripción con este modelo.")
        if "download" in message or "huggingface" in message or "connection" in message or "network" in message:
            return WhisperEngineError("AudiTo necesita descargar el modelo de transcripción. Conéctate a internet y vuelve a intentarlo.")
        if "cuda" in message or "cudnn" in message or "cublas" in message:
            return WhisperEngineError("No fue posible utilizar la GPU. AudiTo intentó cambiar a CPU, pero el modelo no pudo iniciarse.")
        return WhisperEngineError("No fue posible transcribir este audio. Revisa que el archivo sea válido e inténtalo nuevamente.")
