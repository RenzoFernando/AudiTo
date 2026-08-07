from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.constants import SUPPORTED_AUDIO_EXTENSIONS


class AudioInputWidget(QFrame):
    files_selected = Signal(list)
    browse_requested = Signal()
    record_requested = Signal()
    stop_record_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._recording = False
        self._microphone_name = "Micrófono predeterminado de Windows"
        self.setObjectName("audioInput")
        self.setAcceptDrops(True)
        self.setProperty("dragActive", False)
        self.setFixedHeight(124)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(4)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("Arrastra un audio aquí")
        self.title_label.setObjectName("dropTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.helper_label = QLabel("o selecciona un archivo o graba con tu micrófono")
        self.helper_label.setObjectName("inputHelperLabel")
        self.helper_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.helper_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.formats_label = QLabel("MP3 · M4A · WAV · FLAC · AAC · OGG")
        self.formats_label.setObjectName("mutedLabel")
        self.formats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formats_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.addStretch(1)
        self.browse_button = QPushButton("Seleccionar audio")
        self.browse_button.setObjectName("secondaryButton")
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_button = QPushButton("Grabar")
        self.record_button.setObjectName("recordButton")
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        actions.addWidget(self.browse_button)
        actions.addWidget(self.record_button)
        actions.addStretch(1)

        root.addWidget(self.title_label)
        root.addWidget(self.helper_label)
        root.addWidget(self.formats_label)
        root.addSpacing(2)
        root.addLayout(actions)

        self.browse_button.clicked.connect(self.browse_requested.emit)
        self.record_button.clicked.connect(self._record_clicked)

    def _record_clicked(self) -> None:
        if self._recording:
            self.stop_record_requested.emit()
        else:
            self.record_requested.emit()

    def set_recording(self, active: bool) -> None:
        self._recording = active
        self.setAcceptDrops(not active)
        self.browse_button.setEnabled(not active)
        self.record_button.setText("DETENER" if active else "Grabar")
        self.record_button.setProperty("recording", active)
        if active:
            self.title_label.setText("Grabando · 00:00")
            self.helper_label.setText(f"Micrófono · {self._microphone_name}")
            self.formats_label.setText("WAV · guardado automático")
        else:
            self.title_label.setText("Arrastra un audio aquí")
            self.helper_label.setText("o selecciona un archivo o graba con tu micrófono")
            self.formats_label.setText("MP3 · M4A · WAV · FLAC · AAC · OGG")
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)

    def set_recording_time(self, seconds: int) -> None:
        if not self._recording:
            return
        seconds = max(0, int(seconds))
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            value = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            value = f"{minutes:02d}:{secs:02d}"
        self.title_label.setText(f"Grabando · {value}")

    def set_microphone_name(self, name: str) -> None:
        cleaned = " ".join(str(name).split()).strip()
        if "(" in cleaned:
            short_name = cleaned.split("(", 1)[0].strip()
            if len(short_name) >= 4:
                cleaned = short_name
        if not cleaned:
            cleaned = "Micrófono predeterminado de Windows"
        if len(cleaned) > 42:
            cleaned = cleaned[:39].rstrip() + "..."
        self._microphone_name = cleaned
        self.setToolTip(str(name))
        if self._recording:
            self.helper_label.setText(f"Micrófono · {self._microphone_name}")

    def set_interactions_enabled(self, enabled: bool) -> None:
        if self._recording:
            self.setAcceptDrops(False)
            self.browse_button.setEnabled(False)
            self.record_button.setEnabled(True)
            return
        self.setAcceptDrops(enabled)
        self.browse_button.setEnabled(enabled)
        self.record_button.setEnabled(enabled)

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
