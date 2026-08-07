from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class RecordingSession:
    path: Path
    sample_rate: int
    started_at: datetime
    duration: float = 0.0
