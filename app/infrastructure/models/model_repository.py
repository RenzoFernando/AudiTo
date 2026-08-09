from __future__ import annotations

import io
import shutil
from collections.abc import Callable
from pathlib import Path

from app.domain.model_profile import ModelProfile
from app.infrastructure.system.app_paths import AppPaths


class ModelRepositoryError(RuntimeError):
    pass


class ModelRepository:
    _REQUIRED_FILES = ("config.json", "model.bin")

    def model_dir(self, profile: ModelProfile) -> Path:
        return AppPaths.models_dir() / profile.model_name

    def is_available(self, profile: ModelProfile) -> bool:
        path = self.model_dir(profile)
        marker = path / ".audito_model_complete"
        return marker.exists() and all((path / name).is_file() for name in self._REQUIRED_FILES)

    def installed_profiles(self) -> list[str]:
        return [profile.label for profile in ModelProfile if self.is_available(profile)]

    def ensure_available(self, profile: ModelProfile, status_callback: Callable[[str], None]) -> Path:
        target = self.download(profile, status_callback)
        status_callback("Cargando modelo")
        return target

    def download(self, profile: ModelProfile, status_callback: Callable[[str], None]) -> Path:
        target = self.model_dir(profile)
        if self.is_available(profile):
            status_callback("MODEL_DOWNLOAD_PROGRESS:100")
            return target
        self._download(profile, target, status_callback)
        return target

    def _download(self, profile: ModelProfile, target: Path, status_callback: Callable[[str], None]) -> None:
        try:
            from huggingface_hub import HfApi, hf_hub_download
            from tqdm.auto import tqdm
        except ImportError as exc:
            raise ModelRepositoryError("Falta el componente necesario para descargar el modelo. Reinicia AudiTo después de instalar las dependencias.") from exc

        repo_id = f"Systran/faster-whisper-{profile.model_name}"
        target.mkdir(parents=True, exist_ok=True)
        marker = target / ".audito_model_complete"
        marker.unlink(missing_ok=True)
        status_callback("MODEL_DOWNLOAD_PROGRESS:0")

        try:
            info = HfApi().model_info(repo_id=repo_id, files_metadata=True)
            files = [item for item in (info.siblings or []) if item.rfilename not in {".gitattributes", "README.md"}]
            if not files:
                raise ModelRepositoryError("No se encontraron archivos para el modelo seleccionado.")
            total_size = sum(max(0, int(item.size or 0)) for item in files)
            completed_size = 0
            completed_files = 0
            last_percent = -1

            def emit_progress(current_size: int, current_files: int) -> None:
                nonlocal last_percent
                if total_size > 0:
                    percent = int((max(0, current_size) / total_size) * 100)
                else:
                    percent = int((max(0, current_files) / max(1, len(files))) * 100)
                percent = max(0, min(99, percent))
                if percent != last_percent:
                    last_percent = percent
                    status_callback(f"MODEL_DOWNLOAD_PROGRESS:{percent}")

            for file_info in files:
                filename = str(file_info.rfilename)
                expected_size = max(0, int(file_info.size or 0))
                local_path = target / Path(filename)
                if local_path.is_file() and expected_size > 0 and local_path.stat().st_size == expected_size:
                    completed_size += expected_size
                    completed_files += 1
                    emit_progress(completed_size, completed_files)
                    continue
                base_size = completed_size
                base_files = completed_files
                output_buffer = io.StringIO()

                class DownloadProgress(tqdm):
                    def __init__(self, *args, **kwargs):
                        kwargs["file"] = output_buffer
                        kwargs["leave"] = False
                        super().__init__(*args, **kwargs)

                    def update(self, n=1):
                        result = super().update(n)
                        current_file = min(int(self.n), expected_size) if expected_size > 0 else 0
                        emit_progress(base_size + current_file, base_files)
                        return result

                hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=target,
                    force_download=False,
                    tqdm_class=DownloadProgress,
                )
                if expected_size > 0:
                    completed_size += expected_size
                elif local_path.exists():
                    completed_size += local_path.stat().st_size
                completed_files += 1
                emit_progress(completed_size, completed_files)

            if not all((target / name).is_file() for name in self._REQUIRED_FILES):
                raise ModelRepositoryError("La descarga terminó incompleta. Vuelve a intentarlo con conexión a Internet.")
            marker.write_text(profile.model_name, encoding="utf-8")
            shutil.rmtree(target / ".cache", ignore_errors=True)
            status_callback("MODEL_DOWNLOAD_PROGRESS:100")
        except ModelRepositoryError:
            raise
        except OSError as exc:
            message = str(exc).lower()
            if "space" in message or "disk full" in message or "no space" in message:
                raise ModelRepositoryError("No hay espacio suficiente para descargar el modelo de transcripción.") from exc
            raise ModelRepositoryError("No se pudo guardar el modelo de transcripción en la carpeta de AudiTo.") from exc
        except Exception as exc:
            raise ModelRepositoryError("No se pudo descargar el modelo de transcripción. Comprueba tu conexión a Internet e inténtalo nuevamente.") from exc
