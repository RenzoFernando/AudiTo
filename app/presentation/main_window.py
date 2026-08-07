from __future__ import annotations

import logging
import math
import time
from pathlib import Path

from PySide6.QtCore import Qt
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
from app.constants import APP_NAME, SUPPORTED_AUDIO_EXTENSIONS
from app.domain.job_status import JobStatus
from app.infrastructure.persistence.settings_repository import SettingsRepository
from app.presentation.drop_zone import DropZone
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
        self._worker: TranscriptionWorker | None = None
        self._current_job_id: str | None = None
        self._transcription_started_at: float | None = None
        self._eta_seconds: float | None = None
        self._last_outcome = "idle"
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(430, 500)
        self.resize(int(self._settings["window_width"]), int(self._settings["window_height"]))
        self.setStyleSheet(APP_STYLE)
        self._build_ui()

    def _build_ui(self) -> None:
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(20, 17, 20, 13)
        root.setSpacing(9)

        brand = QLabel(APP_NAME)
        brand.setObjectName("brandLabel")
        root.addWidget(brand)

        self.drop_zone = DropZone()
        self.drop_zone.files_selected.connect(self._add_files)
        self.drop_zone.browse_requested.connect(self._browse_files)
        root.addWidget(self.drop_zone)

        self.file_card = QFrame()
        self.file_card.setObjectName("fileCard")
        self.file_card.setFixedHeight(56)
        file_layout = QHBoxLayout(self.file_card)
        file_layout.setContentsMargins(12, 8, 12, 8)
        file_layout.setSpacing(9)
        file_dot = QLabel("●")
        file_dot.setStyleSheet("color: #cf4747; font-size: 10px;")
        file_dot.setFixedWidth(10)
        file_text = QVBoxLayout()
        file_text.setContentsMargins(0, 0, 0, 0)
        file_text.setSpacing(1)
        self.file_name_label = QLabel("Ningún audio seleccionado")
        self.file_name_label.setObjectName("fileNameLabel")
        self.file_name_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.file_meta_label = QLabel("Selecciona o arrastra un archivo")
        self.file_meta_label.setObjectName("fileMetaLabel")
        file_text.addWidget(self.file_name_label)
        file_text.addWidget(self.file_meta_label)
        file_layout.addWidget(file_dot)
        file_layout.addLayout(file_text, 1)
        root.addWidget(self.file_card)

        self.settings_widget = SettingsWidget(
            self._settings["language"],
            self._settings["profile"],
            self._settings["output_dir"],
        )
        self.settings_widget.settings_changed.connect(self._update_pending_settings)
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
        actions.setSpacing(8)
        self.transcribe_button = QPushButton("TRANSCRIBIR")
        self.transcribe_button.setObjectName("primaryButton")
        self.transcribe_button.setEnabled(False)
        self.transcribe_button.clicked.connect(self._start_transcription)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self._cancel_current)
        actions.addWidget(self.transcribe_button, 1)
        actions.addWidget(self.cancel_button)
        root.addLayout(actions)

        root.addStretch(1)

        footer = QFrame()
        footer.setObjectName("footerFrame")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.addStretch(1)
        local_label = QLabel("●  Local")
        local_label.setObjectName("localLabel")
        footer_layout.addWidget(local_label)
        root.addWidget(footer)

        self.setCentralWidget(container)

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
            self.file_meta_label.setText(self._file_meta(job.duration))
            self.progress_status_label.setText("Listo para transcribir")
            self.eta_label.setText("")
            self.overall_progress.setRange(0, 100)
            self.overall_progress.setValue(0)
            self.transcribe_button.setEnabled(True)
            self._last_outcome = "idle"
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

    def _start_transcription(self) -> None:
        jobs = self._queue_service.pending_jobs()
        if not jobs and self._queue_service.jobs:
            job = self._queue_service.jobs[0]
            if job.status != JobStatus.PROCESSING:
                job.status = JobStatus.PENDING
                job.progress = 0
                job.error = None
                jobs = [job]
        if not jobs:
            QMessageBox.information(self, "Sin audio", "Selecciona un archivo de audio antes de transcribir.")
            return
        output_text = self.settings_widget.output_edit.text().strip()
        if not output_text:
            QMessageBox.warning(self, "Carpeta de salida", "Selecciona una carpeta donde guardar la transcripción.")
            return
        output_dir = Path(output_text).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            test_path = output_dir / ".audito_write_test"
            test_path.write_text("ok", encoding="utf-8")
            test_path.unlink(missing_ok=True)
        except Exception:
            QMessageBox.warning(self, "Carpeta de salida", "No se puede escribir en la carpeta seleccionada.")
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
            self.eta_label.setText("Un momento…")
            return
        if status == "Transcribiendo":
            self.overall_progress.setRange(0, 100)
            self.overall_progress.setValue(0)
            self._transcription_started_at = time.monotonic()
            self._eta_seconds = None
            self.progress_status_label.setText("Transcribiendo · 0 %")
            self.eta_label.setText("Calculando tiempo…")
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
            self.eta_label.setText(f"≈ {self._format_remaining(self._eta_seconds)} restantes")
        elif value >= 100:
            self.eta_label.setText("")
        else:
            self.eta_label.setText("Calculando tiempo…")

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
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(100)
        self.progress_status_label.setText("Completado · 100 %")
        self.eta_label.setText(Path(output_path).name)
        self.cancel_button.setEnabled(False)

    def _on_job_failed(self, job_id: str, message: str) -> None:
        self._last_outcome = "failed"
        self.overall_progress.setRange(0, 100)
        self.progress_status_label.setText("No se pudo transcribir")
        self.eta_label.setText("")
        self.cancel_button.setEnabled(False)
        QMessageBox.warning(self, "No se pudo transcribir", message)

    def _on_job_cancelled(self, job_id: str) -> None:
        self._last_outcome = "cancelled"
        self.overall_progress.setRange(0, 100)
        self.progress_status_label.setText("Cancelado")
        self.eta_label.setText("Parcial conservado")
        self.cancel_button.setEnabled(False)

    def _on_queue_finished(self) -> None:
        self._current_job_id = None
        self._set_processing_state(False)
        self._save_settings()
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def _set_processing_state(self, processing: bool) -> None:
        self.drop_zone.set_interactions_enabled(not processing)
        self.settings_widget.set_interactions_enabled(not processing)
        self.transcribe_button.setVisible(not processing)
        self.cancel_button.setVisible(processing)
        if processing:
            self.cancel_button.setEnabled(True)
        else:
            self.cancel_button.setEnabled(False)
            self.transcribe_button.setEnabled(bool(self._queue_service.jobs))

    def _save_settings(self) -> None:
        self._settings_repository.save(
            {
                "language": self.settings_widget.language_combo.currentText(),
                "profile": self.settings_widget.profile_combo.currentText(),
                "output_dir": self.settings_widget.output_edit.text(),
                "window_width": self.width(),
                "window_height": self.height(),
            }
        )

    def closeEvent(self, event) -> None:
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
