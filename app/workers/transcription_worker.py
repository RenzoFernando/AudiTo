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
    queue_progress = Signal(int)
    queue_finished = Signal()

    def __init__(self, jobs: list[TranscriptionJob], output_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._jobs = jobs
        self._output_dir = output_dir
        self._cancel_event = threading.Event()
        self._service = TranscriptionService()

    def cancel_current(self) -> None:
        self._cancel_event.set()

    def run(self) -> None:
        total = len(self._jobs)
        completed_units = 0
        for job in self._jobs:
            self._cancel_event.clear()
            job.status = JobStatus.PROCESSING
            job.progress = 0
            self.job_started.emit(job.id)
            try:
                result = self._service.transcribe_job(
                    job,
                    self._output_dir,
                    self._cancel_event,
                    lambda value, job_id=job.id: self._emit_progress(job_id, value, completed_units, total),
                    lambda value, job_id=job.id: self.job_status.emit(job_id, value),
                )
                job.status = JobStatus.COMPLETED
                job.progress = 100
                self.job_completed.emit(job.id, str(result.output_path))
            except TranscriptionCancelled:
                job.status = JobStatus.CANCELLED
                self.job_cancelled.emit(job.id)
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.error = str(exc)
                self.job_failed.emit(job.id, str(exc))
            completed_units += 1
            overall = 100 if total == 0 else int((completed_units / total) * 100)
            self.queue_progress.emit(overall)
        self.queue_finished.emit()

    def _emit_progress(self, job_id: str, value: int, completed_units: int, total: int) -> None:
        value = max(0, min(100, int(value)))
        self.job_progress.emit(job_id, value)
        if total > 0:
            overall = int(((completed_units + value / 100) / total) * 100)
            self.queue_progress.emit(max(0, min(100, overall)))
