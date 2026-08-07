from __future__ import annotations

import unittest

from app.infrastructure.audio.live_audio_buffer import LiveAudioBuffer


class LiveAudioBufferTests(unittest.TestCase):
    def test_snapshot_uses_global_offsets(self) -> None:
        buffer = LiveAudioBuffer(sample_rate=10, channels=1, sample_width=2, max_seconds=10)
        buffer.append(b"\x01\x00" * 50)
        snapshot = buffer.snapshot(2.0, 4.0)
        self.assertAlmostEqual(snapshot.start_seconds, 2.0, places=1)
        self.assertAlmostEqual(snapshot.end_seconds, 4.0, places=1)
        self.assertEqual(len(snapshot.pcm), 40)

    def test_release_keeps_overlap_region(self) -> None:
        buffer = LiveAudioBuffer(sample_rate=10, channels=1, sample_width=2, max_seconds=10)
        buffer.append(b"\x01\x00" * 60)
        buffer.release_before(3.5)
        self.assertAlmostEqual(buffer.start_seconds, 3.5, places=1)
        self.assertAlmostEqual(buffer.end_seconds, 6.0, places=1)

    def test_buffer_is_bounded(self) -> None:
        buffer = LiveAudioBuffer(sample_rate=10, channels=1, sample_width=2, max_seconds=2)
        buffer.append(b"\x01\x00" * 50)
        self.assertTrue(buffer.overflowed)
        self.assertLessEqual(buffer.end_seconds - buffer.start_seconds, 2.1)


if __name__ == "__main__":
    unittest.main()
