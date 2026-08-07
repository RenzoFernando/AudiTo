from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from app.constants import LANGUAGES
from app.domain.model_profile import ModelProfile


class SettingsWidget(QWidget):
    settings_changed = Signal(str, str)

    def __init__(self, language: str, profile: str, output_dir: str, parent=None) -> None:
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(5)
        language_label = QLabel("Idioma")
        language_label.setObjectName("sectionLabel")
        profile_label = QLabel("Precisión")
        profile_label.setObjectName("sectionLabel")
        output_label = QLabel("Guardar en")
        output_label.setObjectName("sectionLabel")
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(LANGUAGES.keys()))
        self.language_combo.setCurrentText(language)
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(ModelProfile.labels())
        self.profile_combo.setCurrentText(profile)
        self.output_edit = QLineEdit(output_dir)
        self.output_button = QPushButton("…")
        self.output_button.setObjectName("browseButton")
        self.output_button.setFixedWidth(36)
        layout.addWidget(language_label, 0, 0)
        layout.addWidget(profile_label, 0, 1)
        layout.addWidget(self.language_combo, 1, 0)
        layout.addWidget(self.profile_combo, 1, 1)
        layout.addWidget(output_label, 2, 0, 1, 2)
        output_row = QHBoxLayout()
        output_row.setSpacing(6)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row, 3, 0, 1, 2)
        self.language_combo.currentTextChanged.connect(self._emit_settings_changed)
        self.profile_combo.currentTextChanged.connect(self._emit_settings_changed)
        self.output_button.clicked.connect(self._browse_output)

    def _emit_settings_changed(self) -> None:
        self.settings_changed.emit(self.language_combo.currentText(), self.profile_combo.currentText())

    def _browse_output(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida", self.output_edit.text())
        if selected:
            self.output_edit.setText(selected)

    def set_interactions_enabled(self, enabled: bool) -> None:
        self.language_combo.setEnabled(enabled)
        self.profile_combo.setEnabled(enabled)
        self.output_edit.setEnabled(enabled)
        self.output_button.setEnabled(enabled)
