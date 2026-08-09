from __future__ import annotations

import threading

from PySide6.QtCore import QThread, Signal

from app.domain.model_profile import ModelProfile
from app.infrastructure.models.model_repository import ModelDownloadCancelled, ModelRepository


class ModelDownloadWorker(QThread):
    status_changed = Signal(str)
    completed = Signal(str)
    cancelled = Signal(str)
    failed = Signal(str)

    def __init__(self, profile: ModelProfile, repository: ModelRepository, parent=None) -> None:
        super().__init__(parent)
        self._profile = profile
        self._repository = repository
        self._cancel_event = threading.Event()

    def request_cancel(self) -> None:
        self._cancel_event.set()

    def run(self) -> None:
        try:
            self._repository.download(self._profile, self.status_changed.emit, self._cancel_event)
            if self._cancel_event.is_set():
                self.cancelled.emit(self._profile.label)
                return
            self.completed.emit(self._profile.label)
        except ModelDownloadCancelled:
            self.cancelled.emit(self._profile.label)
        except Exception as exc:
            self.failed.emit(str(exc))
