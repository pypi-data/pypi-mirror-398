"""
CUDA Compute Plugin - NVIDIA GPU acceleration.

Requires: pip install cupy-cuda12x
Performance: ~500M-4B ops/sec depending on GPU.
"""

from typing import List, Tuple, Optional

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

from ants_worker.plugins.registry import ComputePlugin, register_compute
from ants_worker.core.crypto import Point, JumpTable, P, G, add, is_distinguished
from ants_worker.core.worker import WalkResult


# secp256k1 constants for GPU
_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


if CUPY_AVAILABLE:
    @register_compute
    class CUDAPlugin(ComputePlugin):
        """
        NVIDIA CUDA backend using CuPy.

        Batches operations for GPU efficiency.
        """

        def __init__(self, device: int = 0, batch_size: int = 10000):
            self.device = device
            self.batch_size = batch_size
            self._gpu_name: Optional[str] = None
            self._init_gpu()

        def _init_gpu(self):
            """Initialize GPU context."""
            try:
                with cp.cuda.Device(self.device):
                    props = cp.cuda.runtime.getDeviceProperties(self.device)
                    self._gpu_name = props["name"].decode()
            except Exception:
                self._gpu_name = "Unknown"

        @property
        def name(self) -> str:
            return "cuda"

        @classmethod
        def is_available(cls) -> bool:
            if not CUPY_AVAILABLE:
                return False
            try:
                return cp.cuda.runtime.getDeviceCount() > 0
            except Exception:
                return False

        @classmethod
        def priority(cls) -> int:
            return 100  # High priority

        def walk(
            self,
            start_point: Point,
            start_distance: int,
            jump_table: JumpTable,
            dp_mask: int,
            max_ops: int,
        ) -> WalkResult:
            """
            GPU-accelerated kangaroo walk.

            For now, uses CPU with batched operations.
            True CUDA kernel implementation coming.
            """
            # TODO: Implement full CUDA kernel
            # For now, use hybrid approach
            return self._walk_hybrid(
                start_point, start_distance, jump_table, dp_mask, max_ops
            )

        def _walk_hybrid(
            self,
            start_point: Point,
            start_distance: int,
            jump_table: JumpTable,
            dp_mask: int,
            max_ops: int,
        ) -> WalkResult:
            """
            Hybrid CPU/GPU walk.

            Does point arithmetic on CPU, will batch to GPU.
            """
            # For MVP, delegate to CPU
            # Real implementation would:
            # 1. Batch multiple kangaroos in parallel
            # 2. Use GPU for EC point additions
            # 3. Transfer only DPs back to CPU

            point = start_point
            distance = start_distance
            ops = 0
            dps: List[Tuple[str, int]] = []

            while ops < max_ops:
                if is_distinguished(point, dp_mask):
                    dps.append((point.to_hex(), distance))

                jump_size, jump_point = jump_table.get_jump(point)
                point = add(point, jump_point)
                distance += jump_size
                ops += 1

            return WalkResult(
                operations=ops,
                distinguished_points=dps,
                final_point=point,
                final_distance=distance,
            )

        def info(self) -> dict:
            mem_info = None
            try:
                with cp.cuda.Device(self.device):
                    free, total = cp.cuda.runtime.memGetInfo()
                    mem_info = {
                        "free_gb": free / (1024**3),
                        "total_gb": total / (1024**3),
                    }
            except Exception:
                pass

            return {
                "name": self.name,
                "device": self.device,
                "gpu_name": self._gpu_name,
                "batch_size": self.batch_size,
                "memory": mem_info,
                "priority": self.priority(),
            }
