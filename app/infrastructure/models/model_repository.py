from __future__ import annotations

import io
import json
import shutil
import threading
from collections.abc import Callable
from pathlib import Path

from app.domain.model_profile import ModelProfile
from app.infrastructure.system.app_paths import AppPaths


class ModelRepositoryError(RuntimeError):
    pass


class ModelDownloadCancelled(ModelRepositoryError):
    pass


class ModelRepository:
    _COMPLETE_MARKER = ".audito_model_complete"
    _MANIFEST_FILE = ".audito_model_manifest.json"
    _INVALID_MARKER = ".audito_model_invalid"
    _PARTIAL_MARKER = ".audito_model_partial"
    _MIN_MODEL_BIN_SIZE = 1024 * 1024

    def _required_files(self, profile: ModelProfile) -> tuple[str, ...]:
        if profile.model_name == "large-v3":
            return ("config.json", "model.bin", "tokenizer.json", "vocabulary.json", "preprocessor_config.json")
        return ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")

    def model_dir(self, profile: ModelProfile) -> Path:
        return AppPaths.models_dir() / profile.model_name

    def is_available(self, profile: ModelProfile) -> bool:
        return self._validate_model(profile)

    def installed_profiles(self) -> list[str]:
        return [profile.label for profile in ModelProfile if self.is_available(profile)]

    def validate_installed_models(self) -> list[str]:
        AppPaths.models_dir().mkdir(parents=True, exist_ok=True)
        invalid: list[str] = []
        for profile in ModelProfile:
            target = self.model_dir(profile)
            if not target.exists():
                continue
            partial_marker = target / self._PARTIAL_MARKER
            if partial_marker.exists():
                try:
                    (target / self._COMPLETE_MARKER).unlink(missing_ok=True)
                    (target / self._INVALID_MARKER).unlink(missing_ok=True)
                except OSError:
                    pass
                continue
            try:
                has_content = any(target.iterdir())
            except OSError:
                has_content = True
            if not has_content:
                continue
            if self._validate_model(profile):
                (target / self._INVALID_MARKER).unlink(missing_ok=True)
                continue
            invalid.append(profile.label)
            try:
                (target / self._COMPLETE_MARKER).unlink(missing_ok=True)
                (target / self._INVALID_MARKER).write_text(profile.model_name, encoding="utf-8")
            except OSError:
                pass
        return invalid

    def ensure_available(self, profile: ModelProfile, status_callback: Callable[[str], None]) -> Path:
        target = self.download(profile, status_callback)
        status_callback("Cargando modelo")
        return target

    def download(
        self,
        profile: ModelProfile,
        status_callback: Callable[[str], None],
        cancel_event: threading.Event | None = None,
    ) -> Path:
        target = self.model_dir(profile)
        if self.is_available(profile):
            status_callback("MODEL_DOWNLOAD_PROGRESS:100")
            return target
        if self._is_cancelled(cancel_event):
            raise ModelDownloadCancelled("Descarga de modelo cancelada")
        if (target / self._INVALID_MARKER).exists():
            shutil.rmtree(target, ignore_errors=True)
        self._download(profile, target, status_callback, cancel_event)
        return target

    def _validate_model(self, profile: ModelProfile) -> bool:
        target = self.model_dir(profile)
        if not target.is_dir() or (target / self._INVALID_MARKER).exists() or (target / self._PARTIAL_MARKER).exists():
            return False
        marker = target / self._COMPLETE_MARKER
        if not marker.is_file():
            return False
        try:
            if marker.read_text(encoding="utf-8").strip() != profile.model_name:
                return False
        except OSError:
            return False
        for name in self._required_files(profile):
            path = target / name
            try:
                if not path.is_file() or path.stat().st_size <= 0:
                    return False
            except OSError:
                return False
        try:
            if (target / "model.bin").stat().st_size < self._MIN_MODEL_BIN_SIZE:
                return False
            config = json.loads((target / "config.json").read_text(encoding="utf-8"))
            if not isinstance(config, dict) or not config:
                return False
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False

        manifest_path = target / self._MANIFEST_FILE
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                files = manifest.get("files")
                if not isinstance(files, dict) or not files:
                    return False
                for filename, raw_size in files.items():
                    path = target / str(filename)
                    expected_size = max(0, int(raw_size or 0))
                    if not path.is_file():
                        return False
                    actual_size = path.stat().st_size
                    if actual_size <= 0:
                        return False
                    if expected_size > 0 and actual_size != expected_size:
                        return False
            except (OSError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
                return False
        return True

    def _download(
        self,
        profile: ModelProfile,
        target: Path,
        status_callback: Callable[[str], None],
        cancel_event: threading.Event | None,
    ) -> None:
        try:
            from huggingface_hub import HfApi, hf_hub_download
            from tqdm.auto import tqdm
        except ImportError as exc:
            raise ModelRepositoryError("Falta el componente necesario para descargar el modelo. Reinicia AudiTo después de instalar las dependencias.") from exc

        repo_id = f"Systran/faster-whisper-{profile.model_name}"
        target.mkdir(parents=True, exist_ok=True)
        marker = target / self._COMPLETE_MARKER
        manifest_path = target / self._MANIFEST_FILE
        invalid_marker = target / self._INVALID_MARKER
        partial_marker = target / self._PARTIAL_MARKER
        marker.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        invalid_marker.unlink(missing_ok=True)
        try:
            partial_marker.write_text(profile.model_name, encoding="utf-8")
        except OSError as exc:
            raise ModelRepositoryError("No se pudo guardar el modelo de transcripción en la carpeta de AudiTo.") from exc
        status_callback("MODEL_DOWNLOAD_PREPARING")

        try:
            self._raise_if_cancelled(cancel_event)
            info = HfApi().model_info(repo_id=repo_id, files_metadata=True, timeout=10)
            self._raise_if_cancelled(cancel_event)
            files = [item for item in (info.siblings or []) if item.rfilename not in {".gitattributes", "README.md"}]
            if not files:
                raise ModelRepositoryError("No se encontraron archivos para el modelo seleccionado.")
            total_size = sum(max(0, int(item.size or 0)) for item in files)
            completed_size = 0
            completed_files = 0
            last_percent = -1
            manifest_files: dict[str, int] = {}

            def emit_progress(current_size: int, current_files: int) -> None:
                nonlocal last_percent
                self._raise_if_cancelled(cancel_event)
                if total_size > 0:
                    percent = int((max(0, current_size) / total_size) * 100)
                else:
                    percent = int((max(0, current_files) / max(1, len(files))) * 100)
                percent = max(0, min(99, percent))
                if percent != last_percent:
                    last_percent = percent
                    status_callback(f"MODEL_DOWNLOAD_PROGRESS:{percent}")

            status_callback("MODEL_DOWNLOAD_PROGRESS:0")
            for file_info in files:
                self._raise_if_cancelled(cancel_event)
                filename = str(file_info.rfilename)
                expected_size = max(0, int(file_info.size or 0))
                local_path = target / Path(filename)
                if local_path.is_file() and expected_size > 0 and local_path.stat().st_size == expected_size:
                    completed_size += expected_size
                    completed_files += 1
                    manifest_files[filename] = expected_size
                    emit_progress(completed_size, completed_files)
                    continue
                base_size = completed_size
                base_files = completed_files
                output_buffer = io.StringIO()
                repository = self

                class DownloadProgress(tqdm):
                    def __init__(self, *args, **kwargs):
                        kwargs["file"] = output_buffer
                        kwargs["leave"] = False
                        super().__init__(*args, **kwargs)

                    def update(self, n=1):
                        repository._raise_if_cancelled(cancel_event)
                        result = super().update(n)
                        current_file = min(int(self.n), expected_size) if expected_size > 0 else 0
                        emit_progress(base_size + current_file, base_files)
                        return result

                hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=target,
                    force_download=False,
                    etag_timeout=10,
                    tqdm_class=DownloadProgress,
                )
                self._raise_if_cancelled(cancel_event)
                actual_size = local_path.stat().st_size if local_path.exists() else 0
                if expected_size > 0:
                    completed_size += expected_size
                    manifest_files[filename] = expected_size
                else:
                    completed_size += actual_size
                    manifest_files[filename] = actual_size
                completed_files += 1
                emit_progress(completed_size, completed_files)

            self._raise_if_cancelled(cancel_event)
            if not all((target / name).is_file() for name in self._required_files(profile)):
                raise ModelRepositoryError("La descarga terminó incompleta. Vuelve a intentarlo con conexión a Internet.")
            manifest_path.write_text(
                json.dumps(
                    {
                        "repository": repo_id,
                        "profile": profile.model_name,
                        "files": manifest_files,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            marker.write_text(profile.model_name, encoding="utf-8")
            partial_marker.unlink(missing_ok=True)
            shutil.rmtree(target / ".cache", ignore_errors=True)
            if not self._validate_model(profile):
                marker.unlink(missing_ok=True)
                partial_marker.write_text(profile.model_name, encoding="utf-8")
                raise ModelRepositoryError("La descarga terminó incompleta. Vuelve a intentarlo con conexión a Internet.")
            status_callback("MODEL_DOWNLOAD_PROGRESS:100")
        except ModelDownloadCancelled:
            marker.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)
            try:
                partial_marker.write_text(profile.model_name, encoding="utf-8")
            except OSError:
                pass
            raise
        except ModelRepositoryError:
            raise
        except OSError as exc:
            if self._is_cancelled(cancel_event):
                raise ModelDownloadCancelled("Descarga de modelo cancelada") from exc
            message = str(exc).lower()
            if "space" in message or "disk full" in message or "no space" in message:
                raise ModelRepositoryError("No hay espacio suficiente para descargar el modelo de transcripción.") from exc
            raise ModelRepositoryError("No se pudo guardar el modelo de transcripción en la carpeta de AudiTo.") from exc
        except Exception as exc:
            if self._is_cancelled(cancel_event):
                raise ModelDownloadCancelled("Descarga de modelo cancelada") from exc
            raise ModelRepositoryError("No se pudo descargar el modelo de transcripción. Comprueba tu conexión a Internet e inténtalo nuevamente.") from exc

    def _raise_if_cancelled(self, cancel_event: threading.Event | None) -> None:
        if self._is_cancelled(cancel_event):
            raise ModelDownloadCancelled("Descarga de modelo cancelada")

    def _is_cancelled(self, cancel_event: threading.Event | None) -> bool:
        return cancel_event is not None and cancel_event.is_set()
