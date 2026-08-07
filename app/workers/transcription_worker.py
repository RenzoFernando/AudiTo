from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.application.transcription_service import TranscriptionCancelled, TranscriptionService
from app.domain.job_status import JobStatus
from app.domain.transcription_job import TranscriptionJob


class TranscriptionWorker(QThread):
    job_started = Signal(str)
    job_progress = Signal(str, int)
    job_status = Signal(str, str)
    job_completed = Signal(str, str)
    job_failed = Signal(str, str)
    job_cancelled = Signal(str)
    task_finished = Signal()

    def __init__(self, job: TranscriptionJob, output_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._job = job
        self._output_dir = output_dir
        self._cancel_event = threading.Event()
        self._service = TranscriptionService()

    def cancel_current(self) -> None:
        self._cancel_event.set()

    def run(self) -> None:
        self._job.status = JobStatus.PROCESSING
        self._job.progress = 0
        self.job_started.emit(self._job.id)
        try:
            result = self._service.transcribe_job(
                self._job,
                self._output_dir,
                self._cancel_event,
                self._emit_progress,
                lambda value: self.job_status.emit(self._job.id, value),
            )
            self._job.status = JobStatus.COMPLETED
            self._job.progress = 100
            self.job_completed.emit(self._job.id, str(result.output_path))
        except TranscriptionCancelled:
            self._job.status = JobStatus.CANCELLED
            self.job_cancelled.emit(self._job.id)
        except Exception as exc:
            self._job.status = JobStatus.FAILED
            self._job.error = str(exc)
            self.job_failed.emit(self._job.id, str(exc))
        self.task_finished.emit()

    def _emit_progress(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        self._job.progress = value
        self.job_progress.emit(self._job.id, value)
