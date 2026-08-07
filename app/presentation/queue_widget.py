from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QProgressBar, QVBoxLayout, QWidget

from app.domain.job_status import JobStatus
from app.domain.transcription_job import TranscriptionJob
from app.infrastructure.exporters.txt_exporter import format_duration


STATUS_LABELS = {
    JobStatus.PENDING: "Esperando",
    JobStatus.PROCESSING: "Transcribiendo",
    JobStatus.COMPLETED: "Completado",
    JobStatus.FAILED: "Error",
    JobStatus.CANCELLED: "Cancelado",
}


class QueueItemWidget(QWidget):
    def __init__(self, job: TranscriptionJob, parent=None) -> None:
        super().__init__(parent)
        self._job = job
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 9, 10, 9)
        root.setSpacing(6)
        top = QHBoxLayout()
        top.setSpacing(10)
        self._name = QLabel(job.input_path.name)
        self._name.setToolTip(str(job.input_path))
        self._name.setStyleSheet("font-weight: 600;")
        self._duration = QLabel(format_duration(job.duration))
        self._duration.setObjectName("mutedLabel")
        self._duration.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self._name, 1)
        top.addWidget(self._duration)
        bottom = QHBoxLayout()
        bottom.setSpacing(10)
        self._status = QLabel(STATUS_LABELS[job.status])
        self._status.setObjectName("mutedLabel")
        self._progress_text = QLabel("0 %")
        self._progress_text.setObjectName("mutedLabel")
        self._progress_text.setAlignment(Qt.AlignmentFlag.AlignRight)
        bottom.addWidget(self._status, 1)
        bottom.addWidget(self._progress_text)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        root.addLayout(top)
        root.addLayout(bottom)
        root.addWidget(self._progress)

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def set_job_status(self, status: JobStatus) -> None:
        self._status.setText(STATUS_LABELS[status])
        if status == JobStatus.COMPLETED:
            self.set_progress(100)

    def set_progress(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        self._progress.setValue(value)
        self._progress_text.setText(f"{value} %")


class QueueWidget(QListWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.setMaximumHeight(220)
        self.setSpacing(2)
        self._widgets: dict[str, QueueItemWidget] = {}

    def add_job(self, job: TranscriptionJob) -> None:
        item = QListWidgetItem()
        widget = QueueItemWidget(job)
        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)
        self._widgets[job.id] = widget

    def set_status(self, job_id: str, text: str) -> None:
        widget = self._widgets.get(job_id)
        if widget:
            widget.set_status(text)

    def set_job_status(self, job_id: str, status: JobStatus) -> None:
        widget = self._widgets.get(job_id)
        if widget:
            widget.set_job_status(status)

    def set_progress(self, job_id: str, value: int) -> None:
        widget = self._widgets.get(job_id)
        if widget:
            widget.set_progress(value)
