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
from app.constants import APP_NAME, LANGUAGES, SUPPORTED_AUDIO_EXTENSIONS, WINDOW_HEIGHT, WINDOW_WIDTH
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
from app.workers.live_transcription_worker import LiveTranscriptionWorker
from app.workers.transcription_worker import TranscriptionWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._settings_repository = SettingsRepository()
        self._settings = self._settings_repository.load()
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
        self._discard_restore_pending = False
        self._recording_error_handled = False
        self._record_timer = QTimer(self)
        self._record_timer.setInterval(250)
        self._record_timer.timeout.connect(self._update_recording_time)
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self.input_widget.set_microphone_name(self._recording_service.default_input_name())
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
        brand_row.addStretch(1)
        brand = QLabel(APP_NAME)
        brand.setObjectName("brandLabel")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_row.addWidget(brand, 0, Qt.AlignmentFlag.AlignCenter)
        brand_row.addStretch(1)
        brand_row.addWidget(self._accent_group(False))
        root.addLayout(brand_row)
        self.input_widget = AudioInputWidget()
        self.input_widget.files_selected.connect(self._select_audio)
        self.input_widget.browse_requested.connect(self._browse_audio)
        self.input_widget.record_requested.connect(self._start_recording)
        self.input_widget.stop_record_requested.connect(self._stop_recording)
        self.input_widget.discard_record_requested.connect(self._discard_recording)
        root.addWidget(self.input_widget)
        self.current_audio_widget = CurrentAudioWidget()
        self.current_audio_widget.remove_requested.connect(self._clear_audio)
        root.addWidget(self.current_audio_widget)
        self.settings_widget = SettingsWidget(
            self._settings["language"],
            self._settings["profile"],
            self._settings["output_dir"],
        )
        self.settings_widget.settings_changed.connect(self._update_selected_settings)
        self.settings_widget.preferences_changed.connect(self._preferences_changed)
        root.addWidget(self.settings_widget)
        self.progress_widget = ProgressWidget()
        root.addWidget(self.progress_widget)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.transcribe_button = QPushButton("TRANSCRIBIR")
        self.transcribe_button.setObjectName("primaryButton")
        self.transcribe_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transcribe_button.clicked.connect(self._start_transcription)
        self.cancel_button = QPushButton("CANCELAR")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cancel_button.clicked.connect(self._cancel_current)
        actions.addWidget(self.transcribe_button, 1)
        actions.addWidget(self.cancel_button)
        root.addLayout(actions)
        result_layout = QHBoxLayout()
        result_layout.setSpacing(8)
        self.open_file_button = QPushButton("ABRIR TRANSCRIPCIÓN")
        self.open_file_button.setObjectName("openFileButton")
        self.open_file_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.open_file_button.clicked.connect(self._open_last_transcription)
        self.open_folder_button = QPushButton("ABRIR CARPETA")
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
        footer_label = QLabel("Copyright © 2026 · Renzo Fernando Mosquera Daza")
        footer_label.setObjectName("footerLabel")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(footer_label)
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

    def _browse_audio(self) -> None:
        if not self._is_stable_state():
            return
        patterns = " ".join(f"*{extension}" for extension in sorted(SUPPORTED_AUDIO_EXTENSIONS))
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar audio", "", f"Archivos de audio ({patterns});;Todos los archivos (*.*)")
        if path:
            self._select_audio([path])

    def _select_audio(self, paths: list[str]) -> None:
        if not self._is_stable_state():
            return
        job, rejected, ignored_count = self._current_audio.select(
            paths,
            self.settings_widget.language_combo.currentText(),
            self.settings_widget.profile_combo.currentText(),
        )
        if job is None:
            if rejected:
                QMessageBox.warning(self, "Archivo no compatible", "No se pudo abrir este archivo de audio.")
            return
        self._last_output_path = None
        self.current_audio_widget.show_audio(job.input_path, job.duration)
        self.progress_widget.set_idle("Listo para transcribir", "")
        if ignored_count:
            self.progress_widget.set_idle("Un audio seleccionado", "AudiTo procesa un archivo a la vez")
        self._set_state(AppState.AUDIO_SELECTED)

    def _clear_audio(self) -> None:
        if not self._is_stable_state():
            return
        self._current_audio.clear()
        self._last_output_path = None
        self.current_audio_widget.show_empty()
        self.progress_widget.set_idle()
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
                QMessageBox.warning(self, "Carpeta de salida", "Selecciona una carpeta donde guardar los archivos.")
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
                message = "No hay espacio suficiente para guardar los archivos." if getattr(exc, "errno", None) == 28 else "No se puede escribir en la carpeta seleccionada."
                QMessageBox.warning(self, "Carpeta de salida", message)
            return None
        except Exception:
            if show_errors:
                QMessageBox.warning(self, "Carpeta de salida", "No se puede escribir en la carpeta seleccionada.")
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
        self._discard_restore_pending = False
        self._recording_error_handled = False
        try:
            session = self._recording_service.start(output_dir)
        except AudioRecordingError as exc:
            QMessageBox.warning(self, "No se pudo grabar", str(exc))
            return
        buffer = self._recording_service.buffer
        if buffer is None:
            self._recording_service.discard()
            QMessageBox.warning(self, "No se pudo grabar", "No se pudo preparar el búfer de audio para la grabación.")
            return
        language_label = self.settings_widget.language_combo.currentText()
        profile_label = self.settings_widget.profile_combo.currentText()
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
        self.progress_widget.set_recording("Preparando transcripción...", "AudiTo empezará cerca de 00:30")
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
                    self.settings_widget.language_combo.currentText(),
                    self.settings_widget.profile_combo.currentText(),
                )
                self.current_audio_widget.show_audio(job.input_path, job.duration, "Grabación · ")
            if self._live_worker and self._live_worker.isRunning():
                self._live_worker.request_cancel(False)
            self.progress_widget.set_idle("Grabación detenida", "El audio guardado se conserva")
            self._recording_service.reset()
            self._set_state(AppState.ERROR)
            QMessageBox.warning(self, "Error de grabación", str(exc))
            return
        self._recording_started_at = None
        self.input_widget.set_recording(False)
        job = self._current_audio.set_recording(
            session.path,
            session.duration,
            self.settings_widget.language_combo.currentText(),
            self.settings_widget.profile_combo.currentText(),
        )
        self.current_audio_widget.show_audio(job.input_path, job.duration, "Grabación · ")
        self.current_audio_widget.set_state("recorded")
        if self._live_failed_message:
            self.progress_widget.set_idle("Grabación guardada", "Transcripción en vivo detenida · pulsa TRANSCRIBIR")
            self._recording_service.reset()
            self._set_state(AppState.ERROR)
            return
        if self._live_worker and self._live_worker.isRunning():
            self.progress_widget.set_indeterminate("Finalizando transcripción...", "Procesando los últimos segundos")
            self._set_state(AppState.FINALIZING_RECORDING)
            self._live_worker.request_finalize(session.duration)
        else:
            self.progress_widget.set_idle("Grabación guardada", "Pulsa TRANSCRIBIR para generar el TXT")
            self._recording_service.reset()
            self._set_state(AppState.AUDIO_SELECTED)

    def _discard_recording(self) -> None:
        if not self._recording_service.is_recording:
            return
        answer = QMessageBox.question(
            self,
            "Descartar grabación",
            "¿Quieres descartar esta grabación? El WAV actual será eliminado.",
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
        self.progress_widget.set_indeterminate("Descartando grabación...", "")
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
            QMessageBox.information(self, "Sin audio", "Selecciona o graba un audio antes de transcribir.")
            return
        output_dir = self._output_directory()
        if output_dir is None:
            return
        self._current_audio.update_settings(
            self.settings_widget.language_combo.currentText(),
            self.settings_widget.profile_combo.currentText(),
        )
        job.status = JobStatus.PENDING
        job.progress = 0
        job.error = None
        self._last_output_path = None
        self._transcription_started_at = None
        self._eta_seconds = None
        self.progress_widget.set_file_progress(0, "Tiempo restante: calculando…")
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
            self.progress_widget.set_indeterminate("Cancelando…", "El parcial se conservará")
            self.cancel_button.setEnabled(False)
            self._worker.cancel_current()

    def _on_job_started(self, job_id: str) -> None:
        self._current_job_id = job_id
        self.progress_widget.set_indeterminate("Preparando audio", "")
        self._apply_state()

    def _on_job_status(self, job_id: str, status: str) -> None:
        if status == "Descargando modelo por primera vez":
            self.progress_widget.set_indeterminate("Descargando modelo", "Solo la primera vez")
            return
        if status == "Cargando modelo":
            self.progress_widget.set_indeterminate("Cargando modelo", "Preparando transcripción")
            return
        if status == "Transcribiendo":
            self._transcription_started_at = time.monotonic()
            self._eta_seconds = None
            self.progress_widget.set_file_progress(0, "Tiempo restante: calculando…")
            return
        if status == "Guardando":
            self.progress_widget.set_indeterminate("Guardando…", "")
            return
        self.progress_widget.set_indeterminate(status, "")

    def _on_job_progress(self, job_id: str, value: int) -> None:
        value = max(0, min(100, int(value)))
        detail = "Tiempo restante: calculando…"
        if value >= 2 and value < 100 and self._transcription_started_at is not None:
            elapsed = max(0.1, time.monotonic() - self._transcription_started_at)
            raw_eta = elapsed * (100 - value) / value
            if self._eta_seconds is None:
                self._eta_seconds = raw_eta
            else:
                self._eta_seconds = self._eta_seconds * 0.72 + raw_eta * 0.28
            detail = f"Tiempo restante: ≈ {self._format_remaining(self._eta_seconds)}"
        elif value >= 100:
            detail = ""
        self.progress_widget.set_file_progress(value, detail)

    def _on_job_completed(self, job_id: str, output_path: str) -> None:
        self._last_output_path = Path(output_path)
        self.current_audio_widget.set_state("completed")
        self.progress_widget.set_completed("Completado · 100 %", "Finalizado")
        self._set_state(AppState.COMPLETED)

    def _on_job_failed(self, job_id: str, message: str) -> None:
        self.progress_widget.set_idle("No se pudo transcribir", "Parcial conservado")
        self._set_state(AppState.ERROR)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("No se pudo transcribir")
        box.setText(message)
        if "Conéctate a internet" in message:
            box.setStandardButtons(QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close)
            if box.exec() == QMessageBox.StandardButton.Retry:
                QTimer.singleShot(0, self._start_transcription)
        else:
            box.setStandardButtons(QMessageBox.StandardButton.Close)
            box.exec()

    def _on_job_cancelled(self, job_id: str) -> None:
        self.progress_widget.set_idle("Cancelado", "Parcial conservado")
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
                self.progress_widget.set_indeterminate("Finalizando transcripción...", "Descargando modelo")
            elif status == "Cargando modelo":
                self.progress_widget.set_indeterminate("Finalizando transcripción...", "Cargando modelo")
            return
        if not self._recording_service.is_recording:
            return
        if status == "Descargando modelo por primera vez":
            self.progress_widget.set_recording("● Grabando", "Descargando modelo de transcripción")
            return
        if status == "Cargando modelo":
            self.progress_widget.set_recording("● Grabando", "Cargando modelo de transcripción")
            return
        if status == "Transcribiendo":
            self.progress_widget.set_recording("Transcribiendo en segundo plano", "Procesando audio reciente...")
            self._set_state(AppState.RECORDING_TRANSCRIBING)
            return
        if status == "GPU no disponible. Usando CPU":
            self.progress_widget.set_recording("● Grabando", "GPU no disponible · usando CPU")

    def _on_live_confirmed(self, seconds: float) -> None:
        if self._discard_restore_pending:
            return
        detail = f"Texto procesado hasta · {self._format_clock(seconds)}"
        if self._state == AppState.FINALIZING_RECORDING:
            self.progress_widget.set_indeterminate("Finalizando transcripción...", detail)
            return
        if self._recording_service.is_recording:
            self.progress_widget.set_recording("Transcribiendo en segundo plano", detail)
            self._set_state(AppState.RECORDING_TRANSCRIBING)

    def _on_live_completed(self, output_path: str) -> None:
        if self._discard_restore_pending:
            return
        self._last_output_path = Path(output_path)
        self.current_audio_widget.set_state("completed")
        self.progress_widget.set_completed("Completado", "TXT listo")
        self._recording_service.reset()
        self._live_service = None
        self._set_state(AppState.COMPLETED)
        self._save_settings()

    def _on_live_failed(self, message: str) -> None:
        if self._discard_restore_pending:
            if self._live_service is not None:
                self._live_service.discard_output()
            self._restore_after_discard()
            return
        self._live_failed_message = message
        if self._recording_service.is_recording:
            self.progress_widget.set_recording("La grabación continúa", "La transcripción en vivo se detuvo por un error")
            self._set_state(AppState.RECORDING)
            self._logger.error("Transcripción en vivo detenida: %s", message)
            return
        self.progress_widget.set_idle("Grabación guardada", "Puedes transcribir el WAV completo")
        self._recording_service.reset()
        self._set_state(AppState.ERROR)
        QMessageBox.warning(self, "Transcripción en vivo", f"{message}\n\nLa grabación original se conservó.")

    def _on_live_cancelled(self) -> None:
        if self._discard_restore_pending:
            self._restore_after_discard()

    def _restore_after_discard(self) -> None:
        self._discard_restore_pending = False
        self._live_failed_message = None
        self._live_service = None
        self._current_audio.restore(self._recording_previous_job)
        self._last_output_path = self._recording_previous_output_path
        job = self._current_audio.job
        if job is None:
            self.current_audio_widget.show_empty()
            self.progress_widget.set_idle("Grabación descartada", "")
            self._set_state(AppState.IDLE)
        else:
            self.current_audio_widget.show_audio(job.input_path, job.duration)
            if self._last_output_path and self._last_output_path.exists():
                self.current_audio_widget.set_state("completed")
                self.progress_widget.set_completed("Grabación descartada", "Resultado anterior disponible")
                self._set_state(AppState.COMPLETED)
            else:
                self.progress_widget.set_idle("Grabación descartada", "Listo para transcribir")
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

    def _save_settings(self) -> None:
        try:
            installed = self._model_repository.installed_profiles()
        except Exception:
            installed = list(self._settings.get("installed_models", []))
        self._settings_repository.save(
            {
                "language": self.settings_widget.language_combo.currentText(),
                "profile": self.settings_widget.profile_combo.currentText(),
                "output_dir": self.settings_widget.output_edit.text(),
                "installed_models": installed,
            }
        )

    def _format_remaining(self, seconds: float) -> str:
        seconds = max(0, int(seconds))
        if seconds < 60:
            return "< 1 min"
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
            message = "Hay una grabación en curso. AudiTo la detendrá y conservará el audio antes de cerrar." if self._recording_service.is_recording else "Hay un proceso en curso. El TXT parcial se conservará si cierras ahora."
            answer = QMessageBox.question(
                self,
                "Cerrar AudiTo",
                f"{message}\n\n¿Quieres cerrar AudiTo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self._record_timer.stop()
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
