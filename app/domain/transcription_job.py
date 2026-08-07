from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.domain.job_status import JobStatus
from app.domain.model_profile import ModelProfile


@dataclass
class TranscriptionJob:
    input_path: Path
    language_label: str
    language_code: str | None
    model_profile: ModelProfile
    duration: float | None = None
    output_path: Path | None = None
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: uuid4().hex)
