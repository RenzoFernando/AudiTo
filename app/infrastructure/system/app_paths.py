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
    def others_dir(cls) -> Path:
        path = cls.user_data_dir() / "Otros"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def models_dir(cls) -> Path:
        path = cls.others_dir() / "models"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def cache_dir(cls) -> Path:
        path = cls.others_dir() / "cache"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def huggingface_cache_dir(cls) -> Path:
        path = cls.cache_dir() / "huggingface"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def temp_dir(cls) -> Path:
        path = cls.others_dir() / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def settings_file(cls) -> Path:
        return cls.others_dir() / "settings.json"

    @classmethod
    def assets_dir(cls) -> Path:
        return cls.resource_dir() / "assets"

    @classmethod
    def app_icon_path(cls) -> Path:
        return cls.assets_dir() / "icon.png"

    @classmethod
    def cleanup_legacy_layout(cls) -> None:
        base = cls.user_data_dir()
        cls.transcriptions_dir()
        cls.recordings_dir()
        others = cls.others_dir()
        for name in ("models", "cache", "temp"):
            cls._merge_directory(base / name, others / name)
        old_settings = base / "config" / "settings.json"
        new_settings = cls.settings_file()
        if old_settings.exists() and not new_settings.exists():
            new_settings.parent.mkdir(parents=True, exist_ok=True)
            try:
                old_settings.replace(new_settings)
            except OSError:
                shutil.copy2(old_settings, new_settings)
        for name in ("config", "logs", "ffmpeg"):
            shutil.rmtree(base / name, ignore_errors=True)

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

    @classmethod
    def _merge_directory(cls, source: Path, destination: Path) -> None:
        if not source.exists() or source.resolve() == destination.resolve():
            return
        destination.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            target = destination / item.name
            try:
                if item.is_dir() and target.exists() and target.is_dir():
                    cls._merge_directory(item, target)
                elif target.exists():
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
                else:
                    item.replace(target)
            except OSError:
                try:
                    if item.is_dir():
                        shutil.copytree(item, target, dirs_exist_ok=True)
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        shutil.copy2(item, target)
                        item.unlink(missing_ok=True)
                except Exception:
                    pass
        try:
            source.rmdir()
        except OSError:
            pass
