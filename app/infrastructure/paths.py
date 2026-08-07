from __future__ import annotations

from pathlib import Path

from app.infrastructure.system.app_paths import AppPaths


def base_dir() -> Path:
    return AppPaths.resource_dir()


def config_dir() -> Path:
    return AppPaths.config_dir()


def logs_dir() -> Path:
    return AppPaths.logs_dir()


def models_dir() -> Path:
    return AppPaths.models_dir()


def cache_dir() -> Path:
    return AppPaths.cache_dir()


def temp_dir() -> Path:
    return AppPaths.temp_dir()


def ffmpeg_dir() -> Path:
    return AppPaths.ffmpeg_dir()


def assets_dir() -> Path:
    return AppPaths.assets_dir()


def app_icon_path() -> Path:
    return AppPaths.app_icon_path()
