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
    def unique_output_path(self, output_dir: Path, input_path: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        candidate = output_dir / f"{input_path.stem}.txt"
        counter = 1
        while candidate.exists() or self.partial_path(candidate).exists():
            candidate = output_dir / f"{input_path.stem} ({counter}).txt"
            counter += 1
        return candidate

    def partial_path(self, final_path: Path) -> Path:
        return final_path.with_name(f"{final_path.stem}.partial.txt")

    def start(self, job: TranscriptionJob, final_path: Path) -> Path:
        partial = self.partial_path(final_path)
        title = job.input_path.stem.upper()
        lines = [
            title,
            "",
            f"Archivo: {job.input_path.name}",
            f"Duración: {format_duration(job.duration)}",
            f"Idioma: {job.language_label}",
            f"Fecha de transcripción: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Perfil: {job.model_profile.label}",
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
        with partial_path.open("a", encoding="utf-8") as file:
            file.write(f"[{format_timestamp(segment.start)}]\n\n{cleaned}\n\n")

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
        partial_path.replace(final_path)

    def discard(self, partial_path: Path, final_path: Path | None = None) -> None:
        partial_path.unlink(missing_ok=True)
        if final_path is not None:
            final_path.unlink(missing_ok=True)
