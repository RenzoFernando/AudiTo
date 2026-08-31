from __future__ import annotations

from PySide6.QtCore import QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout

from app.infrastructure.groq.groq_account_service import GroqAccountError, GroqAccountService
from app.infrastructure.groq.groq_usage_tracker import GroqUsageTracker
from app.presentation.translations import tr, translate_runtime_message


GROQ_KEYS_URL = "https://console.groq.com/keys"
GROQ_USAGE_URL = "https://console.groq.com/dashboard/usage"
GROQ_LIMITS_URL = "https://console.groq.com/settings/project/limits"


class GroqKeyCheckWorker(QThread):
    valid = Signal()
    failed = Signal(str)

    def __init__(self, api_key: str, parent=None) -> None:
        super().__init__(parent)
        self._api_key = api_key

    def run(self) -> None:
        try:
            GroqAccountService().validate_api_key(self._api_key)
        except GroqAccountError as exc:
            self.failed.emit(str(exc))
            return
        except Exception:
            self.failed.emit("No se pudo verificar la API key de Groq.")
            return
        self.valid.emit()


class GroqApiDialog(QDialog):
    def __init__(self, api_key: str, ui_language: str, parent=None) -> None:
        super().__init__(parent)
        self._api_key = str(api_key or "").strip()
        self._ui_language = ui_language
        self._tracker = GroqUsageTracker()
        self._worker: GroqKeyCheckWorker | None = None
        self.setWindowTitle(self._t("groq_manager_title"))
        self.setModal(True)
        self.setMinimumWidth(410)
        self.setMaximumWidth(470)
        self._build_ui()
        self._refresh_usage()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(11)

        title = QLabel(self._t("groq_manager_title"))
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        subtitle = QLabel(self._t("groq_manager_subtitle"))
        subtitle.setObjectName("dialogMuted")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        key_frame = QFrame()
        key_frame.setObjectName("infoCard")
        key_layout = QVBoxLayout(key_frame)
        key_layout.setContentsMargins(12, 10, 12, 10)
        key_layout.setSpacing(6)
        key_title = QLabel(self._t("groq_key_status_title"))
        key_title.setObjectName("infoCardTitle")
        key_layout.addWidget(key_title)
        self.key_status = QLabel()
        self.key_status.setObjectName("dialogStatus")
        self.key_status.setWordWrap(True)
        key_layout.addWidget(self.key_status)
        self.check_button = QPushButton(self._t("groq_check_key"))
        self.check_button.setObjectName("dialogSecondaryButton")
        self.check_button.setEnabled(bool(self._api_key))
        self.check_button.clicked.connect(self._check_key)
        key_layout.addWidget(self.check_button)
        root.addWidget(key_frame)

        usage_frame = QFrame()
        usage_frame.setObjectName("infoCard")
        usage_layout = QVBoxLayout(usage_frame)
        usage_layout.setContentsMargins(12, 10, 12, 10)
        usage_layout.setSpacing(7)
        usage_title = QLabel(self._t("groq_local_usage_title"))
        usage_title.setObjectName("infoCardTitle")
        usage_layout.addWidget(usage_title)

        self.hour_label = QLabel()
        self.hour_label.setObjectName("dialogValue")
        usage_layout.addWidget(self.hour_label)
        self.hour_progress = QProgressBar()
        self.hour_progress.setObjectName("quotaProgress")
        self.hour_progress.setRange(0, 1000)
        self.hour_progress.setTextVisible(False)
        usage_layout.addWidget(self.hour_progress)

        self.day_label = QLabel()
        self.day_label.setObjectName("dialogValue")
        usage_layout.addWidget(self.day_label)
        self.day_progress = QProgressBar()
        self.day_progress.setObjectName("quotaProgress")
        self.day_progress.setRange(0, 1000)
        self.day_progress.setTextVisible(False)
        usage_layout.addWidget(self.day_progress)

        self.requests_label = QLabel()
        self.requests_label.setObjectName("dialogMuted")
        self.requests_label.setWordWrap(True)
        usage_layout.addWidget(self.requests_label)

        note = QLabel(self._t("groq_usage_estimate_note"))
        note.setObjectName("dialogMuted")
        note.setWordWrap(True)
        usage_layout.addWidget(note)
        root.addWidget(usage_frame)

        limits_frame = QFrame()
        limits_frame.setObjectName("infoCard")
        limits_layout = QVBoxLayout(limits_frame)
        limits_layout.setContentsMargins(12, 10, 12, 10)
        limits_layout.setSpacing(4)
        limits_title = QLabel(self._t("groq_free_limits_title"))
        limits_title.setObjectName("infoCardTitle")
        limits_layout.addWidget(limits_title)
        limits = QLabel(self._t("groq_free_limits_detail"))
        limits.setObjectName("dialogValue")
        limits.setWordWrap(True)
        limits_layout.addWidget(limits)
        limits_note = QLabel(self._t("groq_free_limits_note"))
        limits_note.setObjectName("dialogMuted")
        limits_note.setWordWrap(True)
        limits_layout.addWidget(limits_note)
        root.addWidget(limits_frame)

        links = QHBoxLayout()
        links.setSpacing(7)
        usage_button = QPushButton(self._t("groq_open_usage"))
        usage_button.setObjectName("dialogSecondaryButton")
        usage_button.clicked.connect(lambda: self._open_url(GROQ_USAGE_URL))
        limits_button = QPushButton(self._t("groq_open_limits"))
        limits_button.setObjectName("dialogSecondaryButton")
        limits_button.clicked.connect(lambda: self._open_url(GROQ_LIMITS_URL))
        links.addWidget(usage_button, 1)
        links.addWidget(limits_button, 1)
        root.addLayout(links)

        keys_button = QPushButton(self._t("groq_manage_keys"))
        keys_button.setObjectName("dialogSecondaryButton")
        keys_button.clicked.connect(lambda: self._open_url(GROQ_KEYS_URL))
        root.addWidget(keys_button)

        close_button = QPushButton(self._t("close"))
        close_button.setObjectName("dialogPrimaryButton")
        close_button.clicked.connect(self.accept)
        root.addWidget(close_button)

        self.key_status.setText(self._t("groq_key_configured") if self._api_key else self._t("groq_key_missing"))

    def _refresh_usage(self) -> None:
        snapshot = self._tracker.snapshot(self._api_key)
        hour_limit = self._tracker.FREE_AUDIO_SECONDS_HOUR
        day_limit = self._tracker.FREE_AUDIO_SECONDS_DAY
        hour_remaining = max(0.0, hour_limit - snapshot.audio_seconds_hour)
        day_remaining = max(0.0, day_limit - snapshot.audio_seconds_day)
        self.hour_label.setText(
            self._t(
                "groq_usage_hour",
                used=self._format_duration(snapshot.audio_seconds_hour),
                limit=self._format_duration(hour_limit),
                remaining=self._format_duration(hour_remaining),
            )
        )
        self.day_label.setText(
            self._t(
                "groq_usage_day",
                used=self._format_duration(snapshot.audio_seconds_day),
                limit=self._format_duration(day_limit),
                remaining=self._format_duration(day_remaining),
            )
        )
        self.hour_progress.setValue(min(1000, int((snapshot.audio_seconds_hour / hour_limit) * 1000)))
        self.day_progress.setValue(min(1000, int((snapshot.audio_seconds_day / day_limit) * 1000)))
        if snapshot.remaining_requests_day is not None:
            limit = snapshot.request_limit_day or self._tracker.FREE_REQUESTS_DAY
            reset = f" · {self._t('groq_request_reset', reset=snapshot.request_reset)}" if snapshot.request_reset else ""
            self.requests_label.setText(
                self._t(
                    "groq_requests_from_api",
                    remaining=snapshot.remaining_requests_day,
                    limit=limit,
                ) + reset
            )
        elif snapshot.last_success_at:
            self.requests_label.setText(self._t("groq_requests_unavailable"))
        else:
            self.requests_label.setText(self._t("groq_requests_waiting"))

    def _check_key(self) -> None:
        if not self._api_key or (self._worker is not None and self._worker.isRunning()):
            return
        self.key_status.setText(self._t("groq_key_checking"))
        self.check_button.setEnabled(False)
        worker = GroqKeyCheckWorker(self._api_key, self)
        worker.valid.connect(self._key_valid)
        worker.failed.connect(self._key_failed)
        worker.finished.connect(lambda worker=worker: self._dispose_worker(worker))
        self._worker = worker
        worker.start()

    def _key_valid(self) -> None:
        self.key_status.setText(self._t("groq_key_valid"))

    def _key_failed(self, message: str) -> None:
        self.key_status.setText(translate_runtime_message(self._ui_language, message))

    def _dispose_worker(self, worker: GroqKeyCheckWorker) -> None:
        if self._worker is worker:
            self._worker = None
        worker.deleteLater()
        self.check_button.setEnabled(bool(self._api_key))

    def _open_url(self, url: str) -> None:
        QDesktopServices.openUrl(QUrl(url))

    def _format_duration(self, seconds: float) -> str:
        total = max(0, int(round(float(seconds))))
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            if minutes:
                return f"{hours} h {minutes} min"
            return f"{hours} h"
        if minutes:
            return f"{minutes} min"
        return f"{secs} s"

    def _t(self, key: str, **values) -> str:
        return tr(self._ui_language, key, **values)

    def accept(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        super().accept()

    def reject(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        super().reject()

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            event.ignore()
            return
        super().closeEvent(event)
