from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ProfileDefinition:
    label: str
    model_name: str
    beam_size: int
    hint: str


class ModelProfile(Enum):
    FAST = ProfileDefinition("Rápida", "small", 3, "Menor consumo · más rápida")
    BALANCED = ProfileDefinition("Equilibrada", "medium", 5, "Balance entre precisión y velocidad")
    MAXIMUM = ProfileDefinition("Máxima", "large-v3", 5, "Mayor precisión · más consumo")

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def model_name(self) -> str:
        return self.value.model_name

    @property
    def beam_size(self) -> int:
        return self.value.beam_size

    @property
    def hint(self) -> str:
        return self.value.hint

    @classmethod
    def from_label(cls, label: str) -> "ModelProfile":
        for profile in cls:
            if profile.label == label:
                return profile
        return cls.BALANCED

    @classmethod
    def labels(cls) -> list[str]:
        return [profile.label for profile in cls]
