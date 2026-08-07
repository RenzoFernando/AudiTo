from __future__ import annotations

import re
from difflib import SequenceMatcher


class TranscriptionGuard:
    def __init__(self) -> None:
        self._last_normalized = ""
        self._duplicate_streak = 0

    def clean_segment(self, text: str) -> str:
        compact = " ".join(str(text).strip().split())
        if not compact:
            return ""
        compact = re.sub(r"(?:\.\.\.\s*){3,}", "... ", compact).strip()
        compact = self._collapse_repeated_phrases(compact)
        normalized = self._normalize(compact)
        if not normalized:
            return ""
        if self._last_normalized and self._is_near_duplicate(normalized, self._last_normalized):
            self._duplicate_streak += 1
            self._last_normalized = normalized
            if self._duplicate_streak >= 2:
                return ""
        else:
            self._duplicate_streak = 0
            self._last_normalized = normalized
        return compact

    def finalize_block(self, text: str) -> str:
        compact = " ".join(str(text).strip().split())
        if compact and compact[-1] not in ".!?…":
            compact += "."
        return compact

    def _collapse_repeated_phrases(self, text: str) -> str:
        words = text.split()
        output: list[str] = []
        index = 0
        while index < len(words):
            match = self._repeated_phrase_at(words, index)
            if match is None:
                output.append(words[index])
                index += 1
                continue
            size, repeats = match
            output.extend(words[index:index + size])
            index += size * repeats
        return " ".join(output)

    def _repeated_phrase_at(self, words: list[str], index: int) -> tuple[int, int] | None:
        remaining = len(words) - index
        max_size = min(12, remaining // 3)
        for size in range(2, max_size + 1):
            phrase = [self._token(word) for word in words[index:index + size]]
            repeats = 1
            while index + (repeats + 1) * size <= len(words):
                next_phrase = [self._token(word) for word in words[index + repeats * size:index + (repeats + 1) * size]]
                if phrase != next_phrase:
                    break
                repeats += 1
            minimum_repeats = 4 if size == 2 else 3
            if repeats >= minimum_repeats:
                return size, repeats
        return None

    def _is_near_duplicate(self, current: str, previous: str) -> bool:
        if len(current) < 40 or len(previous) < 40:
            return False
        length_ratio = len(current) / max(1, len(previous))
        if length_ratio < 0.82 or length_ratio > 1.18:
            return False
        return SequenceMatcher(None, current, previous).ratio() >= 0.96

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^a-záéíóúüñ0-9 ]+", "", text.casefold()).strip()

    def _token(self, word: str) -> str:
        return re.sub(r"[^a-záéíóúüñ0-9]+", "", word.casefold())
