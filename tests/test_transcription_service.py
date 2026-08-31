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


class GroupedFakeEngine:
    def transcribe(self, audio_path, profile, language_code, status_callback):
        status_callback("Transcribiendo")
        segments = iter([
            TranscriptionSegment(0.0, 4.0, "Esta es una idea"),
            TranscriptionSegment(4.0, 8.0, "que continúa en el siguiente segmento"),
            TranscriptionSegment(8.0, 12.0, "y todavía forma parte del mismo bloque"),
            TranscriptionSegment(12.0, 18.5, "hasta cerrar la oración completa."),
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

    def test_groups_contiguous_short_segments_into_one_text_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "clase.wav"
            audio.write_bytes(b"audio")
            output = root / "salida"
            job = TranscriptionJob(audio, "Español", "es", ModelProfile.BALANCED, duration=20.0)
            service = TranscriptionService(engine=GroupedFakeEngine())
            result = service.transcribe_job(
                job,
                output,
                threading.Event(),
                lambda value: None,
                lambda value: None,
            )
            text = result.output_path.read_text(encoding="utf-8")
            self.assertEqual(text.count("[00:00:"), 1)
            self.assertIn("Esta es una idea que continúa en el siguiente segmento y todavía forma parte del mismo bloque hasta cerrar la oración completa.", text)

    def test_can_export_without_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "clase.wav"
            audio.write_bytes(b"audio")
            output = root / "salida"
            job = TranscriptionJob(audio, "Español", "es", ModelProfile.BALANCED, duration=20.0)
            service = TranscriptionService(engine=GroupedFakeEngine())
            result = service.transcribe_job(
                job,
                output,
                threading.Event(),
                lambda value: None,
                lambda value: None,
                timestamps_enabled=False,
            )
            text = result.output_path.read_text(encoding="utf-8")
            self.assertNotIn("[00:00:", text)
            self.assertIn("Esta es una idea que continúa en el siguiente segmento", text)

    def test_uses_custom_output_name_and_preserves_unique_suffixes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "1 2 3.m4a"
            audio.write_bytes(b"audio")
            output = root / "salida"
            output.mkdir()
            (output / "Mi transcripcion.txt").write_text("existing", encoding="utf-8")
            job = TranscriptionJob(audio, "Español", "es", ModelProfile.BALANCED, duration=20.0)
            service = TranscriptionService(engine=FakeEngine())
            result = service.transcribe_job(
                job,
                output,
                threading.Event(),
                lambda value: None,
                lambda value: None,
                "Mi transcripcion.txt",
            )
            self.assertEqual(result.output_path.name, "Mi transcripcion (1).txt")
            text = result.output_path.read_text(encoding="utf-8")
            self.assertEqual(text.splitlines()[0], "Mi transcripcion (1)")
            self.assertIn("Archivo: 1 2 3.m4a", text)
            self.assertTrue(result.output_path.exists())


if __name__ == "__main__":
    unittest.main()
