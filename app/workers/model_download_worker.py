from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.domain.model_profile import ModelProfile
from app.infrastructure.models.model_repository import ModelRepository


class ModelDownloadWorker(QThread):
    status_changed = Signal(str)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, profile: ModelProfile, repository: ModelRepository, parent=None) -> None:
        super().__init__(parent)
        self._profile = profile
        self._repository = repository

    def run(self) -> None:
        try:
            self._repository.download(self._profile, self.status_changed.emit)
            self.completed.emit(self._profile.label)
        except Exception as exc:
            self.failed.emit(str(exc))
