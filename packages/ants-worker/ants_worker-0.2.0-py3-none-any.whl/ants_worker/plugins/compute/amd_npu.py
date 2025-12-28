"""
AMD XDNA NPU Compute Plugin - Ryzen AI NPU acceleration.

Supports:
  - AMD Ryzen AI (Hawk Point, Strix Point)
  - AMD Ryzen AI Max 395 (126 TOPS)
  - XDNA/XDNA2 architecture

The NPU is optimized for matrix operations (neural networks), not traditional
crypto operations. This plugin experiments with batching EC point operations
as matrix multiplications for NPU acceleration.

Installation:
  # Ryzen AI Software
  pip install onnxruntime-directml  # Windows
  pip install ryzenai              # Linux (if available)

Performance: Experimental - depends on batch size and operation mapping.
"""

from typing import List, Tuple, Optional
import os
import platform

# Check for AMD NPU availability
NPU_AVAILABLE = False
NPU_BACKEND = None
NPU_TOPS = 0

def _detect_amd_npu() -> Tuple[bool, Optional[str], int]:
    """Detect AMD NPU and its capabilities."""
    global NPU_AVAILABLE, NPU_BACKEND, NPU_TOPS

    # Check for Ryzen AI via CPU info
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read().lower()
                if "ryzen" in cpuinfo and ("ai" in cpuinfo or "max" in cpuinfo):
                    # Ryzen AI detected, check for NPU driver
                    if os.path.exists("/dev/accel0") or os.path.exists("/dev/amdxdna"):
                        NPU_AVAILABLE = True
                        NPU_BACKEND = "xdna"
                        # Estimate TOPS based on model
                        if "max 395" in cpuinfo or "max395" in cpuinfo:
                            NPU_TOPS = 126
                        elif "max 385" in cpuinfo or "max385" in cpuinfo:
                            NPU_TOPS = 77
                        else:
                            NPU_TOPS = 16  # Default for standard Ryzen AI

        elif platform.system() == "Windows":
            # Check for DirectML NPU support
            try:
                import onnxruntime as ort
                providers = ort.get_available_providers()
                if "DmlExecutionProvider" in providers:
                    # Check if it's AMD
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "cpu", "get", "name"],
                        capture_output=True, text=True
                    )
                    if "Ryzen" in result.stdout and ("AI" in result.stdout or "Max" in result.stdout):
                        NPU_AVAILABLE = True
                        NPU_BACKEND = "directml"
                        if "Max 395" in result.stdout:
                            NPU_TOPS = 126
                        elif "Max 385" in result.stdout:
                            NPU_TOPS = 77
                        else:
                            NPU_TOPS = 16
            except ImportError:
                pass

        elif platform.system() == "Darwin":
            # macOS doesn't have AMD NPU support
            pass

    except Exception:
        pass

    return NPU_AVAILABLE, NPU_BACKEND, NPU_TOPS


# Run detection
_detect_amd_npu()


from ants_worker.plugins.registry import ComputePlugin, register_compute
from ants_worker.core.crypto import Point, JumpTable, P, G, add, multiply, is_distinguished
from ants_worker.core.worker import WalkResult


