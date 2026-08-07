from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from app.constants import SUPPORTED_AUDIO_EXTENSIONS


class DropZone(QFrame):
    files_selected = Signal(list)
    browse_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setProperty("dragActive", False)
        self.setFixedHeight(102)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Arrastra un audio aquí")
        title.setObjectName("dropTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        formats = QLabel("MP3 · M4A · WAV · FLAC · AAC · OGG")
        formats.setObjectName("mutedLabel")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formats.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        button = QPushButton("Seleccionar audio")
        button.setObjectName("secondaryButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self.browse_requested.emit)
        layout.addWidget(title)
        layout.addWidget(formats)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignCenter)
        self._button = button

    def set_interactions_enabled(self, enabled: bool) -> None:
        self.setAcceptDrops(enabled)
        self._button.setEnabled(enabled)

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
        if self._supported_paths(event):
            event.acceptProposedAction()
            self._set_drag_active(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if self._supported_paths(event):
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
