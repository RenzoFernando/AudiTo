from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from app.application.transcription_service import TranscriptionService
from app.domain.model_profile import ModelProfile
from app.domain.transcription_job import TranscriptionJob
from app.domain.transcription_segment import TranscriptionSegment


class FakeEngine:
    def transcribe(self, audio_path, profile, language_code, status_callback):
        status_callback("Transcribiendo")
        segments = iter([
            TranscriptionSegment(1.2, 4.0, "Primera frase"),
            TranscriptionSegment(8.8, 12.0, "Segunda frase"),
        ])
        return segments, "es"


class TranscriptionServiceTests(unittest.TestCase):
    def test_writes_natural_segment_timestamps_and_finalizes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "clase.wav"
            audio.write_bytes(b"audio")
            output = root / "salida"
            job = TranscriptionJob(audio, "Español", "es", ModelProfile.BALANCED, duration=20.0)
            progress = []
            statuses = []
            service = TranscriptionService(engine=FakeEngine())
            result = service.transcribe_job(job, output, threading.Event(), progress.append, statuses.append)
            text = result.output_path.read_text(encoding="utf-8")
            self.assertIn("[00:00:01]", text)
            self.assertIn("[00:00:08]", text)
            self.assertTrue(result.output_path.exists())
            self.assertFalse((output / "clase.partial.txt").exists())
            self.assertEqual(progress[-1], 100)


if __name__ == "__main__":
    unittest.main()
