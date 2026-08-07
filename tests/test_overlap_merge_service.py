from __future__ import annotations

import unittest

from app.application.overlap_merge_service import OverlapMergeService
from app.domain.transcription_segment import TranscriptionSegment


class OverlapMergeServiceTests(unittest.TestCase):
    def test_removes_boundary_duplicate(self) -> None:
        service = OverlapMergeService()
        previous = [TranscriptionSegment(24.0, 30.0, "vamos a revisar integración continua.")]
        incoming = [
            TranscriptionSegment(27.8, 31.0, "integración continua."),
            TranscriptionSegment(31.0, 35.0, "Ahora veamos el pipeline."),
        ]
        merged = service.merge(previous, incoming, 30.0, 2.5)
        self.assertEqual([segment.text for segment in merged], ["Ahora veamos el pipeline."])

    def test_preserves_new_content_near_boundary(self) -> None:
        service = OverlapMergeService()
        previous = [TranscriptionSegment(24.0, 30.0, "cerramos el tema anterior.")]
        incoming = [TranscriptionSegment(28.0, 33.0, "Ahora empieza una idea nueva.")]
        merged = service.merge(previous, incoming, 30.0, 2.5)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].text, incoming[0].text)


if __name__ == "__main__":
    unittest.main()
