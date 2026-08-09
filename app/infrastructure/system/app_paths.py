from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from app.app_meta import APP_DATA_APP_DIR_NAME, APP_DATA_ROOT_DIR_NAME


class AppPaths:
    @staticmethod
    def resource_dir() -> Path:
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS).resolve()
        return Path(__file__).resolve().parents[3]

    @staticmethod
    def user_data_dir() -> Path:
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
        path = base / APP_DATA_ROOT_DIR_NAME / APP_DATA_APP_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def transcriptions_dir(cls) -> Path:
        path = cls.user_data_dir() / "Transcripciones"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def recordings_dir(cls) -> Path:
        path = cls.user_data_dir() / "Grabaciones"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def models_dir(cls) -> Path:
        path = cls.user_data_dir() / "models"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def cache_dir(cls) -> Path:
        path = cls.user_data_dir() / "cache"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def huggingface_cache_dir(cls) -> Path:
        path = cls.cache_dir() / "huggingface"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def logs_dir(cls) -> Path:
        path = cls.user_data_dir() / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def error_log_file(cls) -> Path:
        return cls.logs_dir() / "error.log"

    @classmethod
    def temp_dir(cls) -> Path:
        path = cls.user_data_dir() / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def config_dir(cls) -> Path:
        path = cls.user_data_dir() / "config"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def settings_file(cls) -> Path:
        return cls.config_dir() / "settings.json"

    @classmethod
    def assets_dir(cls) -> Path:
        return cls.resource_dir() / "assets"

    @classmethod
    def ffmpeg_dir(cls) -> Path:
        return cls.resource_dir() / "ffmpeg"

    @classmethod
    def app_icon_path(cls) -> Path:
        return cls.assets_dir() / "icon.png"

    @classmethod
    def cleanup_temp(cls) -> None:
        directory = cls.temp_dir()
        for path in directory.iterdir():
            try:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)
            except Exception:
                pass
