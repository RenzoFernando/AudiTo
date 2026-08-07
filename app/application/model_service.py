from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeTarget:
    device: str
    compute_type: str


class ModelService:
    def preferred_runtime(self) -> RuntimeTarget:
        try:
            import ctranslate2

            if ctranslate2.get_cuda_device_count() > 0:
                return RuntimeTarget("cuda", "float16")
        except Exception:
            pass
        return RuntimeTarget("cpu", "int8")
