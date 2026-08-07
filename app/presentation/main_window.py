from __future__ import annotations

import logging
import math
import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.application.queue_service import QueueService
from app.constants import APP_NAME, SUPPORTED_AUDIO_EXTENSIONS, WINDOW_HEIGHT, WINDOW_WIDTH
from app.domain.job_status import JobStatus
from app.infrastructure.audio.audio_recorder import AudioRecorder, AudioRecordingError
from app.infrastructure.persistence.settings_repository import SettingsRepository
from app.presentation.input_widget import AudioInputWidget
from app.presentation.settings_widget import SettingsWidget
from app.presentation.styles import APP_STYLE
from app.workers.transcription_worker import TranscriptionWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._settings_repository = SettingsRepository()
        self._settings = self._settings_repository.load()
        self._queue_service = QueueService()
        self._recorder = AudioRecorder()
        self._worker: TranscriptionWorker | None = None
        self._current_job_id: str | None = None
        self._transcription_started_at: float | None = None
        self._eta_seconds: float | None = None
        self._recording_started_at: float | None = None
        self._last_output_path: Path | None = None
        self._last_outcome = "idle"
        self._record_timer = QTimer(self)
        self._record_timer.setInterval(250)
        self._record_timer.timeout.connect(self._update_recording_time)
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self.input_widget.set_microphone_name(self._recorder.default_input_name())

    def _build_ui(self) -> None:
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(18, 15, 18, 14)
        root.setSpacing(10)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 2)
        brand_row.setSpacing(10)

        left_accents = self._accent_group(mirrored=True)
        right_accents = self._accent_group(mirrored=False)
        brand = QLabel(APP_NAME)
        brand.setObjectName("brandLabel")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_row.addWidget(left_accents)
        brand_row.addStretch(1)
        brand_row.addWidget(brand, 0, Qt.AlignmentFlag.AlignCenter)
        brand_row.addStretch(1)
        brand_row.addWidget(right_accents)
        root.addLayout(brand_row)

        self.input_widget = AudioInputWidget()
        self.input_widget.files_selected.connect(self._add_files)
        self.input_widget.browse_requested.connect(self._browse_files)
        self.input_widget.record_requested.connect(self._start_recording)
        self.input_widget.stop_record_requested.connect(self._stop_recording)
        root.addWidget(self.input_widget)

        self.file_card = QFrame()
        self.file_card.setObjectName("fileCard")
        self.file_card.setFixedHeight(56)
        file_layout = QHBoxLayout(self.file_card)
        file_layout.setContentsMargins(11, 8, 11, 8)
        file_layout.setSpacing(8)
        self.file_dot = QLabel("●")
        self.file_dot.setObjectName("fileDot")
        self.file_dot.setProperty("state", "idle")
        self.file_dot.setFixedWidth(10)
        file_text = QVBoxLayout()
        file_text.setContentsMargins(0, 0, 0, 0)
        file_text.setSpacing(1)
        self.file_name_label = QLabel("Ningún audio seleccionado")
        self.file_name_label.setObjectName("fileNameLabel")
        self.file_name_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.file_meta_label = QLabel("Selecciona, arrastra o graba un audio")
        self.file_meta_label.setObjectName("fileMetaLabel")
        file_text.addWidget(self.file_name_label)
        file_text.addWidget(self.file_meta_label)
        file_layout.addWidget(self.file_dot)
        file_layout.addLayout(file_text, 1)
        root.addWidget(self.file_card)

        self.settings_widget = SettingsWidget(
            self._settings["language"],
            self._settings["profile"],
            self._settings["output_dir"],
        )
        self.settings_widget.settings_changed.connect(self._update_pending_settings)
        self.settings_widget.preferences_changed.connect(self._save_settings)
        root.addWidget(self.settings_widget)

        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(0, 2, 0, 0)
        progress_layout.setSpacing(5)
        progress_header = QHBoxLayout()
        progress_header.setContentsMargins(0, 0, 0, 0)
        self.progress_status_label = QLabel("Listo")
        self.progress_status_label.setObjectName("progressStatusLabel")
        self.progress_status_label.setProperty("state", "idle")
        self.eta_label = QLabel("")
        self.eta_label.setObjectName("etaLabel")
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        progress_header.addWidget(self.progress_status_label, 1)
        progress_header.addWidget(self.eta_label)
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        progress_layout.addLayout(progress_header)
        progress_layout.addWidget(self.overall_progress)
        root.addWidget(progress_frame)

        actions = QHBoxLayout()
        actions.setSpacing(7)
        self.transcribe_button = QPushButton("TRANSCRIBIR")
        self.transcribe_button.setObjectName("primaryButton")
        self.transcribe_button.setEnabled(False)
        self.transcribe_button.clicked.connect(self._start_transcription)
        self.cancel_button = QPushButton("CANCELAR")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel_current)
        actions.addWidget(self.transcribe_button, 1)
        actions.addWidget(self.cancel_button)
        root.addLayout(actions)

        result_layout = QHBoxLayout()
        result_layout.setSpacing(7)
        self.open_file_button = QPushButton("ABRIR TRANSCRIPCIÓN")
        self.open_file_button.setObjectName("openFileButton")
        self.open_file_button.setEnabled(False)
        self.open_file_button.clicked.connect(self._open_last_transcription)
        self.open_folder_button = QPushButton("ABRIR CARPETA")
        self.open_folder_button.setObjectName("openFolderButton")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self._open_last_folder)
        result_layout.addWidget(self.open_file_button, 1)
        result_layout.addWidget(self.open_folder_button, 1)
        root.addLayout(result_layout)

        footer_divider = QFrame()
        footer_divider.setObjectName("footerDivider")
        footer_divider.setFixedHeight(8)
        root.addWidget(footer_divider)

        footer = QLabel("Copyright © 2026 · Renzo Fernando Mosquera Daza")
        footer.setObjectName("footerLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

        self.setCentralWidget(container)

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

    def _browse_files(self) -> None:
        patterns = " ".join(f"*{extension}" for extension in sorted(SUPPORTED_AUDIO_EXTENSIONS))
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar audio", "", f"Archivos de audio ({patterns});;Todos los archivos (*.*)")
        if path:
            self._add_files([path])

    def _add_files(self, paths: list[str]) -> None:
        added, rejected = self._queue_service.add_files(
            paths,
            self.settings_widget.language_combo.currentText(),
            self.settings_widget.profile_combo.currentText(),
        )
        if added:
            job = added[0]
            self.file_name_label.setText(job.input_path.name)
            self.file_name_label.setToolTip(str(job.input_path))
            self.file_meta_label.setText(self._file_meta(job.duration))
            self._set_file_state("selected")
            self._set_progress_state("idle")
            self.progress_status_label.setText("Listo para transcribir")
            self.eta_label.setText("")
            self.overall_progress.setRange(0, 100)
            self.overall_progress.setValue(0)
            self.transcribe_button.setEnabled(True)
            self._last_output_path = None
            self._last_outcome = "idle"
            self._set_result_actions_enabled(False)
        if rejected and not added:
            QMessageBox.warning(self, "Archivo no compatible", "El archivo seleccionado no es un audio compatible con AudiTo.")

    def _file_meta(self, duration: float | None) -> str:
        if duration is None:
            return "Duración no disponible"
        total = max(0, int(duration))
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _update_pending_settings(self, language: str, profile: str) -> None:
        self._queue_service.update_pending_settings(language, profile)

    def _output_directory(self) -> Path | None:
        output_text = self.settings_widget.output_edit.text().strip()
        if not output_text:
            QMessageBox.warning(self, "Carpeta de salida", "Selecciona una carpeta donde guardar los archivos.")
            return None
        output_dir = Path(output_text).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            test_path = output_dir / ".audito_write_test"
            test_path.write_text("ok", encoding="utf-8")
            test_path.unlink(missing_ok=True)
        except Exception:
            QMessageBox.warning(self, "Carpeta de salida", "No se puede escribir en la carpeta seleccionada.")
            return None
        return output_dir

    def _start_recording(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        output_dir = self._output_directory()
        if output_dir is None:
            return
        try:
            path = self._recorder.start(output_dir)
        except AudioRecordingError as exc:
            QMessageBox.warning(self, "No se pudo grabar", str(exc))
            return
        self._last_output_path = None
        self._set_result_actions_enabled(False)
        self.file_name_label.setText(path.name)
        self.file_name_label.setToolTip(str(path))
        self.file_meta_label.setText("Grabando · guardado automático")
        self._set_file_state("selected")
        self.input_widget.set_recording(True)
        self.settings_widget.set_interactions_enabled(False)
        self.transcribe_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self._recording_started_at = time.monotonic()
        self.input_widget.set_recording_time(0)
        self._record_timer.start()
        self.overall_progress.setRange(0, 0)
        self.progress_status_label.setText("Grabando audio")
        self.eta_label.setText("Guardado automático")
        self._set_progress_state("idle")

    def _stop_recording(self) -> None:
        if not self._recorder.is_recording:
            return
        self._record_timer.stop()
        try:
            result = self._recorder.stop()
        except AudioRecordingError as exc:
            self.input_widget.set_recording(False)
            self.settings_widget.set_interactions_enabled(True)
            self.overall_progress.setRange(0, 100)
            self.overall_progress.setValue(0)
            self.progress_status_label.setText("Grabación incompleta")
            self.eta_label.setText("")
            QMessageBox.warning(self, "Error de grabación", str(exc))
            return
        self._recording_started_at = None
        self.input_widget.set_recording(False)
        self.settings_widget.set_interactions_enabled(True)
        self._add_files([str(result.path)])
        jobs = self._queue_service.jobs
        if jobs:
            jobs[0].duration = result.duration
            self.file_meta_label.setText(f"Grabación · {self._file_meta(result.duration)}")
        self._set_file_state("recorded")
        self.progress_status_label.setText("Grabación guardada")
        self.eta_label.setText(self._file_meta(result.duration))
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)

    def _update_recording_time(self) -> None:
        if self._recording_started_at is None:
            return
        elapsed = int(time.monotonic() - self._recording_started_at)
        self.input_widget.set_recording_time(elapsed)

    def _start_transcription(self) -> None:
        if self._recorder.is_recording:
            return
        jobs = self._queue_service.pending_jobs()
        if not jobs and self._queue_service.jobs:
            job = self._queue_service.jobs[0]
            if job.status != JobStatus.PROCESSING:
                job.status = JobStatus.PENDING
                job.progress = 0
                job.error = None
                jobs = [job]
        if not jobs:
            QMessageBox.information(self, "Sin audio", "Selecciona o graba un audio antes de transcribir.")
            return
        output_dir = self._output_directory()
        if output_dir is None:
            return
        self._update_pending_settings(
            self.settings_widget.language_combo.currentText(),
            self.settings_widget.profile_combo.currentText(),
        )
        self._set_processing_state(True)
        self._last_outcome = "processing"
        self._transcription_started_at = None
        self._eta_seconds = None
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        self.progress_status_label.setText("Preparando audio")
        self.eta_label.setText("")
        self._set_progress_state("idle")
        self._worker = TranscriptionWorker(jobs, output_dir, self)
        self._worker.job_started.connect(self._on_job_started)
        self._worker.job_progress.connect(self._on_job_progress)
        self._worker.job_status.connect(self._on_job_status)
        self._worker.job_completed.connect(self._on_job_completed)
        self._worker.job_failed.connect(self._on_job_failed)
        self._worker.job_cancelled.connect(self._on_job_cancelled)
        self._worker.queue_finished.connect(self._on_queue_finished)
        self._worker.start()

    def _cancel_current(self) -> None:
        if self._worker and self._worker.isRunning() and self._current_job_id:
            self.progress_status_label.setText("Cancelando…")
            self.eta_label.setText("")
            self.cancel_button.setEnabled(False)
            self._worker.cancel_current()

    def _on_job_started(self, job_id: str) -> None:
        self._current_job_id = job_id
        self.progress_status_label.setText("Preparando audio")
        self.cancel_button.setEnabled(True)

    def _on_job_status(self, job_id: str, status: str) -> None:
        if status == "Descargando modelo por primera vez":
            self.overall_progress.setRange(0, 0)
            self.progress_status_label.setText("Descargando modelo")
            self.eta_label.setText("Solo la primera vez")
            return
        if status == "Cargando modelo":
            self.overall_progress.setRange(0, 0)
            self.progress_status_label.setText("Cargando modelo")
            self.eta_label.setText("Preparando modelo")
            return
        if status == "Transcribiendo":
            self.overall_progress.setRange(0, 100)
            self.overall_progress.setValue(0)
            self._transcription_started_at = time.monotonic()
            self._eta_seconds = None
            self.progress_status_label.setText("Transcribiendo · 0 %")
            self.eta_label.setText("Tiempo restante: calculando…")
            return
        if status == "Guardando":
            self.overall_progress.setRange(0, 100)
            self.progress_status_label.setText("Guardando…")
            self.eta_label.setText("")
            return
        self.progress_status_label.setText(status)

    def _on_job_progress(self, job_id: str, value: int) -> None:
        value = max(0, min(100, int(value)))
        if self.overall_progress.minimum() == 0 and self.overall_progress.maximum() == 0:
            self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(value)
        self.progress_status_label.setText(f"Transcribiendo · {value} %")
        if value >= 2 and value < 100 and self._transcription_started_at is not None:
            elapsed = max(0.1, time.monotonic() - self._transcription_started_at)
            raw_eta = elapsed * (100 - value) / value
            if self._eta_seconds is None:
                self._eta_seconds = raw_eta
            else:
                self._eta_seconds = self._eta_seconds * 0.72 + raw_eta * 0.28
            self.eta_label.setText(f"Tiempo restante: ≈ {self._format_remaining(self._eta_seconds)}")
        elif value >= 100:
            self.eta_label.setText("")
        else:
            self.eta_label.setText("Tiempo restante: calculando…")

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

    def _on_job_completed(self, job_id: str, output_path: str) -> None:
        self._last_outcome = "completed"
        self._last_output_path = Path(output_path)
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(100)
        self.progress_status_label.setText("Completado · 100 %")
        self.eta_label.setText("Finalizado")
        self._set_progress_state("completed")
        self._set_file_state("completed")
        self.cancel_button.setEnabled(False)
        self._set_result_actions_enabled(True)

    def _on_job_failed(self, job_id: str, message: str) -> None:
        self._last_outcome = "failed"
        self.overall_progress.setRange(0, 100)
        self.progress_status_label.setText("No se pudo transcribir")
        self.eta_label.setText("")
        self._set_progress_state("idle")
        self.cancel_button.setEnabled(False)
        QMessageBox.warning(self, "No se pudo transcribir", message)

    def _on_job_cancelled(self, job_id: str) -> None:
        self._last_outcome = "cancelled"
        self.overall_progress.setRange(0, 100)
        self.progress_status_label.setText("Cancelado")
        self.eta_label.setText("Parcial conservado")
        self._set_progress_state("idle")
        self.cancel_button.setEnabled(False)

    def _on_queue_finished(self) -> None:
        self._current_job_id = None
        self._set_processing_state(False)
        self._save_settings()
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def _set_processing_state(self, processing: bool) -> None:
        self.input_widget.set_interactions_enabled(not processing)
        self.settings_widget.set_interactions_enabled(not processing)
        self.transcribe_button.setEnabled(not processing and bool(self._queue_service.jobs))
        self.cancel_button.setEnabled(processing)

    def _set_result_actions_enabled(self, enabled: bool) -> None:
        self.open_file_button.setEnabled(enabled)
        self.open_folder_button.setEnabled(enabled)

    def _set_file_state(self, state: str) -> None:
        self.file_dot.setProperty("state", state)
        self.file_dot.style().unpolish(self.file_dot)
        self.file_dot.style().polish(self.file_dot)

    def _set_progress_state(self, state: str) -> None:
        self.progress_status_label.setProperty("state", state)
        self.progress_status_label.style().unpolish(self.progress_status_label)
        self.progress_status_label.style().polish(self.progress_status_label)

    def _open_last_transcription(self) -> None:
        if self._last_output_path and self._last_output_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_output_path)))

    def _open_last_folder(self) -> None:
        if self._last_output_path:
            folder = self._last_output_path.parent
            if folder.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _save_settings(self) -> None:
        self._settings_repository.save(
            {
                "language": self.settings_widget.language_combo.currentText(),
                "profile": self.settings_widget.profile_combo.currentText(),
                "output_dir": self.settings_widget.output_edit.text(),
            }
        )

    def closeEvent(self, event) -> None:
        if self._recorder.is_recording:
            self._record_timer.stop()
            try:
                self._recorder.stop()
            except AudioRecordingError:
                pass
        if self._worker and self._worker.isRunning():
            answer = QMessageBox.question(
                self,
                "Transcripción en curso",
                "Hay una transcripción en curso. ¿Quieres cerrar AudiTo? El archivo actual se cancelará.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._worker.cancel_current()
            self._worker.wait(5000)
        self._save_settings()
        event.accept()
