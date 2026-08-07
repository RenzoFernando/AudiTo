from __future__ import annotations

from pathlib import Path

from app.constants import LANGUAGES
from app.domain.job_status import JobStatus
from app.domain.model_profile import ModelProfile
from app.domain.transcription_job import TranscriptionJob
from app.infrastructure.audio.audio_probe import AudioProbe


class QueueService:
    def __init__(self) -> None:
        self._probe = AudioProbe()
        self._jobs: list[TranscriptionJob] = []

    @property
    def jobs(self) -> list[TranscriptionJob]:
        return list(self._jobs)

    def add_files(self, paths: list[str], language_label: str, profile_label: str) -> tuple[list[TranscriptionJob], list[str]]:
        profile = ModelProfile.from_label(profile_label)
        language_code = LANGUAGES.get(language_label)
        rejected: list[str] = []
        selected: Path | None = None
        for raw_path in paths:
            path = Path(raw_path)
            if self._probe.is_supported(path):
                if selected is None:
                    selected = path
            else:
                rejected.append(path.name or raw_path)
        if selected is None:
            return [], rejected
        job = TranscriptionJob(
            input_path=selected,
            language_label=language_label,
            language_code=language_code,
            model_profile=profile,
            duration=self._probe.duration(selected),
        )
        self._jobs = [job]
        return [job], rejected

    def clear(self) -> None:
        self._jobs.clear()

    def update_pending_settings(self, language_label: str, profile_label: str) -> None:
        profile = ModelProfile.from_label(profile_label)
        language_code = LANGUAGES.get(language_label)
        for job in self._jobs:
            if job.status == JobStatus.PENDING:
                job.language_label = language_label
                job.language_code = language_code
                job.model_profile = profile

    def pending_jobs(self) -> list[TranscriptionJob]:
        return [job for job in self._jobs if job.status == JobStatus.PENDING]
