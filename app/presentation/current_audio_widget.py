from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout

from app.presentation.translations import tr


class CurrentAudioWidget(QFrame):
    remove_requested = Signal()

    def __init__(self, ui_language: str = "es", parent=None) -> None:
        super().__init__(parent)
        self._ui_language = ui_language
        self._view_mode = "empty"
        self._path: Path | None = None
        self._duration: float | None = None
        self._recorded_audio = False
        self.setObjectName("fileCard")
        self.setFixedHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 8, 10, 8)
        layout.setSpacing(8)
        self.dot = QLabel("●")
        self.dot.setObjectName("fileDot")
        self.dot.setProperty("state", "idle")
        self.dot.setFixedWidth(10)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)
        self.name_label = QLabel()
        self.name_label.setObjectName("fileNameLabel")
        self.name_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.meta_label = QLabel()
        self.meta_label.setObjectName("fileMetaLabel")
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.meta_label)
        self.remove_button = QPushButton("×")
        self.remove_button.setObjectName("removeAudioButton")
        self.remove_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.remove_button.setVisible(False)
        self.remove_button.clicked.connect(self.remove_requested.emit)
        layout.addWidget(self.dot)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self.remove_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self._refresh_text()

    def set_ui_language(self, ui_language: str) -> None:
        self._ui_language = ui_language
        self._refresh_text()

    def show_empty(self) -> None:
        self._view_mode = "empty"
        self._path = None
        self._duration = None
        self._recorded_audio = False
        self.name_label.setToolTip("")
        self._refresh_text()
        self.set_state("idle")
        self.set_remove_available(False)

    def show_audio(self, path: Path, duration: float | None, recorded_audio: bool = False) -> None:
        self._view_mode = "audio"
        self._path = path
        self._duration = duration
        self._recorded_audio = recorded_audio
        self.name_label.setToolTip(str(path))
        self._refresh_text()
        self.set_state("selected")

    def show_recording(self, path: Path) -> None:
        self._view_mode = "recording"
        self._path = path
        self._duration = None
        self._recorded_audio = True
        self.name_label.setToolTip(str(path))
        self._refresh_text()
        self.set_state("recorded")
        self.set_remove_available(False)

    def set_state(self, state: str) -> None:
        self.dot.setProperty("state", state)
        self.dot.style().unpolish(self.dot)
        self.dot.style().polish(self.dot)

    def set_remove_available(self, available: bool) -> None:
        self.remove_button.setVisible(available)
        self.remove_button.setEnabled(available)

    def _refresh_text(self) -> None:
        self.remove_button.setToolTip(tr(self._ui_language, "remove_audio_tooltip"))
        if self._view_mode == "empty":
            self.name_label.setText(tr(self._ui_language, "no_audio"))
            self.meta_label.setText(tr(self._ui_language, "select_drag_record"))
            return
        if self._path is not None:
            self.name_label.setText(self._path.name)
        if self._view_mode == "recording":
            self.meta_label.setText(tr(self._ui_language, "recording_auto_saved"))
            return
        meta = self._format_duration(self._duration)
        if self._recorded_audio:
            meta = f"{tr(self._ui_language, 'recording_prefix')}{meta}"
        self.meta_label.setText(meta)

    def _format_duration(self, duration: float | None) -> str:
        if duration is None:
            return tr(self._ui_language, "duration_unavailable")
        total = max(0, int(duration))
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
