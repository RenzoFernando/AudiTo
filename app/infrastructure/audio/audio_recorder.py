from __future__ import annotations

import logging
import queue
import threading
import time
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class AudioRecordingError(RuntimeError):
    pass


@dataclass(frozen=True)
class RecordingResult:
    path: Path
    duration: float


class AudioRecorder:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._stream = None
        self._wave_file: wave.Wave_write | None = None
        self._writer_thread: threading.Thread | None = None
        self._chunks: queue.Queue[bytes | None] = queue.Queue(maxsize=512)
        self._path: Path | None = None
        self._started_at: float | None = None
        self._writer_error: Exception | None = None

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def default_input_name(self) -> str:
        try:
            import sounddevice as sd

            device = sd.query_devices(kind="input")
            name = str(device.get("name", "Micrófono predeterminado")).strip()
            return name or "Micrófono predeterminado"
        except Exception:
            return "Micrófono predeterminado"

    def start(self, output_dir: Path) -> Path:
        if self.is_recording:
            raise AudioRecordingError("Ya hay una grabación en curso.")
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise AudioRecordingError("Falta el componente de grabación. Reinicia AudiTo para instalarlo.") from exc

        recordings_dir = output_dir / "Grabaciones"
        recordings_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._unique_recording_path(recordings_dir)
        try:
            device = sd.query_devices(kind="input")
            sample_rate = int(float(device.get("default_samplerate", 48000)))
            if sample_rate <= 0:
                sample_rate = 48000
            self._wave_file = wave.open(str(self._path), "wb")
            self._wave_file.setnchannels(1)
            self._wave_file.setsampwidth(2)
            self._wave_file.setframerate(sample_rate)
            self._writer_error = None
            self._chunks = queue.Queue(maxsize=512)
            self._writer_thread = threading.Thread(target=self._writer_loop, name="AudiToAudioWriter", daemon=True)
            self._writer_thread.start()
            self._stream = sd.RawInputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._started_at = time.monotonic()
            self._logger.info("Grabación iniciada: path=%s samplerate=%s", self._path, sample_rate)
            return self._path
        except Exception as exc:
            self._cleanup_failed_start()
            raise AudioRecordingError(self._friendly_error(exc)) from exc

    def stop(self) -> RecordingResult:
        if not self.is_recording or self._path is None:
            raise AudioRecordingError("No hay una grabación en curso.")
        path = self._path
        started_at = self._started_at or time.monotonic()
        writer_error = self._finish_stream()
        duration = max(0.0, time.monotonic() - started_at)
        self._reset_state()
        if writer_error:
            raise AudioRecordingError("La grabación se guardó de forma incompleta por un error de escritura.") from writer_error
        self._logger.info("Grabación finalizada: path=%s duration=%.2f", path, duration)
        return RecordingResult(path=path, duration=duration)

    def cancel(self) -> None:
        if not self.is_recording or self._path is None:
            return
        path = self._path
        self._finish_stream()
        self._reset_state()
        try:
            path.unlink(missing_ok=True)
        except Exception as exc:
            self._logger.warning("No se pudo eliminar la grabación descartada: %s", exc)
        self._logger.info("Grabación descartada: path=%s", path)

    def _finish_stream(self) -> Exception | None:
        try:
            self._stream.stop()
            self._stream.close()
        except Exception as exc:
            self._logger.warning("No se pudo cerrar correctamente el micrófono: %s", exc)
        finally:
            self._stream = None
        try:
            self._chunks.put(None, timeout=2)
        except queue.Full:
            self._logger.warning("No se pudo cerrar inmediatamente el búfer de grabación.")
        if self._writer_thread:
            self._writer_thread.join(timeout=5)
        if self._wave_file:
            try:
                self._wave_file.close()
            except Exception as exc:
                self._logger.warning("No se pudo cerrar correctamente el archivo de audio: %s", exc)
        return self._writer_error

    def _reset_state(self) -> None:
        self._wave_file = None
        self._writer_thread = None
        self._path = None
        self._started_at = None
        self._writer_error = None

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            self._logger.warning("Estado del micrófono: %s", status)
        try:
            self._chunks.put_nowait(bytes(indata))
        except queue.Full:
            self._logger.warning("Se descartó un bloque de audio porque el búfer de grabación estaba lleno.")

    def _writer_loop(self) -> None:
        try:
            while True:
                chunk = self._chunks.get()
                if chunk is None:
                    break
                if self._wave_file:
                    self._wave_file.writeframesraw(chunk)
        except Exception as exc:
            self._writer_error = exc
            self._logger.exception("Error escribiendo la grabación")

    def _cleanup_failed_start(self) -> None:
        try:
            if self._stream:
                self._stream.close()
        except Exception:
            pass
        self._stream = None
        try:
            self._chunks.put_nowait(None)
        except Exception:
            pass
        if self._writer_thread:
            self._writer_thread.join(timeout=2)
        if self._wave_file:
            try:
                self._wave_file.close()
            except Exception:
                pass
        if self._path:
            try:
                self._path.unlink(missing_ok=True)
            except Exception:
                pass
        self._reset_state()

    def _unique_recording_path(self, directory: Path) -> Path:
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        candidate = directory / f"Grabacion_{stamp}.wav"
        counter = 1
        while candidate.exists():
            candidate = directory / f"Grabacion_{stamp} ({counter}).wav"
            counter += 1
        return candidate

    def _friendly_error(self, exc: Exception) -> str:
        message = str(exc).lower()
        if "device" in message or "input" in message or "microphone" in message:
            return "No se pudo acceder al micrófono. Revisa el dispositivo de entrada y los permisos de Windows."
        return "No se pudo iniciar la grabación. Revisa el micrófono e inténtalo nuevamente."
