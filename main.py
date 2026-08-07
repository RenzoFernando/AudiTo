from __future__ import annotations

import importlib.util
import logging
import os
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _prepare_environment() -> None:
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def _ensure_dependencies() -> None:
    if getattr(sys, "frozen", False):
        return
    required = ("PySide6", "faster_whisper")
    missing = [module for module in required if importlib.util.find_spec(module) is None]
    if not missing:
        return
    requirements = _project_root() / "requirements.txt"
    print("Preparando AudiTo por primera vez...")
    print("Instalando dependencias necesarias. Esto solo debería ocurrir una vez.")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements)])
    except Exception:
        print("No fue posible instalar las dependencias automáticamente.")
        print(f"Ejecuta: {sys.executable} -m pip install -r {requirements}")
        raise SystemExit(1)
    os.execv(sys.executable, [sys.executable, str(Path(__file__).resolve())])


def main() -> int:
    _prepare_environment()
    _ensure_dependencies()
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from app.constants import APP_NAME
    from app.infrastructure.logging_setup import configure_logging
    from app.presentation.main_window import MainWindow

    configure_logging()
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    application = QApplication(sys.argv)
    application.setApplicationName(APP_NAME)
    application.setOrganizationName(APP_NAME)
    application.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
