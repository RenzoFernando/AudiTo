from __future__ import annotations

import json
from pathlib import Path

from app.constants import CONFIG_VERSION, DEFAULT_LANGUAGE, DEFAULT_PROFILE, DEFAULT_UI_LANGUAGE
from app.infrastructure.system.app_paths import AppPaths


class SettingsRepository:
    def __init__(self) -> None:
        self._path = AppPaths.settings_file()

    def _defaults(self) -> dict:
        return {
            "config_version": CONFIG_VERSION,
            "ui_language": DEFAULT_UI_LANGUAGE,
            "language": DEFAULT_LANGUAGE,
            "profile": DEFAULT_PROFILE,
            "output_dir": str(AppPaths.transcriptions_dir()),
            "installed_models": [],
        }

    def load(self) -> dict:
        defaults = self._defaults()
        if not self._path.exists():
            return defaults
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            stored_version = int(data.get("config_version", 0) or 0)
            old_default = str(Path.home() / "Documents" / "Transcripciones")
            stored_output = str(data.get("output_dir", "") or "")
            if stored_version < CONFIG_VERSION and stored_output == old_default:
                data["output_dir"] = defaults["output_dir"]
            defaults.update({key: value for key, value in data.items() if key in defaults})
        except Exception:
            pass
        defaults["config_version"] = CONFIG_VERSION
        if defaults["ui_language"] not in {"es", "en"}:
            defaults["ui_language"] = DEFAULT_UI_LANGUAGE
        if defaults["language"] not in {"Español", "Inglés", "Automático"}:
            defaults["language"] = DEFAULT_LANGUAGE
        if defaults["profile"] not in {"Rápida", "Equilibrada", "Máxima"}:
            defaults["profile"] = DEFAULT_PROFILE
        if not str(defaults["output_dir"]).strip():
            defaults["output_dir"] = str(AppPaths.transcriptions_dir())
        return defaults

    def save(self, settings: dict) -> None:
        payload = {
            "config_version": CONFIG_VERSION,
            "ui_language": settings.get("ui_language", DEFAULT_UI_LANGUAGE),
            "language": settings.get("language", DEFAULT_LANGUAGE),
            "profile": settings.get("profile", DEFAULT_PROFILE),
            "output_dir": settings.get("output_dir", str(AppPaths.transcriptions_dir())),
            "installed_models": list(settings.get("installed_models", [])),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self._path)
