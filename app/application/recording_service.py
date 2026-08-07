from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.constants import LIVE_BUFFER_MAX_SECONDS
from app.domain.recording_session import RecordingSession
from app.infrastructure.audio.audio_recorder import AudioRecorder, AudioRecordingError
from app.infrastructure.audio.live_audio_buffer import LiveAudioBuffer


class RecordingService:
    def __init__(self, recorder: AudioRecorder | None = None) -> None:
        self._recorder = recorder or AudioRecorder()
        self._buffer: LiveAudioBuffer | None = None
        self._session: RecordingSession | None = None

    @property
    def is_recording(self) -> bool:
        return self._recorder.is_recording

    @property
    def buffer(self) -> LiveAudioBuffer | None:
        return self._buffer

    @property
    def session(self) -> RecordingSession | None:
        return self._session

    @property
    def writer_error(self) -> Exception | None:
        return self._recorder.writer_error

    def default_input_name(self) -> str:
        return self._recorder.default_input_name()

    def start(self, output_dir: Path) -> RecordingSession:
        holder: dict[str, LiveAudioBuffer] = {}

        def append_frame(data: bytes) -> None:
            buffer = holder.get("buffer")
            if buffer is not None:
                buffer.append(data)

        result = self._recorder.start(output_dir, append_frame)
        self._buffer = LiveAudioBuffer(result.sample_rate, max_seconds=LIVE_BUFFER_MAX_SECONDS)
        holder["buffer"] = self._buffer
        self._session = RecordingSession(result.path, result.sample_rate, datetime.now())
        return self._session

    def stop(self) -> RecordingSession:
        result = self._recorder.stop()
        if self._session is None:
            self._session = RecordingSession(result.path, result.sample_rate, datetime.now(), result.duration)
        self._session.duration = result.duration
        return self._session

    def discard(self) -> None:
        self._recorder.cancel()
        self._session = None
        self._buffer = None

    def reset(self) -> None:
        self._session = None
        self._buffer = None


__all__ = ["RecordingService", "AudioRecordingError"]
