from __future__ import annotations

import threading
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioSnapshot:
    start_seconds: float
    end_seconds: float
    pcm: bytes
    sample_rate: int
    channels: int
    sample_width: int

    def write_wav(self, path: Path) -> None:
        with wave.open(str(path), "wb") as file:
            file.setnchannels(self.channels)
            file.setsampwidth(self.sample_width)
            file.setframerate(self.sample_rate)
            file.writeframes(self.pcm)


class LiveAudioBuffer:
    def __init__(self, sample_rate: int, channels: int = 1, sample_width: int = 2, max_seconds: float = 300.0) -> None:
        self._sample_rate = max(1, int(sample_rate))
        self._channels = max(1, int(channels))
        self._sample_width = max(1, int(sample_width))
        self._bytes_per_second = self._sample_rate * self._channels * self._sample_width
        self._max_bytes = max(self._bytes_per_second, int(max_seconds * self._bytes_per_second))
        self._data = bytearray()
        self._start_seconds = 0.0
        self._overflowed = False
        self._lock = threading.RLock()

    @property
    def start_seconds(self) -> float:
        with self._lock:
            return self._start_seconds

    @property
    def end_seconds(self) -> float:
        with self._lock:
            return self._start_seconds + len(self._data) / self._bytes_per_second

    @property
    def overflowed(self) -> bool:
        with self._lock:
            return self._overflowed

    def append(self, data: bytes) -> None:
        if not data:
            return
        with self._lock:
            self._data.extend(data)
            overflow = len(self._data) - self._max_bytes
            if overflow <= 0:
                return
            frame_size = self._channels * self._sample_width
            drop = overflow - (overflow % frame_size)
            if drop <= 0:
                drop = frame_size
            drop = min(drop, len(self._data))
            del self._data[:drop]
            self._start_seconds += drop / self._bytes_per_second
            self._overflowed = True

    def snapshot(self, start_seconds: float, end_seconds: float | None = None) -> AudioSnapshot:
        with self._lock:
            available_start = self._start_seconds
            available_end = self._start_seconds + len(self._data) / self._bytes_per_second
            start = max(available_start, float(start_seconds))
            end = available_end if end_seconds is None else min(available_end, float(end_seconds))
            if end <= start:
                return AudioSnapshot(start, start, b"", self._sample_rate, self._channels, self._sample_width)
            start_offset = int(round((start - available_start) * self._bytes_per_second))
            end_offset = int(round((end - available_start) * self._bytes_per_second))
            frame_size = self._channels * self._sample_width
            start_offset -= start_offset % frame_size
            end_offset -= end_offset % frame_size
            pcm = bytes(self._data[start_offset:end_offset])
            actual_start = available_start + start_offset / self._bytes_per_second
            actual_end = available_start + end_offset / self._bytes_per_second
            return AudioSnapshot(actual_start, actual_end, pcm, self._sample_rate, self._channels, self._sample_width)

    def release_before(self, seconds: float) -> None:
        with self._lock:
            target = min(max(float(seconds), self._start_seconds), self._start_seconds + len(self._data) / self._bytes_per_second)
            drop = int((target - self._start_seconds) * self._bytes_per_second)
            frame_size = self._channels * self._sample_width
            drop -= drop % frame_size
            if drop <= 0:
                return
            del self._data[:drop]
            self._start_seconds += drop / self._bytes_per_second
