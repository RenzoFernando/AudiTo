from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TranscriptionResult:
    output_path: Path
    duration: float | None
    detected_language: str | None
    segment_count: int
