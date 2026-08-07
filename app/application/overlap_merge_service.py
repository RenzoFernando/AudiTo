from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.domain.transcription_segment import TranscriptionSegment


class OverlapMergeService:
    def merge(
        self,
        confirmed_tail: list[TranscriptionSegment],
        new_segments: list[TranscriptionSegment],
        boundary_seconds: float,
        overlap_seconds: float,
    ) -> list[TranscriptionSegment]:
        if not new_segments:
            return []
        if boundary_seconds <= 0 or not confirmed_tail:
            return new_segments
        nearby_previous = [segment for segment in confirmed_tail if segment.end >= boundary_seconds - overlap_seconds - 2.0]
        merged: list[TranscriptionSegment] = []
        for segment in new_segments:
            if self._is_boundary_duplicate(segment, nearby_previous, boundary_seconds, overlap_seconds):
                continue
            if not merged and segment.start <= boundary_seconds + overlap_seconds + 1.0:
                trimmed = self._trim_prefix(segment.text, nearby_previous)
                if not trimmed:
                    continue
                segment = TranscriptionSegment(segment.start, segment.end, trimmed)
            merged.append(segment)
        return merged

    def _is_boundary_duplicate(
        self,
        current: TranscriptionSegment,
        previous: list[TranscriptionSegment],
        boundary_seconds: float,
        overlap_seconds: float,
    ) -> bool:
        if current.start > boundary_seconds + overlap_seconds + 1.0:
            return False
        current_text = self._normalize(current.text)
        if len(current_text) < 12:
            return False
        for segment in previous:
            if abs(current.start - segment.start) > overlap_seconds + 4.0 and abs(current.end - segment.end) > overlap_seconds + 4.0:
                continue
            previous_text = self._normalize(segment.text)
            if not previous_text:
                continue
            ratio = SequenceMatcher(None, current_text, previous_text).ratio()
            if ratio >= 0.93:
                return True
        return False

    def _trim_prefix(self, text: str, previous: list[TranscriptionSegment]) -> str:
        words = text.split()
        if len(words) < 2 or not previous:
            return text
        previous_words = " ".join(segment.text for segment in previous[-4:]).split()
        normalized_previous = [self._token(word) for word in previous_words]
        normalized_current = [self._token(word) for word in words]
        maximum = min(20, len(normalized_previous), len(normalized_current))
        for size in range(maximum, 1, -1):
            left = normalized_previous[-size:]
            right = normalized_current[:size]
            if left == right:
                return " ".join(words[size:]).strip()
            if size >= 4 and SequenceMatcher(None, " ".join(left), " ".join(right)).ratio() >= 0.94:
                return " ".join(words[size:]).strip()
        return text

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^a-záéíóúüñ0-9 ]+", "", text.casefold()).strip()

    def _token(self, word: str) -> str:
        return re.sub(r"[^a-záéíóúüñ0-9]+", "", word.casefold())
