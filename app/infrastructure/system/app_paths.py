from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from app.constants import APP_NAME


class AppPaths:
    @staticmethod
    def resource_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[3]

    @staticmethod
    def user_data_dir() -> Path:
        location = ""
        try:
            from PySide6.QtCore import QStandardPaths

            location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        except Exception:
            if sys.platform == "win32":
                location = os.environ.get("LOCALAPPDATA", "")
            else:
                location = os.environ.get("XDG_DATA_HOME", "")
        if location:
            path = Path(location)
        elif sys.platform == "win32":
            path = Path.home() / "AppData" / "Local"
        else:
            path = Path.home() / ".local" / "share"
        if path.name.casefold() != APP_NAME.casefold():
            path = path / APP_NAME
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
    def logs_dir(cls) -> Path:
        path = cls.user_data_dir() / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

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
