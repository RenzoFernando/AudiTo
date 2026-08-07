from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from app.infrastructure.paths import ffmpeg_dir


class FFmpegService:
    def _ffprobe_path(self) -> str | None:
        bundled = ffmpeg_dir() / "ffprobe.exe"
        if bundled.exists():
            return str(bundled)
        return shutil.which("ffprobe")

    def duration(self, path: Path) -> float | None:
        executable = self._ffprobe_path()
        if not executable:
            return None
        process = subprocess.run(
            [
                executable,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if process.returncode != 0:
            return None
        try:
            payload = json.loads(process.stdout)
            value = payload.get("format", {}).get("duration")
            return float(value) if value is not None else None
        except (ValueError, TypeError, json.JSONDecodeError):
            return None
