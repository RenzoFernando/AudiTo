from __future__ import annotations

import unittest

from app.application.transcription_guard import TranscriptionGuard


class TranscriptionGuardTests(unittest.TestCase):
    def test_collapses_mechanical_single_word_loop(self) -> None:
        guard = TranscriptionGuard()
        text = guard.clean_segment("gracias gracias gracias gracias gracias gracias gracias gracias")
        self.assertEqual(text, "gracias")

    def test_preserves_human_repetition(self) -> None:
        guard = TranscriptionGuard()
        text = guard.clean_segment("La diferencia, la diferencia importante aquí, es que cambia el contexto")
        self.assertIn("la diferencia importante", text.casefold())

    def test_filters_repeated_near_duplicate_streak_conservatively(self) -> None:
        guard = TranscriptionGuard()
        base = "Este es un segmento suficientemente largo para comprobar que una repetición mecánica idéntica no continúe para siempre"
        self.assertTrue(guard.clean_segment(base))
        self.assertTrue(guard.clean_segment(base))
        self.assertEqual(guard.clean_segment(base), "")


if __name__ == "__main__":
    unittest.main()