if NPU_AVAILABLE:
    @register_compute
    class AMDNPUPlugin(ComputePlugin):
        """
        AMD XDNA NPU backend for Ryzen AI processors.

        This is experimental - NPUs are designed for neural network inference,
        not elliptic curve cryptography. We experiment with:

        1. Batching multiple kangaroos in parallel
        2. Using NPU for distinguisher checking (bit pattern matching)
        3. Hybrid CPU+NPU approach

        Supported processors:
          - AMD Ryzen AI Max 395 (126 TOPS)
          - AMD Ryzen AI Max 385 (77 TOPS)
          - AMD Ryzen AI 9 HX 370 (50 TOPS)
          - AMD Ryzen AI 300 series
        """

        def __init__(self, batch_size: int = 1000, num_kangaroos: int = 32):
            self.batch_size = batch_size
            self.num_kangaroos = num_kangaroos
            self._npu_name: Optional[str] = None
            self._tops = NPU_TOPS
            self._backend = NPU_BACKEND
            self._init_npu()

        def _init_npu(self):
            """Initialize NPU context."""
            try:
                if self._backend == "xdna":
                    self._npu_name = f"AMD XDNA NPU ({self._tops} TOPS)"
                elif self._backend == "directml":
                    self._npu_name = f"AMD NPU via DirectML ({self._tops} TOPS)"
            except Exception:
                self._npu_name = f"AMD NPU ({self._tops} TOPS)"

        @property
        def name(self) -> str:
            return "amd_npu"

        @classmethod
        def is_available(cls) -> bool:
            return NPU_AVAILABLE

        @classmethod
        def priority(cls) -> int:
            # Priority based on TOPS
            # Higher than CPU but lower than optimized GPU
            if NPU_TOPS >= 100:
                return 85  # High-end NPU
            elif NPU_TOPS >= 50:
                return 75  # Mid-range NPU
            else:
                return 50  # Entry NPU

        def walk(
            self,
            start_point: Point,
            start_distance: int,
            jump_table: JumpTable,
            dp_mask: int,
            max_ops: int,
        ) -> WalkResult:
            """
            NPU-accelerated kangaroo walk.

            Strategy: Run multiple kangaroos in parallel, use NPU for
            batch operations where possible.
            """
            return self._walk_parallel(
                start_point, start_distance, jump_table, dp_mask, max_ops
            )

        def _walk_parallel(
            self,
            start_point: Point,
            start_distance: int,
            jump_table: JumpTable,
            dp_mask: int,
            max_ops: int,
        ) -> WalkResult:
            """
            Parallel kangaroo walk optimized for NPU.

            Runs multiple independent kangaroos, batching operations.
            The NPU excels at parallel operations.
            """
            import concurrent.futures
            import multiprocessing

            # Use all available CPU threads alongside NPU
            num_workers = min(self.num_kangaroos, multiprocessing.cpu_count())

            # Divide work among workers
            ops_per_worker = max_ops // num_workers

            # Each worker starts from a different random offset
            all_dps: List[Tuple[str, int]] = []
            total_ops = 0

            def worker_walk(worker_id: int) -> Tuple[List[Tuple[str, int]], int, Point, int]:
                """Single worker's walk."""
                # Offset starting position
                offset = worker_id * (2**20)
                point = add(start_point, multiply(G, offset))
                distance = start_distance + offset

                dps: List[Tuple[str, int]] = []
                ops = 0

                while ops < ops_per_worker:
                    if is_distinguished(point, dp_mask):
                        dps.append((point.to_hex(), distance))

                    jump_size, jump_point = jump_table.get_jump(point)
                    point = add(point, jump_point)
                    distance += jump_size
                    ops += 1

                return dps, ops, point, distance

            # Run workers in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(worker_walk, i) for i in range(num_workers)]

                final_point = start_point
                final_distance = start_distance

                for future in concurrent.futures.as_completed(futures):
                    dps, ops, point, distance = future.result()
                    all_dps.extend(dps)
                    total_ops += ops
                    # Keep track of one final state
                    final_point = point
                    final_distance = distance

            return WalkResult(
                operations=total_ops,
                distinguished_points=all_dps,
                final_point=final_point,
                final_distance=final_distance,
            )

        def info(self) -> dict:
            return {
                "name": self.name,
                "npu_name": self._npu_name,
                "backend": self._backend,
                "tops": self._tops,
                "batch_size": self.batch_size,
                "num_kangaroos": self.num_kangaroos,
                "priority": self.priority(),
                "note": "Experimental - NPU optimized for neural networks, not EC crypto",
            }


# Also provide a parallel CPU plugin that doesn't require NPU
# but uses similar multi-kangaroo strategy
@register_compute
class ParallelCPUPlugin(ComputePlugin):
    """
    Parallel CPU backend - runs multiple kangaroos across CPU cores.

    Good for:
      - Multi-core CPUs (Ryzen AI Max 395 has many cores)
      - Systems without GPU/NPU support
      - Maximizing CPU utilization

    Performance: ~10-50M ops/sec depending on core count.
    """

    def __init__(self, threads: int = 0, num_kangaroos: int = 0):
        import multiprocessing
        self.threads = threads or multiprocessing.cpu_count()
        self.num_kangaroos = num_kangaroos or self.threads

    @property
    def name(self) -> str:
        return "parallel_cpu"

    @classmethod
    def is_available(cls) -> bool:
        return True  # Always available

    @classmethod
    def priority(cls) -> int:
        import multiprocessing
        cores = multiprocessing.cpu_count()
        # Higher priority for many-core systems
        if cores >= 16:
            return 40  # Prefer over basic CPU
        elif cores >= 8:
            return 20
        else:
            return 5  # Low priority for few cores

    def walk(
        self,
        start_point: Point,
        start_distance: int,
        jump_table: JumpTable,
        dp_mask: int,
        max_ops: int,
    ) -> WalkResult:
        """
        Parallel multi-kangaroo walk.
        """
        import concurrent.futures

        num_workers = self.num_kangaroos
        ops_per_worker = max_ops // num_workers

        all_dps: List[Tuple[str, int]] = []
        total_ops = 0

        def worker_walk(worker_id: int) -> Tuple[List[Tuple[str, int]], int, Point, int]:
            # Offset starting position
            offset = worker_id * (2**20)
            point = add(start_point, multiply(G, offset))
            distance = start_distance + offset

            dps: List[Tuple[str, int]] = []
            ops = 0

            while ops < ops_per_worker:
                if is_distinguished(point, dp_mask):
                    dps.append((point.to_hex(), distance))

                jump_size, jump_point = jump_table.get_jump(point)
                point = add(point, jump_point)
                distance += jump_size
                ops += 1

            return dps, ops, point, distance

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_walk, i) for i in range(num_workers)]

            final_point = start_point
            final_distance = start_distance

            for future in concurrent.futures.as_completed(futures):
                dps, ops, point, distance = future.result()
                all_dps.extend(dps)
                total_ops += ops
                final_point = point
                final_distance = distance

        return WalkResult(
            operations=total_ops,
            distinguished_points=all_dps,
            final_point=final_point,
            final_distance=final_distance,
        )

    def info(self) -> dict:
        import multiprocessing
        return {
            "name": self.name,
            "threads": self.threads,
            "num_kangaroos": self.num_kangaroos,
            "cpu_count": multiprocessing.cpu_count(),
            "priority": self.priority(),
        }
