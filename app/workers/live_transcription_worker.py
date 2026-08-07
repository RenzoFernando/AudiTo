from __future__ import annotations

import threading
import time

from PySide6.QtCore import QThread, Signal

from app.application.live_transcription_service import LiveTranscriptionService


class LiveTranscriptionWorker(QThread):
    live_status = Signal(str)
    live_confirmed = Signal(float)
    live_metrics = Signal(float, float)
    live_completed = Signal(str)
    live_failed = Signal(str)
    live_cancelled = Signal()

    def __init__(self, service: LiveTranscriptionService, parent=None) -> None:
        super().__init__(parent)
        self._service = service
        self._finalize_event = threading.Event()
        self._cancel_event = threading.Event()
        self._discard_output = False
        self._duration = 0.0

    def request_finalize(self, duration: float) -> None:
        self._duration = max(0.0, float(duration))
        self._finalize_event.set()

    def request_cancel(self, discard_output: bool = False) -> None:
        self._discard_output = discard_output
        self._cancel_event.set()

    def run(self) -> None:
        try:
            while True:
                if self._cancel_event.is_set():
                    if self._discard_output:
                        self._service.discard_output()
                    self.live_cancelled.emit()
                    return
                force = self._finalize_event.is_set()
                started_at = time.monotonic()
                result = self._service.process_available(force, self.live_status.emit)
                processing_seconds = max(0.0, time.monotonic() - started_at)
                if result is not None:
                    audio_seconds = max(0.2, result.end_seconds - result.start_seconds)
                    self.live_metrics.emit(audio_seconds, processing_seconds)
                    self.live_confirmed.emit(result.end_seconds)
                if force:
                    if self._cancel_event.is_set():
                        continue
                    path = self._service.finish(self._duration)
                    self.live_completed.emit(str(path))
                    return
                if result is None:
                    time.sleep(0.2)
        except Exception as exc:
            self.live_failed.emit(str(exc))
