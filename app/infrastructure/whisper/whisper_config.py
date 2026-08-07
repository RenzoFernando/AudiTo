from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WhisperConfig:
    vad_filter: bool = True
    vad_parameters: dict = field(default_factory=lambda: {"min_silence_duration_ms": 300})
    condition_on_previous_text: bool = False
    temperature: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6)
    compression_ratio_threshold: float = 2.4
    log_prob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    repetition_penalty: float = 1.05
    no_repeat_ngram_size: int = 5
    word_timestamps: bool = False

    def transcribe_kwargs(self, language_code: str | None, beam_size: int) -> dict:
        return {
            "language": language_code,
            "beam_size": beam_size,
            "vad_filter": self.vad_filter,
            "vad_parameters": dict(self.vad_parameters),
            "condition_on_previous_text": self.condition_on_previous_text,
            "temperature": list(self.temperature),
            "compression_ratio_threshold": self.compression_ratio_threshold,
            "log_prob_threshold": self.log_prob_threshold,
            "no_speech_threshold": self.no_speech_threshold,
            "repetition_penalty": self.repetition_penalty,
            "no_repeat_ngram_size": self.no_repeat_ngram_size,
            "word_timestamps": self.word_timestamps,
        }
