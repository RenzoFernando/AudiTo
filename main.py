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
    from app.infrastructure.system.app_paths import AppPaths

    AppPaths.cleanup_legacy_layout()
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("HF_HOME", str(AppPaths.huggingface_cache_dir()))
    os.environ.setdefault("HF_HUB_CACHE", str(AppPaths.huggingface_cache_dir() / "hub"))


def _ensure_dependencies() -> None:
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        return
    required = ("PySide6", "faster_whisper", "sounddevice", "huggingface_hub", "av", "groq")
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
    from PySide6.QtCore import QEvent, QObject, QTimer, Qt
    from PySide6.QtGui import QCursor, QIcon
    from PySide6.QtWidgets import QApplication, QDialog
    from app.app_meta import APP_COMPANY_NAME
    from app.constants import APP_NAME
    from app.infrastructure.system.app_paths import AppPaths
    from app.presentation.main_window import MainWindow

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    application = QApplication(sys.argv)

    def center_window(widget) -> None:
        try:
            parent = widget.parentWidget()
            if parent is not None and parent.isVisible():
                screen = parent.screen()
                target_center = parent.frameGeometry().center()
            else:
                screen = application.screenAt(QCursor.pos()) or application.primaryScreen()
                if screen is None:
                    return
                target_center = screen.availableGeometry().center()
            frame = widget.frameGeometry()
            frame.moveCenter(target_center)
            if screen is not None:
                available = screen.availableGeometry()
                x = max(available.left(), min(frame.left(), available.right() - frame.width() + 1))
                y = max(available.top(), min(frame.top(), available.bottom() - frame.height() + 1))
                widget.move(x, y)
            else:
                widget.move(frame.topLeft())
        except RuntimeError:
            return

    class DialogCenterFilter(QObject):
        def eventFilter(self, watched, event) -> bool:
            if event.type() == QEvent.Type.Show and isinstance(watched, QDialog):
                QTimer.singleShot(0, lambda target=watched: center_window(target))
            return super().eventFilter(watched, event)

    dialog_center_filter = DialogCenterFilter(application)
    application.installEventFilter(dialog_center_filter)
    application.setApplicationName(APP_NAME)
    application.setOrganizationName(APP_COMPANY_NAME)
    application.setStyle("Fusion")
    AppPaths.cleanup_temp()
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    icon_path = AppPaths.app_icon_path()
    if icon_path.exists():
        application.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    center_window(window)
    window.show()
    QTimer.singleShot(0, lambda: center_window(window))
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())


