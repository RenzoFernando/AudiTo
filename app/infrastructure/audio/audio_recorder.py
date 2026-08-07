from __future__ import annotations

import logging
import queue
import time
import wave
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class AudioRecordingError(RuntimeError):
    pass


@dataclass(frozen=True)
class RecordingStartResult:
    path: Path
    sample_rate: int


@dataclass(frozen=True)
class RecordingResult:
    path: Path
    duration: float
    sample_rate: int


class AudioRecorder:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._stream = None
        self._wave_file: wave.Wave_write | None = None
        self._writer_thread = None
        self._chunks: queue.SimpleQueue[bytes | None] = queue.SimpleQueue()
        self._path: Path | None = None
        self._started_at: float | None = None
        self._writer_error: Exception | None = None
        self._frame_callback: Callable[[bytes], None] | None = None
        self._sample_rate = 48000

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    @property
    def writer_error(self) -> Exception | None:
        return self._writer_error

    def default_input_name(self) -> str:
        try:
            import sounddevice as sd

            device = sd.query_devices(kind="input")
            name = str(device.get("name", "Micrófono predeterminado")).strip()
            return name or "Micrófono predeterminado"
        except Exception:
            return "Micrófono predeterminado"

    def start(self, output_dir: Path, frame_callback: Callable[[bytes], None] | None = None) -> RecordingStartResult:
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
            self._sample_rate = int(float(device.get("default_samplerate", 48000)))
            if self._sample_rate <= 0:
                self._sample_rate = 48000
            self._wave_file = wave.open(str(self._path), "wb")
            self._wave_file.setnchannels(1)
            self._wave_file.setsampwidth(2)
            self._wave_file.setframerate(self._sample_rate)
            self._writer_error = None
            self._frame_callback = frame_callback
            self._chunks = queue.SimpleQueue()
            import threading

            self._writer_thread = threading.Thread(target=self._writer_loop, name="AudiToAudioWriter", daemon=True)
            self._writer_thread.start()
            self._stream = sd.RawInputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype="int16",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._started_at = time.monotonic()
            self._logger.info("Grabación iniciada: path=%s samplerate=%s", self._path, self._sample_rate)
            return RecordingStartResult(self._path, self._sample_rate)
        except Exception as exc:
            self._cleanup_failed_start()
            raise AudioRecordingError(self._friendly_error(exc)) from exc

    def stop(self) -> RecordingResult:
        if not self.is_recording or self._path is None:
            raise AudioRecordingError("No hay una grabación en curso.")
        path = self._path
        started_at = self._started_at or time.monotonic()
        sample_rate = self._sample_rate
        writer_error = self._finish_stream()
        duration = max(0.0, time.monotonic() - started_at)
        self._reset_state()
        if writer_error:
            raise AudioRecordingError(self._friendly_write_error(writer_error)) from writer_error
        self._logger.info("Grabación finalizada: path=%s duration=%.2f", path, duration)
        return RecordingResult(path=path, duration=duration, sample_rate=sample_rate)

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
            if self._stream:
                self._stream.stop()
                self._stream.close()
        except Exception as exc:
            self._logger.warning("No se pudo cerrar correctamente el micrófono: %s", exc)
        finally:
            self._stream = None
        self._chunks.put(None)
        if self._writer_thread:
            self._writer_thread.join(timeout=8)
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
        self._frame_callback = None

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            self._logger.warning("Estado del micrófono: %s", status)
        if self._writer_error is not None:
            return
        data = bytes(indata)
        self._chunks.put(data)
        if self._frame_callback is not None:
            try:
                self._frame_callback(data)
            except Exception as exc:
                self._logger.warning("No se pudo copiar audio al búfer de transcripción: %s", exc)

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
        self._chunks.put(None)
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
        if "space" in message or "disk full" in message or "no space" in message:
            return "No hay espacio suficiente para guardar la grabación."
        if "device" in message or "input" in message or "microphone" in message:
            return "No se pudo acceder al micrófono. Revisa el dispositivo de entrada y los permisos de Windows."
        return "No se pudo iniciar la grabación. Revisa el micrófono e inténtalo nuevamente."

    def _friendly_write_error(self, exc: Exception) -> str:
        message = str(exc).lower()
        if "space" in message or "disk full" in message or "no space" in message:
            return "No hay espacio suficiente para guardar la grabación."
        return "La grabación se guardó de forma incompleta por un error de escritura."
