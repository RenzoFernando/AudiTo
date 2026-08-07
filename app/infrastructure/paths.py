from __future__ import annotations

import sys
from pathlib import Path


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def config_dir() -> Path:
    path = base_dir() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = base_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def models_dir() -> Path:
    path = base_dir() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ffmpeg_dir() -> Path:
    path = base_dir() / "ffmpeg"
    path.mkdir(parents=True, exist_ok=True)
    return path


def assets_dir() -> Path:
    path = base_dir() / "assets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_icon_path() -> Path:
    return assets_dir() / "icon.png"
