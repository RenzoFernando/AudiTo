from __future__ import annotations

import shutil
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


class FlacChunkerError(RuntimeError):
    pass


class FlacChunkingCancelled(RuntimeError):
    pass


@dataclass(frozen=True)
class FlacChunk:
    path: Path
    start_seconds: float
    end_seconds: float


class FlacChunker:
    SAMPLE_RATE = 16000
    CHUNK_SECONDS = 540.0
    DIRECT_FLAC_MAX_BYTES = 24 * 1024 * 1024

    def prepare(
        self,
        input_path: Path,
        temp_root: Path,
        cancel_event: threading.Event,
        status_callback: Callable[[str], None],
        progress_callback: Callable[[int], None],
        duration: float | None = None,
    ) -> list[FlacChunk]:
        work_dir = temp_root / f"groq_flac_{uuid.uuid4().hex}"
        work_dir.mkdir(parents=True, exist_ok=True)
        status_callback("GROQ_PREPARING_FLAC")
        if (
            input_path.suffix.casefold() == ".flac"
            and input_path.exists()
            and input_path.stat().st_size <= self.DIRECT_FLAC_MAX_BYTES
            and duration is not None
            and duration > 0
        ):
            target = work_dir / "chunk_0001.flac"
            try:
                shutil.copy2(input_path, target)
            except Exception as exc:
                shutil.rmtree(work_dir, ignore_errors=True)
                raise FlacChunkerError("No se pudo preparar el archivo FLAC para la transcripción online.") from exc
            if cancel_event.is_set():
                shutil.rmtree(work_dir, ignore_errors=True)
                raise FlacChunkingCancelled()
            progress_callback(15)
            return [FlacChunk(target, 0.0, float(duration))]

        try:
            import av
        except ImportError as exc:
            shutil.rmtree(work_dir, ignore_errors=True)
            raise FlacChunkerError("Falta PyAV para preparar el audio online. Reinicia AudiTo después de instalar las dependencias.") from exc

        chunks: list[FlacChunk] = []
        target_samples = max(1, int(self.CHUNK_SECONDS * self.SAMPLE_RATE))
        total_samples = 0
        chunk_start_samples = 0
        chunk_samples = 0
        output_container = None
        output_stream = None
        chunk_path: Path | None = None

        def open_chunk() -> None:
            nonlocal output_container, output_stream, chunk_path
            chunk_path = work_dir / f"chunk_{len(chunks) + 1:04d}.flac"
            output_container = av.open(str(chunk_path), mode="w", format="flac")
            output_stream = output_container.add_stream("flac", rate=self.SAMPLE_RATE)
            output_stream.layout = "mono"
            output_stream.format = "s16"

        def close_chunk() -> None:
            nonlocal output_container, output_stream, chunk_path, chunk_samples, chunk_start_samples
            if output_container is None or output_stream is None or chunk_path is None:
                return
            for packet in output_stream.encode(None):
                output_container.mux(packet)
            output_container.close()
            end_samples = chunk_start_samples + chunk_samples
            if chunk_path.exists() and chunk_path.stat().st_size > 0 and chunk_samples > 0:
                chunks.append(
                    FlacChunk(
                        path=chunk_path,
                        start_seconds=chunk_start_samples / self.SAMPLE_RATE,
                        end_seconds=end_samples / self.SAMPLE_RATE,
                    )
                )
            else:
                chunk_path.unlink(missing_ok=True)
            chunk_start_samples = end_samples
            chunk_samples = 0
            output_container = None
            output_stream = None
            chunk_path = None

        try:
            with av.open(str(input_path), mode="r", metadata_errors="ignore") as input_container:
                if not input_container.streams.audio:
                    raise FlacChunkerError("No se encontró una pista de audio válida en el archivo seleccionado.")
                resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=self.SAMPLE_RATE)
                for frame in input_container.decode(audio=0):
                    if cancel_event.is_set():
                        raise FlacChunkingCancelled()
                    for resampled in resampler.resample(frame):
                        if cancel_event.is_set():
                            raise FlacChunkingCancelled()
                        if output_container is None:
                            open_chunk()
                        resampled.pts = None
                        for packet in output_stream.encode(resampled):
                            output_container.mux(packet)
                        frame_samples = int(resampled.samples)
                        chunk_samples += frame_samples
                        total_samples += frame_samples
                        if duration and duration > 0:
                            converted = min(1.0, total_samples / max(1.0, duration * self.SAMPLE_RATE))
                            progress_callback(max(1, min(15, int(converted * 15))))
                        if chunk_samples >= target_samples:
                            close_chunk()
                for resampled in resampler.resample(None):
                    if cancel_event.is_set():
                        raise FlacChunkingCancelled()
                    if output_container is None:
                        open_chunk()
                    resampled.pts = None
                    for packet in output_stream.encode(resampled):
                        output_container.mux(packet)
                    frame_samples = int(resampled.samples)
                    chunk_samples += frame_samples
                    total_samples += frame_samples
                close_chunk()
            if not chunks:
                raise FlacChunkerError("No se pudo preparar audio válido para la transcripción online.")
            progress_callback(15)
            return chunks
        except FlacChunkingCancelled:
            if output_container is not None:
                try:
                    output_container.close()
                except Exception:
                    pass
            shutil.rmtree(work_dir, ignore_errors=True)
            raise
        except FlacChunkerError:
            if output_container is not None:
                try:
                    output_container.close()
                except Exception:
                    pass
            shutil.rmtree(work_dir, ignore_errors=True)
            raise
        except Exception as exc:
            if output_container is not None:
                try:
                    output_container.close()
                except Exception:
                    pass
            shutil.rmtree(work_dir, ignore_errors=True)
            raise FlacChunkerError("No se pudo convertir el audio a FLAC para la transcripción online.") from exc
