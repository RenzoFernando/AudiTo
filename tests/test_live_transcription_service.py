from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.application.live_transcription_service import LiveTranscriptionService
from app.domain.model_profile import ModelProfile
from app.domain.transcription_job import TranscriptionJob
from app.domain.transcription_segment import TranscriptionSegment
from app.infrastructure.audio.live_audio_buffer import LiveAudioBuffer
from app.infrastructure.system.app_paths import AppPaths


class FakeLiveEngine:
    def __init__(self) -> None:
        self.calls = 0

    def transcribe(self, audio_path, profile, language_code, status_callback):
        self.calls += 1
        status_callback("Transcribiendo")
        if self.calls == 1:
            return iter([
                TranscriptionSegment(1.0, 3.0, "Inicio de la clase"),
                TranscriptionSegment(27.8, 30.0, "integración continua"),
            ]), "es"
        return iter([
            TranscriptionSegment(0.3, 2.5, "integración continua"),
            TranscriptionSegment(4.0, 7.0, "Ahora veamos el pipeline"),
        ]), "es"


class LiveTranscriptionServiceTests(unittest.TestCase):
    def test_progressive_processing_offsets_and_merges_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "out"
            recording = output / "Grabaciones" / "Grabacion.wav"
            buffer = LiveAudioBuffer(sample_rate=10, channels=1, sample_width=2, max_seconds=300)
            buffer.append(b"\x01\x00" * 300)
            job = TranscriptionJob(recording, "Español", "es", ModelProfile.BALANCED)
            engine = FakeLiveEngine()
            with patch.object(AppPaths, "temp_dir", return_value=root / "temp"):
                (root / "temp").mkdir()
                service = LiveTranscriptionService(job, output, buffer, engine=engine)
                first = service.process_available(False, lambda value: None)
                self.assertIsNotNone(first)
                buffer.append(b"\x01\x00" * 300)
                second = service.process_available(False, lambda value: None)
                self.assertIsNotNone(second)
                final = service.finish(60.0)
            text = final.read_text(encoding="utf-8")
            self.assertEqual(text.count("integración continua"), 1)
            self.assertIn("[00:00:31]", text)
            self.assertIn("Ahora veamos el pipeline", text)


if __name__ == "__main__":
    unittest.main()
