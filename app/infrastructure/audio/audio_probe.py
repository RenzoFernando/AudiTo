from __future__ import annotations

from pathlib import Path

from app.constants import SUPPORTED_AUDIO_EXTENSIONS


class AudioProbe:
    def is_supported(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS

    def duration(self, path: Path) -> float | None:
        try:
            import av

            with av.open(str(path)) as container:
                if container.duration is not None:
                    return float(container.duration / av.time_base)
                durations = []
                for stream in container.streams.audio:
                    if stream.duration is not None and stream.time_base is not None:
                        durations.append(float(stream.duration * stream.time_base))
                return max(durations) if durations else None
        except Exception:
            return None
