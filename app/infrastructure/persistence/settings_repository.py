from __future__ import annotations

import json
from pathlib import Path

from app.constants import DEFAULT_LANGUAGE, DEFAULT_PROFILE
from app.infrastructure.paths import config_dir


class SettingsRepository:
    def __init__(self) -> None:
        self._path = config_dir() / "settings.json"

    def load(self) -> dict:
        defaults = {
            "language": DEFAULT_LANGUAGE,
            "profile": DEFAULT_PROFILE,
            "output_dir": str(Path.home() / "Documents" / "Transcripciones"),
        }
        if not self._path.exists():
            return defaults
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            defaults.update({key: value for key, value in data.items() if key in defaults})
        except Exception:
            pass
        return defaults

    def save(self, settings: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(".tmp")
        temporary.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self._path)
