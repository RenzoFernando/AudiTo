from __future__ import annotations

import logging
import math
import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.application.current_audio_service import CurrentAudioService
from app.application.live_transcription_service import LiveTranscriptionService
from app.application.recording_service import AudioRecordingError, RecordingService
from app.constants import APP_NAME, APP_VERSION, GITHUB_URL, LANGUAGES, SUPPORTED_AUDIO_EXTENSIONS, WINDOW_HEIGHT, WINDOW_WIDTH
from app.domain.app_state import AppState
from app.domain.job_status import JobStatus
from app.domain.model_profile import ModelProfile
from app.domain.transcription_job import TranscriptionJob
from app.infrastructure.models.model_repository import ModelRepository
from app.infrastructure.persistence.settings_repository import SettingsRepository
from app.presentation.current_audio_widget import CurrentAudioWidget
from app.presentation.input_widget import AudioInputWidget
from app.presentation.progress_widget import ProgressWidget
from app.presentation.settings_widget import SettingsWidget
from app.presentation.styles import APP_STYLE
from app.presentation.translations import tr, translate_runtime_message
from app.workers.live_transcription_worker import LiveTranscriptionWorker
from app.workers.transcription_worker import TranscriptionWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._settings_repository = SettingsRepository()
        self._settings = self._settings_repository.load()
        self._ui_language = self._settings["ui_language"]
        self._model_repository = ModelRepository()
        self._current_audio = CurrentAudioService()
        self._recording_service = RecordingService()
        self._state = AppState.IDLE
        self._worker: TranscriptionWorker | None = None
        self._live_worker: LiveTranscriptionWorker | None = None
        self._live_service: LiveTranscriptionService | None = None
        self._current_job_id: str | None = None
        self._transcription_started_at: float | None = None
        self._eta_seconds: float | None = None
        self._recording_started_at: float | None = None
        self._last_output_path: Path | None = None
        self._recording_previous_job: TranscriptionJob | None = None
        self._recording_previous_output_path: Path | None = None
        self._live_failed_message: str | None = None
        self._live_speed_factor: float | None = None
        self._discard_restore_pending = False
        self._recording_error_handled = False
        self._finalization_duration = 0.0
        self._finalization_confirmed = 0.0
        self._finalization_started_at: float | None = None
        self._finalization_eta_seconds: float | None = None
        self._finalization_stage = "processing"
        self._record_timer = QTimer(self)
        self._record_timer.setInterval(250)
        self._record_timer.timeout.connect(self._update_recording_time)
        self._finalization_timer = QTimer(self)
        self._finalization_timer.setInterval(1000)
        self._finalization_timer.timeout.connect(self._update_finalization_progress)
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self.input_widget.set_microphone_name(self._recording_service.default_input_name())
        self._refresh_static_text()
        self._apply_state()

    def _build_ui(self) -> None:
        shell = QWidget()
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(16, 13, 16, 10)
        root.setSpacing(8)
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 2)
        brand_row.setSpacing(8)
        brand_row.addWidget(self._accent_group(True))
        left_language_spacer = QWidget()
        left_language_spacer.setFixedWidth(36)
        brand_row.addWidget(left_language_spacer)
        brand_row.addStretch(1)
        brand = QLabel(APP_NAME)
        brand.setObjectName("brandLabel")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_row.addWidget(brand, 0, Qt.AlignmentFlag.AlignCenter)
        brand_row.addStretch(1)
        self.language_toggle_button = QPushButton()
        self.language_toggle_button.setObjectName("languageToggleButton")
        self.language_toggle_button.setFixedSize(36, 24)
        self.language_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.language_toggle_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.language_toggle_button.clicked.connect(self._toggle_ui_language)
        brand_row.addWidget(self.language_toggle_button)
        brand_row.addWidget(self._accent_group(False))
        root.addLayout(brand_row)
        self.input_widget = AudioInputWidget(self._ui_language)
        self.input_widget.files_selected.connect(self._select_audio)
        self.input_widget.browse_requested.connect(self._browse_audio)
        self.input_widget.record_requested.connect(self._start_recording)
        self.input_widget.stop_record_requested.connect(self._stop_recording)
        self.input_widget.discard_record_requested.connect(self._discard_recording)
        root.addWidget(self.input_widget)
        self.current_audio_widget = CurrentAudioWidget(self._ui_language)
        self.current_audio_widget.remove_requested.connect(self._clear_audio)
        root.addWidget(self.current_audio_widget)
        self.settings_widget = SettingsWidget(
            self._settings["language"],
            self._settings["profile"],
            self._settings["output_dir"],
            self._ui_language,
        )
        self.settings_widget.settings_changed.connect(self._update_selected_settings)
        self.settings_widget.preferences_changed.connect(self._preferences_changed)
        root.addWidget(self.settings_widget)
        self.progress_widget = ProgressWidget(self._ui_language)
        root.addWidget(self.progress_widget)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.transcribe_button = QPushButton()
        self.transcribe_button.setObjectName("primaryButton")
        self.transcribe_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transcribe_button.clicked.connect(self._start_transcription)
        self.cancel_button = QPushButton()
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cancel_button.clicked.connect(self._cancel_current)
        actions.addWidget(self.transcribe_button, 1)
        actions.addWidget(self.cancel_button)
        root.addLayout(actions)
        result_layout = QHBoxLayout()
        result_layout.setSpacing(8)
        self.open_file_button = QPushButton()
        self.open_file_button.setObjectName("openFileButton")
        self.open_file_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.open_file_button.clicked.connect(self._open_last_transcription)
        self.open_folder_button = QPushButton()
        self.open_folder_button.setObjectName("openFolderButton")
        self.open_folder_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.open_folder_button.clicked.connect(self._open_output_folder)
        result_layout.addWidget(self.open_file_button, 1)
        result_layout.addWidget(self.open_folder_button, 1)
        root.addLayout(result_layout)
        footer = QFrame()
        footer.setObjectName("footerFrame")
        footer.setFixedHeight(32)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 0, 10, 0)
        footer_layout.setSpacing(4)
        footer_layout.addStretch(1)
        self.footer_label = QLabel()
        self.footer_label.setObjectName("footerLabel")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(self.footer_label)
        self.github_button = QPushButton("GitHub")
        self.github_button.setObjectName("footerLinkButton")
        self.github_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.github_button.clicked.connect(self._open_github)
        footer_layout.addWidget(self.github_button)
        footer_layout.addStretch(1)
        shell_layout.addWidget(content)
        shell_layout.addWidget(footer)
        self.setCentralWidget(shell)

    def _accent_group(self, mirrored: bool) -> QWidget:
        group = QWidget()
        group.setFixedWidth(52)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        definitions = [("accentRed", 24), ("accentGrayStrong", 11), ("accentGraySoft", 6)]
        if mirrored:
            definitions = list(reversed(definitions))
        for name, width in definitions:
            accent = QFrame()
            accent.setObjectName(name)
            accent.setFixedSize(width, 3)
            layout.addWidget(accent, 0, Qt.AlignmentFlag.AlignVCenter)
        return group

    def _t(self, key: str, **values) -> str:
        return tr(self._ui_language, key, **values)

    def _runtime_message(self, message: str) -> str:
        return translate_runtime_message(self._ui_language, message)

    def _refresh_static_text(self) -> None:
        self.language_toggle_button.setText(self._t("app_language_code"))
        self.language_toggle_button.setToolTip(self._t("switch_language_tooltip"))
        self.transcribe_button.setText(self._t("transcribe"))
        self.cancel_button.setText(self._t("cancel"))
        self.open_file_button.setText(self._t("open_transcription"))
        self.open_folder_button.setText(self._t("open_folder"))
        self.footer_label.setText(f"Copyright © 2026 · Renzo Fernando Mosquera Daza · v{APP_VERSION} ·")
        self.github_button.setToolTip(self._t("github_tooltip"))

    def _toggle_ui_language(self) -> None:
        if not self._is_stable_state():
            return
        self._ui_language = "en" if self._ui_language == "es" else "es"
        self.input_widget.set_ui_language(self._ui_language)
        self.current_audio_widget.set_ui_language(self._ui_language)
        self.settings_widget.set_ui_language(self._ui_language)
        self.progress_widget.set_ui_language(self._ui_language)
        self._refresh_static_text()
        self._refresh_stable_status()
        self._save_settings()
        self._apply_state()

    def _refresh_stable_status(self) -> None:
        if self._state == AppState.IDLE:
            self.progress_widget.set_idle(self._t("status_waiting"))
        elif self._state == AppState.AUDIO_SELECTED:
            self.progress_widget.set_idle(self._t("status_ready"))
        elif self._state == AppState.COMPLETED:
            self.progress_widget.set_completed(self._t("status_completed"), self._t("txt_ready"))
        elif self._state == AppState.CANCELLED:
            self.progress_widget.set_idle(self._t("status_cancelled"), self._t("partial_kept"))
        elif self._state == AppState.ERROR:
            self.progress_widget.set_idle(self._t("generic_error"))

    def _browse_audio(self) -> None:
        if not self._is_stable_state():
            return
        patterns = " ".join(f"*{extension}" for extension in sorted(SUPPORTED_AUDIO_EXTENSIONS))
        filter_text = f"{self._t('audio_files_filter', patterns=patterns)};;{self._t('all_files_filter')}"
        path, _ = QFileDialog.getOpenFileName(self, self._t("select_audio_dialog"), "", filter_text)
        if path:
            self._select_audio([path])

    def _select_audio(self, paths: list[str]) -> None:
        if not self._is_stable_state():
            return
        job, rejected, ignored_count = self._current_audio.select(
            paths,
            self.settings_widget.selected_language(),
            self.settings_widget.selected_profile(),
        )
        if job is None:
            if rejected:
                QMessageBox.warning(self, self._t("incompatible_file_title"), self._t("incompatible_file_message"))
            return
        self._last_output_path = None
        self.current_audio_widget.show_audio(job.input_path, job.duration)
        self.progress_widget.set_idle(self._t("status_ready"))
        if ignored_count:
            self.progress_widget.set_idle(self._t("status_one_audio"), self._t("one_audio_at_time"))
        self._set_state(AppState.AUDIO_SELECTED)

    def _clear_audio(self) -> None:
        if not self._is_stable_state():
            return
        self._current_audio.clear()
        self._last_output_path = None
        self.current_audio_widget.show_empty()
        self.progress_widget.set_idle(self._t("status_waiting"))
        self._set_state(AppState.IDLE)

    def _update_selected_settings(self, language: str, profile: str) -> None:
        self._current_audio.update_settings(language, profile)

    def _preferences_changed(self) -> None:
        self._save_settings()
        self._apply_state()

    def _output_directory(self, show_errors: bool = True) -> Path | None:
        output_text = self.settings_widget.output_edit.text().strip()
        if not output_text:
            if show_errors:
                QMessageBox.warning(self, self._t("output_folder_title"), self._t("select_output_folder_message"))
            return None
        output_dir = Path(output_text).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            test_path = output_dir / ".audito_write_test"
            test_path.write_text("ok", encoding="utf-8")
            test_path.unlink(missing_ok=True)
            return output_dir
        except OSError as exc:
            if show_errors:
                message = self._t("no_space_files") if getattr(exc, "errno", None) == 28 else self._t("cannot_write_folder")
                QMessageBox.warning(self, self._t("output_folder_title"), message)
            return None
        except Exception:
            if show_errors:
                QMessageBox.warning(self, self._t("output_folder_title"), self._t("cannot_write_folder"))
            return None

    def _start_recording(self) -> None:
        if not self._is_stable_state():
            return
        output_dir = self._output_directory()
        if output_dir is None:
            return
        self._recording_previous_job = self._current_audio.job
        self._recording_previous_output_path = self._last_output_path
        self._live_failed_message = None
        self._live_speed_factor = None
        self._discard_restore_pending = False
        self._recording_error_handled = False
        self._reset_finalization_progress()
        try:
            session = self._recording_service.start(output_dir)
        except AudioRecordingError as exc:
            QMessageBox.warning(self, self._t("record_failed_title"), self._runtime_message(str(exc)))
            return
        buffer = self._recording_service.buffer
        if buffer is None:
            self._recording_service.discard()
            QMessageBox.warning(self, self._t("record_failed_title"), self._t("record_buffer_failed"))
            return
        language_label = self.settings_widget.selected_language()
        profile_label = self.settings_widget.selected_profile()
        live_job = TranscriptionJob(
            input_path=session.path,
            language_label=language_label,
            language_code=LANGUAGES.get(language_label),
            model_profile=ModelProfile.from_label(profile_label),
            duration=None,
        )
        self._live_service = LiveTranscriptionService(live_job, output_dir, buffer)
        worker = LiveTranscriptionWorker(self._live_service, self)
        worker.live_status.connect(self._on_live_status)
        worker.live_confirmed.connect(self._on_live_confirmed)
        worker.live_metrics.connect(self._on_live_metrics)
        worker.live_completed.connect(self._on_live_completed)
        worker.live_failed.connect(self._on_live_failed)
        worker.live_cancelled.connect(self._on_live_cancelled)
        worker.finished.connect(lambda worker=worker: self._dispose_live_worker(worker))
        self._live_worker = worker
        self._last_output_path = None
        self.current_audio_widget.show_recording(session.path)
        self.input_widget.set_recording(True)
        self._recording_started_at = time.monotonic()
        self.input_widget.set_recording_time(0)
        self._record_timer.start()
        self.progress_widget.set_recording(self._t("status_preparing_live"), self._t("live_starts_around"))
        self._set_state(AppState.RECORDING)
        worker.start()

    def _stop_recording(self) -> None:
        if not self._recording_service.is_recording:
            return
        self._record_timer.stop()
        session_before = self._recording_service.session
        elapsed = max(0.0, time.monotonic() - self._recording_started_at) if self._recording_started_at is not None else 0.0
        try:
            session = self._recording_service.stop()
        except AudioRecordingError as exc:
            self._recording_started_at = None
            self.input_widget.set_recording(False)
            if session_before is not None and session_before.path.exists():
                job = self._current_audio.set_recording(
                    session_before.path,
                    elapsed,
                    self.settings_widget.selected_language(),
                    self.settings_widget.selected_profile(),
                )
                self.current_audio_widget.show_audio(job.input_path, job.duration, recorded_audio=True)
            if self._live_worker and self._live_worker.isRunning():
                self._live_worker.request_cancel(False)
            self.progress_widget.set_idle(self._t("status_recording_stopped"), self._t("saved_audio_kept"))
            self._recording_service.reset()
            self._set_state(AppState.ERROR)
            QMessageBox.warning(self, self._t("recording_error_title"), self._runtime_message(str(exc)))
            return
        self._recording_started_at = None
        self.input_widget.set_recording(False)
        job = self._current_audio.set_recording(
            session.path,
            session.duration,
            self.settings_widget.selected_language(),
            self.settings_widget.selected_profile(),
        )
        self.current_audio_widget.show_audio(job.input_path, job.duration, recorded_audio=True)
        self.current_audio_widget.set_state("recorded")
        if self._live_failed_message:
            self.progress_widget.set_idle(self._t("status_recording_saved"), self._t("live_stopped_press_transcribe"))
            self._recording_service.reset()
            self._set_state(AppState.ERROR)
            return
        if self._live_worker and self._live_worker.isRunning():
            self._set_state(AppState.FINALIZING_RECORDING)
            self._start_finalization_progress(session.duration)
            self._live_worker.request_finalize(session.duration)
        else:
            self.progress_widget.set_idle(self._t("status_recording_saved"), self._t("press_transcribe_for_txt"))
            self._recording_service.reset()
            self._set_state(AppState.AUDIO_SELECTED)

    def _discard_recording(self) -> None:
        if not self._recording_service.is_recording:
            return
        answer = QMessageBox.question(
            self,
            self._t("discard_recording_title"),
            self._t("discard_recording_question"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._record_timer.stop()
        self._recording_started_at = None
        self._discard_restore_pending = True
        self._recording_service.discard()
        self.input_widget.set_recording(False)
        self.progress_widget.set_indeterminate(self._t("discarding_recording"), "")
        self._set_state(AppState.FINALIZING_RECORDING)
        if self._live_worker and self._live_worker.isRunning():
            self._live_worker.request_cancel(True)
        else:
            if self._live_service is not None:
                self._live_service.discard_output()
            self._restore_after_discard()

    def _update_recording_time(self) -> None:
        if self._recording_started_at is None:
            return
        elapsed = int(time.monotonic() - self._recording_started_at)
        self.input_widget.set_recording_time(elapsed)
        if self._recording_service.writer_error is not None and not self._recording_error_handled:
            self._recording_error_handled = True
            QTimer.singleShot(0, self._stop_recording)

    def _start_transcription(self) -> None:
        if not self._is_stable_state():
            return
        job = self._current_audio.job
        if job is None:
            QMessageBox.information(self, self._t("no_audio_title"), self._t("no_audio_message"))
            return
        output_dir = self._output_directory()
        if output_dir is None:
            return
        self._current_audio.update_settings(
            self.settings_widget.selected_language(),
            self.settings_widget.selected_profile(),
        )
        job.status = JobStatus.PENDING
        job.progress = 0
        job.error = None
        self._last_output_path = None
        self._transcription_started_at = None
        self._eta_seconds = None
        self.progress_widget.set_file_progress(0, self._t("remaining_calculating"))
        self._set_state(AppState.TRANSCRIBING_FILE)
        worker = TranscriptionWorker(job, output_dir, self)
        worker.job_started.connect(self._on_job_started)
        worker.job_progress.connect(self._on_job_progress)
        worker.job_status.connect(self._on_job_status)
        worker.job_completed.connect(self._on_job_completed)
        worker.job_failed.connect(self._on_job_failed)
        worker.job_cancelled.connect(self._on_job_cancelled)
        worker.task_finished.connect(self._on_file_task_finished)
        worker.finished.connect(lambda worker=worker: self._dispose_file_worker(worker))
        self._worker = worker
        worker.start()

    def _cancel_current(self) -> None:
        if self._worker and self._worker.isRunning() and self._current_job_id:
            self.progress_widget.set_indeterminate(self._t("status_cancelling"), self._t("partial_kept"))
            self.cancel_button.setEnabled(False)
            self._worker.cancel_current()

    def _on_job_started(self, job_id: str) -> None:
        self._current_job_id = job_id
        self.progress_widget.set_indeterminate(self._t("status_preparing_audio"), "")
        self._apply_state()

    def _on_job_status(self, job_id: str, status: str) -> None:
        if status == "Descargando modelo por primera vez":
            self.progress_widget.set_indeterminate(self._t("status_downloading_model"), self._t("first_time_only"))
            return
        if status == "Cargando modelo":
            self.progress_widget.set_indeterminate(self._t("status_loading_model"), self._t("preparing_transcription"))
            return
        if status == "Transcribiendo":
            self._transcription_started_at = time.monotonic()
            self._eta_seconds = None
            self.progress_widget.set_file_progress(0, self._t("remaining_calculating"))
            return
        if status == "Guardando":
            self.progress_widget.set_indeterminate(self._t("status_saving"), "")
            return
        if status == "GPU no disponible. Usando CPU":
            self.progress_widget.set_indeterminate(self._t("status_preparing_audio"), self._t("gpu_unavailable_cpu"))
            return
        self.progress_widget.set_indeterminate(self._runtime_message(status), "")

    def _on_job_progress(self, job_id: str, value: int) -> None:
        value = max(0, min(100, int(value)))
        detail = self._t("remaining_calculating")
        if value >= 2 and value < 100 and self._transcription_started_at is not None:
            elapsed = max(0.1, time.monotonic() - self._transcription_started_at)
            raw_eta = elapsed * (100 - value) / value
            if self._eta_seconds is None:
                self._eta_seconds = raw_eta
            else:
                self._eta_seconds = self._eta_seconds * 0.72 + raw_eta * 0.28
            detail = self._t("remaining_approx", remaining=self._format_remaining(self._eta_seconds))
        elif value >= 100:
            detail = ""
        self.progress_widget.set_file_progress(value, detail)

    def _on_job_completed(self, job_id: str, output_path: str) -> None:
        self._last_output_path = Path(output_path)
        self.current_audio_widget.set_state("completed")
        self.progress_widget.set_completed(self._t("status_completed_percent"), self._t("finished"))
        self._set_state(AppState.COMPLETED)

    def _on_job_failed(self, job_id: str, message: str) -> None:
        self.progress_widget.set_idle(self._t("transcription_failed_title"), self._t("partial_kept"))
        self._set_state(AppState.ERROR)
        translated_message = self._runtime_message(message)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self._t("transcription_failed_title"))
        box.setText(translated_message)
        needs_retry = "conéctate a internet" in message.casefold() or "connect to the internet" in message.casefold()
        if needs_retry:
            box.setStandardButtons(QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close)
            if box.exec() == QMessageBox.StandardButton.Retry:
                QTimer.singleShot(0, self._start_transcription)
        else:
            box.setStandardButtons(QMessageBox.StandardButton.Close)
            box.exec()

    def _on_job_cancelled(self, job_id: str) -> None:
        self.progress_widget.set_idle(self._t("status_cancelled"), self._t("partial_kept"))
        self._set_state(AppState.CANCELLED)

    def _on_file_task_finished(self) -> None:
        self._current_job_id = None
        self._save_settings()
        self._apply_state()

    def _on_live_status(self, status: str) -> None:
        if self._discard_restore_pending:
            return
        if self._state == AppState.FINALIZING_RECORDING:
            if status == "Descargando modelo por primera vez":
                self._finalization_stage = "downloading"
            elif status == "Cargando modelo":
                self._finalization_stage = "loading"
            elif status == "Transcribiendo":
                self._finalization_stage = "processing"
            self._update_finalization_progress()
            return
        if not self._recording_service.is_recording:
            return
        if status == "Descargando modelo por primera vez":
            self.progress_widget.set_recording(self._t("status_recording"), self._t("downloading_transcription_model"))
            return
        if status == "Cargando modelo":
            self.progress_widget.set_recording(self._t("status_recording"), self._t("loading_transcription_model"))
            return
        if status == "Transcribiendo":
            self.progress_widget.set_recording(self._t("status_background_transcribing"), self._t("processing_recent_audio"))
            self._set_state(AppState.RECORDING_TRANSCRIBING)
            return
        if status == "GPU no disponible. Usando CPU":
            self.progress_widget.set_recording(self._t("status_recording"), self._t("gpu_unavailable_cpu"))

    def _on_live_metrics(self, audio_seconds: float, processing_seconds: float) -> None:
        if audio_seconds <= 0 or processing_seconds <= 0:
            return
        factor = min(30.0, max(0.05, processing_seconds / audio_seconds))
        if self._live_speed_factor is None:
            self._live_speed_factor = factor
        else:
            self._live_speed_factor = self._live_speed_factor * 0.68 + factor * 0.32
        if self._state == AppState.FINALIZING_RECORDING:
            self._recalculate_finalization_eta(self._finalization_confirmed)

    def _on_live_confirmed(self, seconds: float) -> None:
        if self._discard_restore_pending:
            return
        if self._state == AppState.FINALIZING_RECORDING:
            self._finalization_confirmed = max(self._finalization_confirmed, seconds)
            self._finalization_stage = "processing"
            self._recalculate_finalization_eta(self._finalization_confirmed)
            self._update_finalization_progress()
            return
        if self._recording_service.is_recording:
            detail = self._t("processed_until", time=self._format_clock(seconds))
            self.progress_widget.set_recording(self._t("status_background_transcribing"), detail)
            self._set_state(AppState.RECORDING_TRANSCRIBING)

    def _on_live_completed(self, output_path: str) -> None:
        if self._discard_restore_pending:
            return
        self._reset_finalization_progress()
        self._last_output_path = Path(output_path)
        self.current_audio_widget.set_state("completed")
        self.progress_widget.set_completed(self._t("status_completed"), self._t("txt_ready"))
        self._recording_service.reset()
        self._live_service = None
        self._set_state(AppState.COMPLETED)
        self._save_settings()

    def _on_live_failed(self, message: str) -> None:
        self._reset_finalization_progress()
        if self._discard_restore_pending:
            if self._live_service is not None:
                self._live_service.discard_output()
            self._restore_after_discard()
            return
        self._live_failed_message = message
        if self._recording_service.is_recording:
            self.progress_widget.set_recording(self._t("recording_continues"), self._t("live_failed_recording_continues"))
            self._set_state(AppState.RECORDING)
            self._logger.error("Transcripción en vivo detenida: %s", message)
            return
        self.progress_widget.set_idle(self._t("status_recording_saved"), self._t("transcribe_full_wav"))
        self._recording_service.reset()
        self._set_state(AppState.ERROR)
        visible_message = self._runtime_message(message)
        QMessageBox.warning(
            self,
            self._t("live_transcription_title"),
            f"{visible_message}\n\n{self._t('original_recording_kept')}",
        )

    def _on_live_cancelled(self) -> None:
        self._reset_finalization_progress()
        if self._discard_restore_pending:
            self._restore_after_discard()

    def _start_finalization_progress(self, duration: float) -> None:
        self._finalization_duration = max(0.0, float(duration))
        self._finalization_confirmed = self._live_service.confirmed_until if self._live_service is not None else 0.0
        self._finalization_started_at = time.monotonic()
        self._finalization_stage = "processing"
        self._recalculate_finalization_eta(self._finalization_confirmed)
        self._update_finalization_progress()
        self._finalization_timer.start()

    def _recalculate_finalization_eta(self, confirmed: float) -> None:
        self._finalization_started_at = time.monotonic()
        pending = max(0.0, self._finalization_duration - confirmed)
        if self._live_speed_factor is None:
            self._finalization_eta_seconds = None
        else:
            self._finalization_eta_seconds = pending * self._live_speed_factor

    def _update_finalization_progress(self) -> None:
        if self._state != AppState.FINALIZING_RECORDING and self._finalization_duration <= 0:
            return
        if self._finalization_stage == "downloading":
            self.progress_widget.set_indeterminate(self._t("status_finalizing"), self._t("finalizing_download_model"))
            return
        if self._finalization_stage == "loading":
            self.progress_widget.set_indeterminate(self._t("status_finalizing"), self._t("finalizing_load_model"))
            return
        total = max(0.1, self._finalization_duration)
        confirmed = min(total, max(0.0, self._finalization_confirmed))
        value = min(99, int((confirmed / total) * 100))
        detail = self._t(
            "processed_of_total_calculating",
            processed=self._format_clock(confirmed),
            total=self._format_clock(total),
        )
        if self._finalization_eta_seconds is not None and self._finalization_started_at is not None:
            elapsed = max(0.0, time.monotonic() - self._finalization_started_at)
            remaining = max(0.0, self._finalization_eta_seconds - elapsed)
            detail = self._t(
                "processed_of_total_eta",
                processed=self._format_clock(confirmed),
                total=self._format_clock(total),
                remaining=self._format_remaining(remaining),
            )
        self.progress_widget.set_finalizing_progress(value, detail)

    def _reset_finalization_progress(self) -> None:
        self._finalization_timer.stop()
        self._finalization_duration = 0.0
        self._finalization_confirmed = 0.0
        self._finalization_started_at = None
        self._finalization_eta_seconds = None
        self._finalization_stage = "processing"

    def _restore_after_discard(self) -> None:
        self._discard_restore_pending = False
        self._live_failed_message = None
        self._live_service = None
        self._current_audio.restore(self._recording_previous_job)
        self._last_output_path = self._recording_previous_output_path
        job = self._current_audio.job
        if job is None:
            self.current_audio_widget.show_empty()
            self.progress_widget.set_idle(self._t("recording_discarded"), "")
            self._set_state(AppState.IDLE)
        else:
            self.current_audio_widget.show_audio(job.input_path, job.duration)
            if self._last_output_path and self._last_output_path.exists():
                self.current_audio_widget.set_state("completed")
                self.progress_widget.set_completed(self._t("recording_discarded"), self._t("previous_result_available"))
                self._set_state(AppState.COMPLETED)
            else:
                self.progress_widget.set_idle(self._t("recording_discarded"), self._t("status_ready"))
                self._set_state(AppState.AUDIO_SELECTED)
        self._recording_previous_job = None
        self._recording_previous_output_path = None
        self._save_settings()

    def _set_state(self, state: AppState) -> None:
        self._state = state
        self._apply_state()

    def _apply_state(self) -> None:
        stable = self._is_stable_state()
        has_audio = self._current_audio.job is not None
        self.input_widget.set_interactions_enabled(stable)
        self.settings_widget.set_interactions_enabled(stable)
        self.language_toggle_button.setEnabled(stable)
        self.transcribe_button.setEnabled(stable and has_audio)
        self.cancel_button.setEnabled(self._state == AppState.TRANSCRIBING_FILE and self._worker is not None)
        self.current_audio_widget.set_remove_available(stable and has_audio)
        self.open_file_button.setEnabled(bool(self._last_output_path and self._last_output_path.exists()))
        self.open_folder_button.setEnabled(bool(self.settings_widget.output_edit.text().strip()))

    def _is_stable_state(self) -> bool:
        return self._state in {
            AppState.IDLE,
            AppState.AUDIO_SELECTED,
            AppState.COMPLETED,
            AppState.CANCELLED,
            AppState.ERROR,
        }

    def _open_last_transcription(self) -> None:
        if self._last_output_path and self._last_output_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_output_path)))

    def _open_output_folder(self) -> None:
        output_dir = self._output_directory()
        if output_dir is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_dir)))

    def _open_github(self) -> None:
        QDesktopServices.openUrl(QUrl(GITHUB_URL))

    def _save_settings(self) -> None:
        try:
            installed = self._model_repository.installed_profiles()
        except Exception:
            installed = list(self._settings.get("installed_models", []))
        self._settings_repository.save(
            {
                "ui_language": self._ui_language,
                "language": self.settings_widget.selected_language(),
                "profile": self.settings_widget.selected_profile(),
                "output_dir": self.settings_widget.output_edit.text(),
                "installed_models": installed,
            }
        )

    def _format_remaining(self, seconds: float) -> str:
        seconds = max(0.0, float(seconds))
        if seconds < 60:
            rounded = max(5, int(math.ceil(seconds / 5.0) * 5))
            return f"{rounded} s"
        minutes = math.ceil(seconds / 60)
        if minutes < 60:
            return f"{minutes} min"
        hours, remaining_minutes = divmod(minutes, 60)
        if remaining_minutes == 0:
            return f"{hours} h"
        return f"{hours} h {remaining_minutes} min"

    def _format_clock(self, seconds: float) -> str:
        total = max(0, int(seconds))
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _dispose_file_worker(self, worker: TranscriptionWorker) -> None:
        if self._worker is worker:
            self._worker = None
        worker.deleteLater()
        self._apply_state()

    def _dispose_live_worker(self, worker: LiveTranscriptionWorker) -> None:
        if self._live_worker is worker:
            self._live_worker = None
        worker.deleteLater()

    def closeEvent(self, event) -> None:
        active = self._recording_service.is_recording or (self._worker and self._worker.isRunning()) or (self._live_worker and self._live_worker.isRunning())
        if active:
            message = self._t("close_recording_message") if self._recording_service.is_recording else self._t("close_process_message")
            answer = QMessageBox.question(
                self,
                self._t("close_app_title"),
                f"{message}\n\n{self._t('close_question')}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self._record_timer.stop()
        self._finalization_timer.stop()
        if self._recording_service.is_recording:
            try:
                self._recording_service.stop()
            except Exception:
                self._logger.exception("No se pudo cerrar la grabación limpiamente")
        if self._worker and self._worker.isRunning():
            self._worker.cancel_current()
            self._worker.wait(5000)
        if self._live_worker and self._live_worker.isRunning():
            self._live_worker.request_cancel(False)
            self._live_worker.wait(5000)
        self._save_settings()
        event.accept()
