from __future__ import annotations

from pathlib import Path

from app.constants import LANGUAGES
from app.domain.model_profile import ModelProfile
from app.domain.transcription_job import TranscriptionJob
from app.infrastructure.audio.audio_probe import AudioProbe


class CurrentAudioService:
    def __init__(self) -> None:
        self._probe = AudioProbe()
        self._job: TranscriptionJob | None = None

    @property
    def job(self) -> TranscriptionJob | None:
        return self._job

    def select(self, paths: list[str], language_label: str, profile_label: str) -> tuple[TranscriptionJob | None, list[str], int]:
        rejected: list[str] = []
        supported: list[Path] = []
        for raw_path in paths:
            path = Path(raw_path)
            if self._probe.is_supported(path):
                supported.append(path)
            else:
                rejected.append(path.name or raw_path)
        if not supported:
            return None, rejected, 0
        path = supported[0]
        self._job = TranscriptionJob(
            input_path=path,
            language_label=language_label,
            language_code=LANGUAGES.get(language_label),
            model_profile=ModelProfile.from_label(profile_label),
            duration=self._probe.duration(path),
        )
        return self._job, rejected, max(0, len(supported) - 1)

    def set_recording(self, path: Path, duration: float, language_label: str, profile_label: str) -> TranscriptionJob:
        self._job = TranscriptionJob(
            input_path=path,
            language_label=language_label,
            language_code=LANGUAGES.get(language_label),
            model_profile=ModelProfile.from_label(profile_label),
            duration=duration,
        )
        return self._job

    def restore(self, job: TranscriptionJob | None) -> None:
        self._job = job

    def clear(self) -> None:
        self._job = None

    def update_settings(self, language_label: str, profile_label: str) -> None:
        if self._job is None:
            return
        self._job.language_label = language_label
        self._job.language_code = LANGUAGES.get(language_label)
        self._job.model_profile = ModelProfile.from_label(profile_label)
