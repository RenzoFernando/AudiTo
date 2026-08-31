from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPalette, QPen
from PySide6.QtWidgets import QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton, QWidget

from app.constants import DEFAULT_LANGUAGE, DEFAULT_PROFILE, LANGUAGES, ONLINE_PROFILE_LABEL
from app.domain.model_profile import ModelProfile
from app.infrastructure.system.app_paths import AppPaths
from app.presentation.groq_api_dialog import GROQ_KEYS_URL, GROQ_LIMITS_URL, GROQ_USAGE_URL, GroqApiDialog
from app.presentation.translations import tr


class ChevronComboBox(QComboBox):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor("#5f646d" if not self.isEnabled() else ("#ffffff" if self.underMouse() else "#cfd3da"))
        pen = QPen(color, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        drop_width = 27.0
        center_x = self.width() - (drop_width / 2.0)
        center_y = self.height() / 2.0
        painter.drawLine(QPointF(center_x - 4.0, center_y - 2.0), QPointF(center_x, center_y + 2.0))
        painter.drawLine(QPointF(center_x, center_y + 2.0), QPointF(center_x + 4.0, center_y - 2.0))


class CenteredDotsButton(QPushButton):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor("#5f646d" if not self.isEnabled() else ("#ffffff" if self.underMouse() else "#cfd3da"))
        pen = QPen(color, 2.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        for offset in (-4.0, 0.0, 4.0):
            painter.drawPoint(QPointF(center_x + offset, center_y))


class TimestampToggleButton(QPushButton):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._prefix = ""
        self._state = ""

    def set_parts(self, prefix: str, state: str) -> None:
        self._prefix = str(prefix)
        self._state = str(state)
        self.setText(f"{self._prefix} · {self._state}")
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setFont(self.font())
        prefix = f"{self._prefix} · "
        metrics = painter.fontMetrics()
        prefix_width = metrics.horizontalAdvance(prefix)
        prefix_color = QColor("#5f646d" if not self.isEnabled() else "#ff6572")
        state_color = QColor("#5f646d" if not self.isEnabled() else "#ffffff")
        rect = self.rect()
        painter.setPen(prefix_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, prefix)
        state_rect = rect.adjusted(prefix_width, 0, 0, 0)
        painter.setPen(state_color)
        painter.drawText(state_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._state)


class SettingsWidget(QWidget):
    settings_changed = Signal(str, str)
    preferences_changed = Signal()

    def __init__(
        self,
        language: str,
        profile: str,
        output_dir: str,
        ui_language: str = "es",
        timestamps_enabled: bool = True,
        groq_api_key: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ui_language = ui_language
        self._default_output_dir = str(AppPaths.transcriptions_dir())
        self._output_dir = str(output_dir or self._default_output_dir)
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
        self.profile_hint.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.groq_api_label = QLabel()
        self.groq_api_label.setObjectName("sectionLabel")
        self.groq_api_edit = QLineEdit()
        self.groq_api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.groq_api_edit.setClearButtonEnabled(True)
        self.groq_api_edit.setText(str(groq_api_key or "").strip())
        self.groq_api_button = CenteredDotsButton()
        self.groq_api_button.setObjectName("browseButton")
        self.groq_api_button.setFixedWidth(36)
        self.groq_api_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timestamps_toggle = TimestampToggleButton()
        self.timestamps_toggle.setObjectName("timestampToggle")
        self.timestamps_toggle.setCheckable(True)
        self.timestamps_toggle.setChecked(bool(timestamps_enabled))
        self.timestamps_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timestamps_toggle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.output_edit = QLineEdit()
        output_palette = self.output_edit.palette()
        output_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#ff4655"))
        self.output_edit.setPalette(output_palette)
        self.output_button = CenteredDotsButton()
        self.output_button.setObjectName("browseButton")
        self.output_button.setFixedWidth(36)
        self.output_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.language_label, 0, 0)
        layout.addWidget(self.profile_label, 0, 1)
        layout.addWidget(self.language_combo, 1, 0)
        layout.addWidget(self.profile_combo, 1, 1)
        layout.addWidget(self.timestamps_toggle, 2, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.profile_hint, 2, 1)
        layout.addWidget(self.groq_api_label, 3, 0, 1, 2)
        groq_layout = QGridLayout()
        groq_layout.setContentsMargins(0, 0, 0, 0)
        groq_layout.setHorizontalSpacing(6)
        groq_layout.setColumnStretch(0, 1)
        groq_layout.addWidget(self.groq_api_edit, 0, 0)
        groq_layout.addWidget(self.groq_api_button, 0, 1)
        layout.addLayout(groq_layout, 4, 0, 1, 2)
        output_layout = QGridLayout()
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setHorizontalSpacing(6)
        output_layout.setVerticalSpacing(4)
        output_layout.setColumnStretch(0, 1)
        output_header = QHBoxLayout()
        output_header.setContentsMargins(0, 0, 0, 0)
        output_header.setSpacing(8)
        output_header.addWidget(self.output_label)
        output_header.addStretch(1)
        output_layout.addLayout(output_header, 0, 0, 1, 2)
        output_layout.addWidget(self.output_edit, 1, 0)
        output_layout.addWidget(self.output_button, 1, 1)
        layout.addLayout(output_layout, 5, 0, 2, 2)
        self._populate_language_combo(language if language in LANGUAGES else DEFAULT_LANGUAGE)
        valid_profiles = ModelProfile.labels() + [ONLINE_PROFILE_LABEL]
        self._populate_profile_combo(profile if profile in valid_profiles else DEFAULT_PROFILE)
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        self.profile_combo.currentIndexChanged.connect(self._profile_changed)
        self.timestamps_toggle.toggled.connect(self._timestamp_preference_changed)
        self.output_edit.editingFinished.connect(self._output_name_edited)
        self.groq_api_edit.editingFinished.connect(self._groq_api_edited)
        self.groq_api_button.clicked.connect(self._show_groq_menu)
        self.output_button.clicked.connect(self._browse_output)
        self._refresh_labels()
        self._update_profile_hint()
        self._refresh_online_controls()

    def selected_language(self) -> str:
        return str(self.language_combo.currentData() or DEFAULT_LANGUAGE)

    def selected_profile(self) -> str:
        return str(self.profile_combo.currentData() or DEFAULT_PROFILE)

    def timestamps_enabled(self) -> bool:
        return self.timestamps_toggle.isChecked()

    def groq_api_key(self) -> str:
        return self.groq_api_edit.text().strip()

    def output_dir(self) -> str:
        return self._output_dir.strip() or self._default_output_dir

    def output_name(self) -> str:
        return self.output_edit.text().strip()

    def set_output_name(self, name: str) -> None:
        self.output_edit.setText(str(name or "").strip())

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
        self._refresh_online_controls()

    def _language_changed(self) -> None:
        self._emit_settings_changed()
        self.preferences_changed.emit()

    def _profile_changed(self) -> None:
        self._update_profile_hint()
        self._refresh_online_controls()
        self._emit_settings_changed()
        self.preferences_changed.emit()

    def _timestamp_preference_changed(self) -> None:
        self._refresh_timestamp_text()
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
            ONLINE_PROFILE_LABEL: tr(self._ui_language, "profile_online"),
        }
        self.profile_combo.clear()
        for profile in ModelProfile:
            self.profile_combo.addItem(labels.get(profile.label, profile.label), profile.label)
        self.profile_combo.addItem(labels[ONLINE_PROFILE_LABEL], ONLINE_PROFILE_LABEL)
        index = self.profile_combo.findData(selected)
        self.profile_combo.setCurrentIndex(index if index >= 0 else 0)

    def _refresh_labels(self) -> None:
        self.language_label.setText(tr(self._ui_language, "transcription_language"))
        self.profile_label.setText(tr(self._ui_language, "precision"))
        self.output_label.setText(tr(self._ui_language, "save_as"))
        self.groq_api_label.setText(tr(self._ui_language, "groq_api_key"))
        self._refresh_timestamp_text()
        self.timestamps_toggle.setToolTip(tr(self._ui_language, "timestamps_tooltip"))
        self.output_edit.setPlaceholderText(tr(self._ui_language, "output_name_placeholder"))
        self.output_button.setToolTip(tr(self._ui_language, "select_output_folder"))
        self.groq_api_edit.setPlaceholderText(tr(self._ui_language, "groq_api_key_placeholder"))
        self.groq_api_edit.setToolTip(tr(self._ui_language, "groq_api_key_tooltip"))
        self.groq_api_button.setToolTip(tr(self._ui_language, "groq_api_menu_tooltip"))

    def _refresh_timestamp_text(self) -> None:
        state_key = "timestamps_on" if self.timestamps_toggle.isChecked() else "timestamps_off"
        self.timestamps_toggle.set_parts(
            tr(self._ui_language, "timestamps"),
            tr(self._ui_language, state_key),
        )

    def _update_profile_hint(self) -> None:
        keys = {
            "Rápida": "profile_hint_fast",
            "Equilibrada": "profile_hint_balanced",
            "Máxima": "profile_hint_maximum",
            ONLINE_PROFILE_LABEL: "profile_hint_online",
        }
        self.profile_hint.setText(tr(self._ui_language, keys.get(self.selected_profile(), "profile_hint_balanced")))

    def _refresh_online_controls(self) -> None:
        visible = self.selected_profile() == ONLINE_PROFILE_LABEL
        self.groq_api_label.setVisible(visible)
        self.groq_api_edit.setVisible(visible)
        self.groq_api_button.setVisible(visible)

    def _show_groq_menu(self) -> None:
        menu = QMenu(self)
        status_action = menu.addAction(tr(self._ui_language, "groq_api_menu_status"))
        usage_action = menu.addAction(tr(self._ui_language, "groq_api_menu_usage"))
        limits_action = menu.addAction(tr(self._ui_language, "groq_api_menu_limits"))
        menu.addSeparator()
        keys_action = menu.addAction(tr(self._ui_language, "groq_api_menu_keys"))
        selected = menu.exec(self.groq_api_button.mapToGlobal(self.groq_api_button.rect().bottomLeft()))
        if selected is status_action:
            dialog = GroqApiDialog(self.groq_api_key(), self._ui_language, self)
            dialog.exec()
        elif selected is usage_action:
            QDesktopServices.openUrl(QUrl(GROQ_USAGE_URL))
        elif selected is limits_action:
            QDesktopServices.openUrl(QUrl(GROQ_LIMITS_URL))
        elif selected is keys_action:
            QDesktopServices.openUrl(QUrl(GROQ_KEYS_URL))

    def _emit_settings_changed(self) -> None:
        self.settings_changed.emit(self.selected_language(), self.selected_profile())

    def _browse_output(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, tr(self._ui_language, "select_output_folder"), self.output_dir())
        if selected:
            self._output_dir = selected
            self.preferences_changed.emit()

    def _output_name_edited(self) -> None:
        self.preferences_changed.emit()

    def _groq_api_edited(self) -> None:
        self.preferences_changed.emit()

    def set_interactions_enabled(self, enabled: bool) -> None:
        self.language_combo.setEnabled(enabled)
        self.profile_combo.setEnabled(enabled)
        self.timestamps_toggle.setEnabled(enabled)
        self.output_edit.setEnabled(enabled)
        self.output_button.setEnabled(enabled)
        self.groq_api_edit.setEnabled(enabled)
        self.groq_api_button.setEnabled(enabled)
