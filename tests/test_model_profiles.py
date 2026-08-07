from __future__ import annotations

import unittest

from app.constants import DEFAULT_PROFILE
from app.domain.model_profile import ModelProfile


class ModelProfileTests(unittest.TestCase):
    def test_only_requested_profiles_are_visible(self) -> None:
        self.assertEqual(ModelProfile.labels(), ["Rápida", "Equilibrada", "Máxima"])

    def test_balanced_is_default(self) -> None:
        self.assertEqual(DEFAULT_PROFILE, "Equilibrada")
        self.assertEqual(ModelProfile.from_label("desconocido"), ModelProfile.BALANCED)


if __name__ == "__main__":
    unittest.main()
