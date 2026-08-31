from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from app.presentation.translations import tr


class ProgressWidget(QFrame):
    def __init__(self, ui_language: str = "es", parent=None) -> None:
        super().__init__(parent)
        self._ui_language = ui_language
        self._waiting_step = 1
        self._waiting_active = True
        self._download_display_value = 0
        self._download_target_value = 0
        self._download_detail = ""
        self.setObjectName("progressFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(5)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel()
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
        self._waiting_timer = QTimer(self)
        self._waiting_timer.setInterval(500)
        self._waiting_timer.timeout.connect(self._advance_waiting_animation)
        self._download_timer = QTimer(self)
        self._download_timer.setInterval(65)
        self._download_timer.timeout.connect(self._advance_download_animation)
        self._update_waiting_text()
        self._waiting_timer.start()

    def set_ui_language(self, ui_language: str) -> None:
        self._ui_language = ui_language
        if self._waiting_active:
            self._update_waiting_text()
        elif self._download_timer.isActive() or self._download_target_value > 0:
            self._update_download_text()

    def set_idle(self, status: str | None = None, detail: str = "") -> None:
        self._stop_download_animation()
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        waiting_text = tr(self._ui_language, "status_waiting")
        if status is None or status == waiting_text:
            self._start_waiting_animation()
        else:
            self._stop_waiting_animation()
            self.status_label.setText(status)
        self.detail_label.setText(detail)
        self._set_state("idle")

    def set_file_progress(self, value: int, detail: str = "", status: str | None = None) -> None:
        self._stop_waiting_animation()
        self._stop_download_animation()
        value = max(0, min(100, int(value)))
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(value)
        self.status_label.setText(status if status is not None else tr(self._ui_language, "status_transcribing", value=value))
        self.detail_label.setText(detail)
        self._set_state("idle")

    def set_download_progress(self, value: int, detail: str = "") -> None:
        self._stop_waiting_animation()
        value = max(0, min(100, int(value)))
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self._download_detail = detail
        if value <= self._download_display_value:
            self._download_display_value = value
            self._download_target_value = value
            self.progress.setValue(value)
            self._download_timer.stop()
            self._update_download_text()
        else:
            self._download_target_value = value
            self._update_download_text()
            if not self._download_timer.isActive():
                self._download_timer.start()
        self._set_state("idle")

    def set_finalizing_progress(self, value: int, detail: str = "") -> None:
        self._stop_waiting_animation()
        self._stop_download_animation()
        value = max(0, min(100, int(value)))
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(value)
        self.status_label.setText(tr(self._ui_language, "status_finalizing_percent", value=value))
        self.detail_label.setText(detail)
        self._set_state("idle")

    def set_indeterminate(self, status: str, detail: str = "") -> None:
        self._stop_waiting_animation()
        self._stop_download_animation()
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status_label.setText(status)
        self.detail_label.setText(detail)
        self._set_state("idle")

    def set_recording(self, status: str, detail: str = "") -> None:
        self._stop_waiting_animation()
        self._stop_download_animation()
        self.progress.setVisible(False)
        self.status_label.setText(status)
        self.detail_label.setText(detail)
        self._set_state("recording")

    def set_completed(self, status: str | None = None, detail: str | None = None) -> None:
        self._stop_waiting_animation()
        self._stop_download_animation()
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.status_label.setText(status if status is not None else tr(self._ui_language, "status_completed"))
        self.detail_label.setText(detail if detail is not None else tr(self._ui_language, "txt_ready"))
        self._set_state("completed")

    def _start_waiting_animation(self) -> None:
        self._waiting_active = True
        self._waiting_step = 1
        self._update_waiting_text()
        if not self._waiting_timer.isActive():
            self._waiting_timer.start()

    def _stop_waiting_animation(self) -> None:
        self._waiting_active = False
        self._waiting_timer.stop()

    def _advance_waiting_animation(self) -> None:
        if not self._waiting_active:
            return
        self._waiting_step = 1 if self._waiting_step >= 3 else self._waiting_step + 1
        self._update_waiting_text()

    def _update_waiting_text(self) -> None:
        self.status_label.setText(f"{tr(self._ui_language, 'status_waiting')}{'.' * self._waiting_step}")

    def _advance_download_animation(self) -> None:
        if self._download_display_value >= self._download_target_value:
            self._download_timer.stop()
            return
        self._download_display_value += 1
        self.progress.setValue(self._download_display_value)
        self._update_download_text()
        if self._download_display_value >= self._download_target_value:
            self._download_timer.stop()

    def _update_download_text(self) -> None:
        self.status_label.setText(tr(self._ui_language, "status_downloading_model_percent", value=self._download_display_value))
        self.detail_label.setText(self._download_detail)

    def _stop_download_animation(self) -> None:
        self._download_timer.stop()
        self._download_display_value = 0
        self._download_target_value = 0
        self._download_detail = ""

    def _set_state(self, state: str) -> None:
        self.status_label.setProperty("state", state)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
