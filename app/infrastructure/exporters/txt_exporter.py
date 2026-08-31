from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.domain.transcription_job import TranscriptionJob
from app.domain.transcription_segment import TranscriptionSegment


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "No disponible"
    return format_timestamp(seconds)


class TxtExporter:
    _SILENCE_BREAK_SECONDS = 3.0
    _MAX_BLOCK_SECONDS = 36.0
    _MAX_BLOCK_WORDS = 75
    _NATURAL_BREAK_SECONDS = 18.0
    _NATURAL_BREAK_WORDS = 35

    def __init__(self) -> None:
        self._timestamps_enabled = True
        self._pending_segments: list[TranscriptionSegment] = []

    def unique_output_path(self, output_dir: Path, input_path: Path, output_name: str | None = None) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = self._output_stem(input_path, output_name)
        candidate = output_dir / f"{stem}.txt"
        counter = 1
        while candidate.exists() or self.partial_path(candidate).exists():
            candidate = output_dir / f"{stem} ({counter}).txt"
            counter += 1
        return candidate

    def _output_stem(self, input_path: Path, output_name: str | None) -> str:
        value = str(output_name or "").strip()
        if value.casefold().endswith(".txt"):
            value = value[:-4].rstrip()
        return value or input_path.stem

    def partial_path(self, final_path: Path) -> Path:
        return final_path.with_name(f"{final_path.stem}.partial.txt")

    def start(self, job: TranscriptionJob, final_path: Path, timestamps_enabled: bool = True) -> Path:
        partial = self.partial_path(final_path)
        self._timestamps_enabled = bool(timestamps_enabled)
        self._pending_segments = []
        title = final_path.stem
        lines = [
            title,
            "",
            f"Archivo: {job.input_path.name}",
            f"Duración: {format_duration(job.duration)}",
            f"Idioma: {job.language_label}",
            f"Fecha de transcripción: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Perfil: {job.profile_label or job.model_profile.label}",
            "",
            "------------------------------------------------------------",
            "",
        ]
        partial.write_text("\n".join(lines), encoding="utf-8")
        return partial

    def append_segment(self, partial_path: Path, segment: TranscriptionSegment) -> None:
        cleaned = " ".join(segment.text.strip().split())
        if not cleaned:
            return
        normalized = TranscriptionSegment(segment.start, segment.end, cleaned)
        if self._pending_segments:
            gap = max(0.0, normalized.start - self._pending_segments[-1].end)
            if gap >= self._SILENCE_BREAK_SECONDS:
                self.flush(partial_path)
        self._pending_segments.append(normalized)
        if self._should_flush():
            self.flush(partial_path)

    def flush(self, partial_path: Path) -> None:
        if not self._pending_segments:
            return
        start = self._pending_segments[0].start
        text = " ".join(segment.text for segment in self._pending_segments).strip()
        if text and text[-1] not in ".!?…":
            text += "."
        self._pending_segments = []
        if not text:
            return
        with partial_path.open("a", encoding="utf-8") as file:
            if self._timestamps_enabled:
                file.write(f"[{format_timestamp(start)}]\n\n{text}\n\n")
            else:
                file.write(f"{text}\n\n")

    def _should_flush(self) -> bool:
        if not self._pending_segments:
            return False
        first = self._pending_segments[0]
        last = self._pending_segments[-1]
        duration = max(0.0, last.end - first.start)
        words = sum(len(segment.text.split()) for segment in self._pending_segments)
        natural_end = last.text.rstrip().endswith((".", "?", "!", "…"))
        if duration >= self._MAX_BLOCK_SECONDS or words >= self._MAX_BLOCK_WORDS:
            return True
        return natural_end and (duration >= self._NATURAL_BREAK_SECONDS or words >= self._NATURAL_BREAK_WORDS)

    def update_duration(self, partial_path: Path, duration: float) -> None:
        if not partial_path.exists():
            return
        lines = partial_path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if line.startswith("Duración:"):
                lines[index] = f"Duración: {format_duration(duration)}"
                break
        partial_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def finish(self, partial_path: Path, final_path: Path) -> None:
        self.flush(partial_path)
        partial_path.replace(final_path)

    def discard(self, partial_path: Path, final_path: Path | None = None) -> None:
        self._pending_segments = []
        partial_path.unlink(missing_ok=True)
        if final_path is not None:
            final_path.unlink(missing_ok=True)
