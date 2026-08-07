from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout


class CurrentAudioWidget(QFrame):
    remove_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
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
        self.name_label = QLabel("Ningún audio seleccionado")
        self.name_label.setObjectName("fileNameLabel")
        self.name_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.meta_label = QLabel("Selecciona, arrastra o graba un audio")
        self.meta_label.setObjectName("fileMetaLabel")
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.meta_label)
        self.remove_button = QPushButton("×")
        self.remove_button.setObjectName("removeAudioButton")
        self.remove_button.setToolTip("Quitar audio seleccionado")
        self.remove_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.remove_button.setVisible(False)
        self.remove_button.clicked.connect(self.remove_requested.emit)
        layout.addWidget(self.dot)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self.remove_button, 0, Qt.AlignmentFlag.AlignVCenter)

    def show_empty(self) -> None:
        self.name_label.setText("Ningún audio seleccionado")
        self.name_label.setToolTip("")
        self.meta_label.setText("Selecciona, arrastra o graba un audio")
        self.set_state("idle")
        self.set_remove_available(False)

    def show_audio(self, path: Path, duration: float | None, prefix: str = "") -> None:
        self.name_label.setText(path.name)
        self.name_label.setToolTip(str(path))
        meta = self._format_duration(duration)
        self.meta_label.setText(f"{prefix}{meta}" if prefix else meta)
        self.set_state("selected")

    def show_recording(self, path: Path) -> None:
        self.name_label.setText(path.name)
        self.name_label.setToolTip(str(path))
        self.meta_label.setText("Grabando · guardado automático")
        self.set_state("recorded")
        self.set_remove_available(False)

    def set_state(self, state: str) -> None:
        self.dot.setProperty("state", state)
        self.dot.style().unpolish(self.dot)
        self.dot.style().polish(self.dot)

    def set_remove_available(self, available: bool) -> None:
        self.remove_button.setVisible(available)
        self.remove_button.setEnabled(available)

    def _format_duration(self, duration: float | None) -> str:
        if duration is None:
            return "Duración no disponible"
        total = max(0, int(duration))
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
