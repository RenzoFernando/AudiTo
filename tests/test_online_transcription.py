from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from app.application.transcription_service import TranscriptionService
from app.constants import ONLINE_PROFILE_LABEL
from app.domain.model_profile import ModelProfile
from app.domain.transcription_job import TranscriptionJob
from app.domain.transcription_segment import TranscriptionSegment


class FailingLocalEngine:
    def transcribe(self, audio_path, profile, language_code, status_callback):
        raise AssertionError("El motor local no debe ejecutarse para el perfil Online")


class FakeOnlineEngine:
    def __init__(self) -> None:
        self.api_key = None

    def transcribe(
        self,
        audio_path,
        language_code,
        api_key,
        status_callback,
        progress_callback,
        cancel_event,
        duration=None,
        segment_callback=None,
    ):
        self.api_key = api_key
        status_callback("GROQ_PREPARING_FLAC")
        progress_callback(15)
        first = [TranscriptionSegment(0.0, 5.0, "Primera parte online")]
        second = [TranscriptionSegment(5.0, 10.0, "Segunda parte online")]
        if segment_callback is not None:
            segment_callback(first)
        progress_callback(55)
        if segment_callback is not None:
            segment_callback(second)
        progress_callback(95)
        return first + second, "es"


class OnlineTranscriptionTests(unittest.TestCase):
    def test_online_profile_uses_online_engine_and_exports_profile_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "clase.m4a"
            audio.write_bytes(b"audio")
            output = root / "salida"
            online_engine = FakeOnlineEngine()
            service = TranscriptionService(engine=FailingLocalEngine(), online_engine=online_engine)
            job = TranscriptionJob(
                audio,
                "Español",
                "es",
                ModelProfile.MAXIMUM,
                duration=10.0,
                profile_label=ONLINE_PROFILE_LABEL,
                online=True,
            )
            progress = []
            statuses = []
            result = service.transcribe_job(
                job,
                output,
                threading.Event(),
                progress.append,
                statuses.append,
                groq_api_key="test-key",
            )
            text = result.output_path.read_text(encoding="utf-8")
            self.assertEqual(online_engine.api_key, "test-key")
            self.assertIn("Perfil: Online", text)
            self.assertIn("Primera parte online Segunda parte online", text)
            self.assertIn("GROQ_PREPARING_FLAC", statuses)
            self.assertEqual(progress[-1], 100)


if __name__ == "__main__":
    unittest.main()
