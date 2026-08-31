from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from app.infrastructure.system.app_paths import AppPaths


@dataclass(frozen=True)
class GroqUsageSnapshot:
    audio_seconds_hour: float
    audio_seconds_day: float
    requests_hour: int
    requests_day: int
    remaining_requests_day: int | None
    request_limit_day: int | None
    request_reset: str | None
    last_success_at: float | None


class GroqUsageTracker:
    FREE_AUDIO_SECONDS_HOUR = 7200.0
    FREE_AUDIO_SECONDS_DAY = 28800.0
    FREE_REQUESTS_MINUTE = 20
    FREE_REQUESTS_DAY = 2000

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (AppPaths.others_dir() / "groq_usage.json")

    def record_success(self, api_key: str, audio_seconds: float, headers=None, timestamp: float | None = None) -> None:
        fingerprint = self._fingerprint(api_key)
        if not fingerprint:
            return
        now = float(timestamp if timestamp is not None else time.time())
        data = self._load()
        projects = data.setdefault("keys", {})
        current = projects.setdefault(fingerprint, {"events": [], "headers": {}})
        events = current.setdefault("events", [])
        events.append({"timestamp": now, "audio_seconds": max(0.0, float(audio_seconds))})
        current["events"] = [
            event
            for event in events
            if now - float(event.get("timestamp", 0.0) or 0.0) <= 172800.0
        ]
        current["last_success_at"] = now
        normalized_headers = self._extract_headers(headers)
        if normalized_headers:
            current["headers"] = normalized_headers
        self._save(data)

    def snapshot(self, api_key: str, timestamp: float | None = None) -> GroqUsageSnapshot:
        fingerprint = self._fingerprint(api_key)
        now = float(timestamp if timestamp is not None else time.time())
        data = self._load()
        current = data.get("keys", {}).get(fingerprint, {}) if fingerprint else {}
        events = current.get("events", []) if isinstance(current, dict) else []
        hour_events = [event for event in events if now - float(event.get("timestamp", 0.0) or 0.0) <= 3600.0]
        day_events = [event for event in events if now - float(event.get("timestamp", 0.0) or 0.0) <= 86400.0]
        headers = current.get("headers", {}) if isinstance(current, dict) else {}
        return GroqUsageSnapshot(
            audio_seconds_hour=sum(max(0.0, float(event.get("audio_seconds", 0.0) or 0.0)) for event in hour_events),
            audio_seconds_day=sum(max(0.0, float(event.get("audio_seconds", 0.0) or 0.0)) for event in day_events),
            requests_hour=len(hour_events),
            requests_day=len(day_events),
            remaining_requests_day=self._to_int(headers.get("x-ratelimit-remaining-requests")),
            request_limit_day=self._to_int(headers.get("x-ratelimit-limit-requests")),
            request_reset=self._to_text(headers.get("x-ratelimit-reset-requests")),
            last_success_at=self._to_float(current.get("last_success_at")) if isinstance(current, dict) else None,
        )

    def _fingerprint(self, api_key: str) -> str:
        value = str(api_key or "").strip()
        if not value:
            return ""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]

    def _load(self) -> dict:
        if not self._path.exists():
            return {"version": 1, "keys": {}}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("version", 1)
                data.setdefault("keys", {})
                return data
        except Exception:
            pass
        return {"version": 1, "keys": {}}

    def _save(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self._path)

    def _extract_headers(self, headers) -> dict[str, str]:
        if headers is None:
            return {}
        wanted = {
            "x-ratelimit-limit-requests",
            "x-ratelimit-remaining-requests",
            "x-ratelimit-reset-requests",
        }
        result: dict[str, str] = {}
        try:
            items = headers.items()
        except Exception:
            return result
        for key, value in items:
            normalized = str(key).casefold()
            if normalized in wanted:
                result[normalized] = str(value)
        return result

    def _to_int(self, value) -> int | None:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None

    def _to_float(self, value) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_text(self, value) -> str | None:
        text = str(value or "").strip()
        return text or None
