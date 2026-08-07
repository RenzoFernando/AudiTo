from __future__ import annotations

import gc
import logging
import os
from collections.abc import Callable, Iterator
from pathlib import Path

from app.application.model_service import ModelService
from app.domain.model_profile import ModelProfile
from app.infrastructure.paths import models_dir


class WhisperEngineError(RuntimeError):
    pass


class FasterWhisperEngine:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._model = None
        self._loaded_profile: ModelProfile | None = None
        self._loaded_device: str | None = None
        self._model_service = ModelService()

    def _model_cache_path(self, profile: ModelProfile) -> Path:
        return models_dir() / "cache" / f"models--Systran--faster-whisper-{profile.model_name}"

    def _model_is_cached(self, profile: ModelProfile) -> bool:
        snapshots = self._model_cache_path(profile) / "snapshots"
        if not snapshots.exists():
            return False
        return any(path.is_dir() and (path / "model.bin").exists() for path in snapshots.iterdir())

    def _create_model(self, profile: ModelProfile, status_callback: Callable[[str], None]):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise WhisperEngineError("Falta Faster-Whisper. Reinicia la aplicación después de instalar las dependencias.") from exc

        runtime = self._model_service.preferred_runtime()
        if self._model_is_cached(profile):
            status_callback("Cargando modelo")
        else:
            status_callback("Descargando modelo por primera vez")
        cache = models_dir() / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        kwargs = {
            "device": runtime.device,
            "compute_type": runtime.compute_type,
            "download_root": str(cache),
            "cpu_threads": max(1, os.cpu_count() or 2),
            "num_workers": 1,
        }
        try:
            model = WhisperModel(profile.model_name, **kwargs)
            return model, runtime.device
        except Exception as first_error:
            if runtime.device != "cuda":
                raise self._friendly_error(first_error) from first_error
            self._logger.exception("Falló la inicialización CUDA. Se intentará CPU.")
            status_callback("GPU no disponible. Usando CPU")
            try:
                kwargs["device"] = "cpu"
                kwargs["compute_type"] = "int8"
                model = WhisperModel(profile.model_name, **kwargs)
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
    ) -> tuple[Iterator, str | None]:
        self._ensure_model(profile, status_callback)
        status_callback("Transcribiendo")
        try:
            segments, info = self._model.transcribe(
                str(audio_path),
                language=language_code,
                beam_size=profile.beam_size,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 300},
                condition_on_previous_text=False,
                temperature=[0.0, 0.2, 0.4, 0.6],
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                repetition_penalty=1.05,
                no_repeat_ngram_size=5,
                word_timestamps=False,
            )
            return self._safe_segments(segments), getattr(info, "language", None)
        except Exception as exc:
            raise self._friendly_error(exc) from exc

    def _safe_segments(self, segments: Iterator) -> Iterator:
        try:
            yield from segments
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
            return WhisperEngineError("No hay suficiente memoria para este perfil. Prueba nuevamente con un perfil más ligero.")
        if "download" in message or "huggingface" in message or "connection" in message or "network" in message:
            return WhisperEngineError("No se pudo obtener el modelo. La primera descarga necesita conexión a internet.")
        if "cuda" in message or "cudnn" in message or "cublas" in message:
            return WhisperEngineError("No fue posible utilizar la GPU. La aplicación intentó cambiar a CPU, pero el modelo no pudo iniciarse.")
        return WhisperEngineError("No fue posible transcribir este audio. Revisa el archivo o prueba con un perfil diferente.")
