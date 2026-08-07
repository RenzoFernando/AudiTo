from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from app.presentation.translations import tr


class ProgressWidget(QFrame):
    def __init__(self, ui_language: str = "es", parent=None) -> None:
        super().__init__(parent)
        self._ui_language = ui_language
        self.setObjectName("progressFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(5)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel(tr(self._ui_language, "status_waiting"))
        self.status_label.setObjectName("progressStatusLabel")
        self.status_label.setProperty("state", "idle")
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("etaLabel")
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.status_label, 1)
        header.addWidget(self.detail_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addLayout(header)
        layout.addWidget(self.progress)

    def set_ui_language(self, ui_language: str) -> None:
        self._ui_language = ui_language

    def set_idle(self, status: str | None = None, detail: str = "") -> None:
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status_label.setText(status if status is not None else tr(self._ui_language, "status_waiting"))
        self.detail_label.setText(detail)
        self._set_state("idle")

    def set_file_progress(self, value: int, detail: str = "") -> None:
        value = max(0, min(100, int(value)))
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(value)
        self.status_label.setText(tr(self._ui_language, "status_transcribing", value=value))
        self.detail_label.setText(detail)
        self._set_state("idle")

    def set_finalizing_progress(self, value: int, detail: str = "") -> None:
        value = max(0, min(100, int(value)))
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(value)
        self.status_label.setText(tr(self._ui_language, "status_finalizing"))
        self.detail_label.setText(detail)
        self._set_state("idle")

    def set_indeterminate(self, status: str, detail: str = "") -> None:
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status_label.setText(status)
        self.detail_label.setText(detail)
        self._set_state("idle")

    def set_recording(self, status: str, detail: str = "") -> None:
        self.progress.setVisible(False)
        self.status_label.setText(status)
        self.detail_label.setText(detail)
        self._set_state("recording")

    def set_completed(self, status: str | None = None, detail: str | None = None) -> None:
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.status_label.setText(status if status is not None else tr(self._ui_language, "status_completed"))
        self.detail_label.setText(detail if detail is not None else tr(self._ui_language, "txt_ready"))
        self._set_state("completed")

    def _set_state(self, state: str) -> None:
        self.status_label.setProperty("state", state)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
