from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ProfileDefinition:
    label: str
    model_name: str
    beam_size: int


class ModelProfile(Enum):
    FAST = ProfileDefinition("Rápida", "base", 1)
    BALANCED = ProfileDefinition("Equilibrada", "small", 3)
    MAXIMUM = ProfileDefinition("Máxima", "medium", 5)

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def model_name(self) -> str:
        return self.value.model_name

    @property
    def beam_size(self) -> int:
        return self.value.beam_size

    @classmethod
    def from_label(cls, label: str) -> "ModelProfile":
        for profile in cls:
            if profile.label == label:
                return profile
        return cls.BALANCED

    @classmethod
    def labels(cls) -> list[str]:
        return [profile.label for profile in cls]
