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
    BASE = ProfileDefinition("Base", "base", 1, "Más ligero · menor precisión")
    FAST = ProfileDefinition("Rápida", "small", 3, "Rápida · buena para uso diario")
    BALANCED = ProfileDefinition("Equilibrada", "medium", 5, "Más precisa · mayor consumo")
    MAXIMUM = ProfileDefinition("Máxima", "large-v3", 5, "Máxima precisión · más lenta")

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
