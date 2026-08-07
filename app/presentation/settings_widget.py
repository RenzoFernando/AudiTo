from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from app.constants import DEFAULT_LANGUAGE, DEFAULT_PROFILE, LANGUAGES
from app.domain.model_profile import ModelProfile
from app.presentation.translations import tr


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

    def __init__(self, language: str, profile: str, output_dir: str, ui_language: str = "es", parent=None) -> None:
        super().__init__(parent)
        self._ui_language = ui_language
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)
        self.language_label = QLabel()
        self.language_label.setObjectName("sectionLabel")
        self.profile_label = QLabel()
        self.profile_label.setObjectName("sectionLabel")
        self.output_label = QLabel()
        self.output_label.setObjectName("sectionLabel")
        self.language_combo = ChevronComboBox()
        self.profile_combo = ChevronComboBox()
        self.profile_hint = QLabel()
        self.profile_hint.setObjectName("modelHintLabel")
        self.output_edit = QLineEdit(output_dir)
        self.output_button = QPushButton("…")
        self.output_button.setObjectName("browseButton")
        self.output_button.setFixedWidth(36)
        self.output_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.language_label, 0, 0)
        layout.addWidget(self.profile_label, 0, 1)
        layout.addWidget(self.language_combo, 1, 0)
        layout.addWidget(self.profile_combo, 1, 1)
        layout.addWidget(self.profile_hint, 2, 0, 1, 2)
        layout.addWidget(self.output_label, 3, 0, 1, 2)
        output_row = QHBoxLayout()
        output_row.setSpacing(6)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row, 4, 0, 1, 2)
        self._populate_language_combo(language if language in LANGUAGES else DEFAULT_LANGUAGE)
        self._populate_profile_combo(profile if profile in ModelProfile.labels() else DEFAULT_PROFILE)
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        self.profile_combo.currentIndexChanged.connect(self._profile_changed)
        self.output_edit.editingFinished.connect(self.preferences_changed.emit)
        self.output_button.clicked.connect(self._browse_output)
        self._refresh_labels()
        self._update_profile_hint()

    def selected_language(self) -> str:
        return str(self.language_combo.currentData() or DEFAULT_LANGUAGE)

    def selected_profile(self) -> str:
        return str(self.profile_combo.currentData() or DEFAULT_PROFILE)

    def set_ui_language(self, ui_language: str) -> None:
        language_value = self.selected_language()
        profile_value = self.selected_profile()
        self._ui_language = ui_language
        self.language_combo.blockSignals(True)
        self.profile_combo.blockSignals(True)
        self._populate_language_combo(language_value)
        self._populate_profile_combo(profile_value)
        self.language_combo.blockSignals(False)
        self.profile_combo.blockSignals(False)
        self._refresh_labels()
        self._update_profile_hint()

    def _language_changed(self) -> None:
        self._emit_settings_changed()
        self.preferences_changed.emit()

    def _profile_changed(self) -> None:
        self._update_profile_hint()
        self._emit_settings_changed()
        self.preferences_changed.emit()

    def _populate_language_combo(self, selected: str) -> None:
        labels = {
            "Español": tr(self._ui_language, "language_spanish"),
            "Inglés": tr(self._ui_language, "language_english"),
            "Automático": tr(self._ui_language, "language_auto"),
        }
        self.language_combo.clear()
        for canonical in LANGUAGES:
            self.language_combo.addItem(labels.get(canonical, canonical), canonical)
        index = self.language_combo.findData(selected)
        self.language_combo.setCurrentIndex(index if index >= 0 else 0)

    def _populate_profile_combo(self, selected: str) -> None:
        labels = {
            "Rápida": tr(self._ui_language, "profile_fast"),
            "Equilibrada": tr(self._ui_language, "profile_balanced"),
            "Máxima": tr(self._ui_language, "profile_maximum"),
        }
        self.profile_combo.clear()
        for profile in ModelProfile:
            self.profile_combo.addItem(labels.get(profile.label, profile.label), profile.label)
        index = self.profile_combo.findData(selected)
        self.profile_combo.setCurrentIndex(index if index >= 0 else 0)

    def _refresh_labels(self) -> None:
        self.language_label.setText(tr(self._ui_language, "transcription_language"))
        self.profile_label.setText(tr(self._ui_language, "precision"))
        self.output_label.setText(tr(self._ui_language, "save_in"))
        self.output_button.setToolTip(tr(self._ui_language, "select_output_folder"))

    def _update_profile_hint(self) -> None:
        keys = {
            "Rápida": "profile_hint_fast",
            "Equilibrada": "profile_hint_balanced",
            "Máxima": "profile_hint_maximum",
        }
        self.profile_hint.setText(tr(self._ui_language, keys.get(self.selected_profile(), "profile_hint_balanced")))

    def _emit_settings_changed(self) -> None:
        self.settings_changed.emit(self.selected_language(), self.selected_profile())

    def _browse_output(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, tr(self._ui_language, "select_output_folder"), self.output_edit.text())
        if selected:
            self.output_edit.setText(selected)
            self.preferences_changed.emit()

    def set_interactions_enabled(self, enabled: bool) -> None:
        self.language_combo.setEnabled(enabled)
        self.profile_combo.setEnabled(enabled)
        self.output_edit.setEnabled(enabled)
        self.output_button.setEnabled(enabled)
