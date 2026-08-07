from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.constants import SUPPORTED_AUDIO_EXTENSIONS
from app.presentation.translations import tr


class AudioInputWidget(QFrame):
    files_selected = Signal(list)
    browse_requested = Signal()
    record_requested = Signal()
    stop_record_requested = Signal()
    discard_record_requested = Signal()

    def __init__(self, ui_language: str = "es", parent=None) -> None:
        super().__init__(parent)
        self._ui_language = ui_language
        self._recording = False
        self._recording_seconds = 0
        self._microphone_name = tr(self._ui_language, "default_microphone")
        self.setObjectName("audioInput")
        self.setAcceptDrops(True)
        self.setProperty("dragActive", False)
        self.setFixedHeight(116)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(3)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel()
        self.title_label.setObjectName("dropTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.helper_label = QLabel()
        self.helper_label.setObjectName("inputHelperLabel")
        self.helper_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.helper_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.formats_label = QLabel("MP3 · M4A · WAV · FLAC · AAC · OGG")
        self.formats_label.setObjectName("mutedLabel")
        self.formats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formats_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addStretch(1)
        self.browse_button = QPushButton()
        self.browse_button.setObjectName("secondaryButton")
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.record_button = QPushButton()
        self.record_button.setObjectName("recordButton")
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.discard_button = QPushButton()
        self.discard_button.setObjectName("discardRecordButton")
        self.discard_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.discard_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.discard_button.setVisible(False)
        actions.addWidget(self.browse_button)
        actions.addWidget(self.record_button)
        actions.addWidget(self.discard_button)
        actions.addStretch(1)
        root.addWidget(self.title_label)
        root.addWidget(self.helper_label)
        root.addWidget(self.formats_label)
        root.addSpacing(2)
        root.addLayout(actions)
        self.browse_button.clicked.connect(self.browse_requested.emit)
        self.record_button.clicked.connect(self._record_clicked)
        self.discard_button.clicked.connect(self.discard_record_requested.emit)
        self._refresh_text()

    def _record_clicked(self) -> None:
        if self._recording:
            self.stop_record_requested.emit()
        else:
            self.record_requested.emit()

    def set_ui_language(self, ui_language: str) -> None:
        self._ui_language = ui_language
        self._refresh_text()

    def set_recording(self, active: bool) -> None:
        self._recording = active
        if not active:
            self._recording_seconds = 0
        self.setAcceptDrops(not active)
        self.browse_button.setVisible(not active)
        self.discard_button.setVisible(active)
        self.record_button.setProperty("recording", active)
        self._refresh_text()
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)

    def set_recording_time(self, seconds: int) -> None:
        if not self._recording:
            return
        self._recording_seconds = max(0, int(seconds))
        self.title_label.setText(f"● {tr(self._ui_language, 'recording')} · {self._format_time(self._recording_seconds)}")

    def set_microphone_name(self, name: str) -> None:
        cleaned = " ".join(str(name).split()).strip()
        if "(" in cleaned:
            short_name = cleaned.split("(", 1)[0].strip()
            if len(short_name) >= 4:
                cleaned = short_name
        if not cleaned:
            cleaned = tr(self._ui_language, "default_microphone")
        if len(cleaned) > 42:
            cleaned = cleaned[:39].rstrip() + "..."
        self._microphone_name = cleaned
        self.setToolTip(str(name))
        if self._recording:
            self.helper_label.setText(f"{tr(self._ui_language, 'microphone')} · {self._microphone_name}")

    def set_interactions_enabled(self, enabled: bool) -> None:
        if self._recording:
            self.setAcceptDrops(False)
            self.browse_button.setEnabled(False)
            self.record_button.setEnabled(True)
            self.discard_button.setEnabled(True)
            return
        self.setAcceptDrops(enabled)
        self.browse_button.setEnabled(enabled)
        self.record_button.setEnabled(enabled)
        self.discard_button.setEnabled(False)

    def _refresh_text(self) -> None:
        self.browse_button.setText(tr(self._ui_language, "select_audio"))
        self.record_button.setText(tr(self._ui_language, "stop") if self._recording else tr(self._ui_language, "record"))
        self.discard_button.setText(tr(self._ui_language, "discard"))
        if self._recording:
            self.title_label.setText(f"● {tr(self._ui_language, 'recording')} · {self._format_time(self._recording_seconds)}")
            self.helper_label.setText(f"{tr(self._ui_language, 'microphone')} · {self._microphone_name}")
            self.formats_label.setText(tr(self._ui_language, "wav_auto_saved"))
        else:
            self.title_label.setText(tr(self._ui_language, "drop_title"))
            self.helper_label.setText(tr(self._ui_language, "drop_helper"))
            self.formats_label.setText("MP3 · M4A · WAV · FLAC · AAC · OGG")

    def _supported_paths(self, event) -> list[str]:
        paths: list[str] = []
        if not event.mimeData().hasUrls():
            return paths
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                paths.append(str(path))
        return paths

    def dragEnterEvent(self, event) -> None:
        if not self._recording and self._supported_paths(event):
            event.acceptProposedAction()
            self._set_drag_active(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if not self._recording and self._supported_paths(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._set_drag_active(False)
        event.accept()

    def dropEvent(self, event) -> None:
        self._set_drag_active(False)
        paths = self._supported_paths(event)
        if paths:
            self.files_selected.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _set_drag_active(self, active: bool) -> None:
        self.setProperty("dragActive", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def _format_time(self, seconds: int) -> str:
        seconds = max(0, int(seconds))
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
