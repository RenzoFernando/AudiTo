from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from app.constants import DEFAULT_LANGUAGE, DEFAULT_PROFILE, LANGUAGES
from app.domain.model_profile import ModelProfile


class ChevronComboBox(QComboBox):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor("#cfd3da" if self.isEnabled() else "#5f646d")
        pen = QPen(color, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        center_x = self.width() - 13
        center_y = self.height() // 2
        painter.drawLine(center_x - 4, center_y - 2, center_x, center_y + 2)
        painter.drawLine(center_x, center_y + 2, center_x + 4, center_y - 2)


class SettingsWidget(QWidget):
    settings_changed = Signal(str, str)
    preferences_changed = Signal()

    def __init__(self, language: str, profile: str, output_dir: str, parent=None) -> None:
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)
        language_label = QLabel("Idioma")
        language_label.setObjectName("sectionLabel")
        profile_label = QLabel("Precisión")
        profile_label.setObjectName("sectionLabel")
        output_label = QLabel("Guardar en")
        output_label.setObjectName("sectionLabel")
        self.language_combo = ChevronComboBox()
        self.language_combo.addItems(list(LANGUAGES.keys()))
        self.language_combo.setCurrentText(language if language in LANGUAGES else DEFAULT_LANGUAGE)
        self.profile_combo = ChevronComboBox()
        self.profile_combo.addItems(ModelProfile.labels())
        self.profile_combo.setCurrentText(profile if profile in ModelProfile.labels() else DEFAULT_PROFILE)
        self.profile_hint = QLabel()
        self.profile_hint.setObjectName("modelHintLabel")
        self.output_edit = QLineEdit(output_dir)
        self.output_button = QPushButton("…")
        self.output_button.setObjectName("browseButton")
        self.output_button.setFixedWidth(36)
        self.output_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(language_label, 0, 0)
        layout.addWidget(profile_label, 0, 1)
        layout.addWidget(self.language_combo, 1, 0)
        layout.addWidget(self.profile_combo, 1, 1)
        layout.addWidget(self.profile_hint, 2, 0, 1, 2)
        layout.addWidget(output_label, 3, 0, 1, 2)
        output_row = QHBoxLayout()
        output_row.setSpacing(6)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row, 4, 0, 1, 2)
        self.language_combo.currentTextChanged.connect(self._language_changed)
        self.profile_combo.currentTextChanged.connect(self._profile_changed)
        self.output_edit.editingFinished.connect(self.preferences_changed.emit)
        self.output_button.clicked.connect(self._browse_output)
        self._update_profile_hint()

    def _language_changed(self) -> None:
        self._emit_settings_changed()
        self.preferences_changed.emit()

    def _profile_changed(self) -> None:
        self._update_profile_hint()
        self._emit_settings_changed()
        self.preferences_changed.emit()

    def _update_profile_hint(self) -> None:
        self.profile_hint.setText(ModelProfile.from_label(self.profile_combo.currentText()).hint)

    def _emit_settings_changed(self) -> None:
        self.settings_changed.emit(self.language_combo.currentText(), self.profile_combo.currentText())

    def _browse_output(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida", self.output_edit.text())
        if selected:
            self.output_edit.setText(selected)
            self.preferences_changed.emit()

    def set_interactions_enabled(self, enabled: bool) -> None:
        self.language_combo.setEnabled(enabled)
        self.profile_combo.setEnabled(enabled)
        self.output_edit.setEnabled(enabled)
        self.output_button.setEnabled(enabled)
