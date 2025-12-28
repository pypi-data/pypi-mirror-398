"""
Core Worker - The computation engine.

Platform-agnostic. Uses compute plugins for acceleration.
"""

import time
import uuid
import platform
from typing import Optional, List, Tuple, Callable
from dataclasses import dataclass

from ants_worker.core.crypto import Point, JumpTable, add, is_distinguished
from ants_worker.core.protocol import Work, Result, Heartbeat, WorkerInfo


@dataclass
class WalkResult:
    """Result of a kangaroo walk."""
    operations: int
    distinguished_points: List[Tuple[str, int]]
    final_point: Point
    final_distance: int


class Worker:
    """
    Core kangaroo worker.

    Compute backend is injected - can be CPU, CUDA, Metal, etc.
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        compute_backend: Optional["ComputePlugin"] = None,
    ):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.backend = compute_backend

        # Stats
        self.total_ops = 0
        self.total_dps = 0
        self._ops_per_second = 0

    def set_backend(self, backend: "ComputePlugin"):
        """Set compute backend."""
        self.backend = backend

    def walk(
        self,
        start_point: Point,
        start_distance: int,
        jump_table: JumpTable,
        dp_mask: int,
        max_ops: int,
    ) -> WalkResult:
        """
        Perform kangaroo walk.

        If backend is set, delegates to it.
        Otherwise uses pure Python.
        """
        if self.backend is not None:
            return self.backend.walk(
                start_point, start_distance, jump_table, dp_mask, max_ops
            )

        # Pure Python fallback
        return self._walk_python(
            start_point, start_distance, jump_table, dp_mask, max_ops
        )

    def _walk_python(
        self,
        start_point: Point,
        start_distance: int,
        jump_table: JumpTable,
        dp_mask: int,
        max_ops: int,
    ) -> WalkResult:
        """Pure Python kangaroo walk."""
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

    def process(self, work: Work) -> Result:
        """
        Process a work package.

        Args:
            work: Work package from Queen

        Returns:
            Result to send back
        """
        # Parse inputs
        start_point = Point.from_hex(work.start_point_hex)
        jump_table = JumpTable.from_list(work.jump_sizes)

        # Time the computation
        start_time = time.perf_counter()

        # Run walk
        result = self.walk(
            start_point=start_point,
            start_distance=work.start_distance,
            jump_table=jump_table,
            dp_mask=work.dp_mask,
            max_ops=work.ops_limit,
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # Update stats
        self.total_ops += result.operations
        self.total_dps += len(result.distinguished_points)
        if elapsed_ms > 0:
            self._ops_per_second = int(result.operations / (elapsed_ms / 1000))

        return Result(
            job_id=work.job_id,
            worker_id=self.worker_id,
            distinguished_points=result.distinguished_points,
            operations=result.operations,
            elapsed_ms=elapsed_ms,
            final_point_hex=result.final_point.to_hex(),
            final_distance=result.final_distance,
        )

    def heartbeat(self) -> Heartbeat:
        """Generate heartbeat."""
        return Heartbeat(
            worker_id=self.worker_id,
            backend=self.backend.name if self.backend else "python",
            ops_per_second=self._ops_per_second,
            total_ops=self.total_ops,
            total_dps=self.total_dps,
        )

    def info(self) -> WorkerInfo:
        """Get worker info."""
        return WorkerInfo(
            worker_id=self.worker_id,
            platform=platform.system(),
            backend=self.backend.name if self.backend else "python",
            ops_per_second=self._ops_per_second,
        )

    def benchmark(self, duration_secs: float = 5.0) -> dict:
        """
        Run benchmark to measure performance.
        """
        from ants_worker.core.crypto import multiply, G

        # Test setup
        test_point = multiply(G, 12345)
        jump_table = JumpTable(num_jumps=32, mean_jump=2**20)
        dp_mask = (1 << 20) - 1
        ops_per_batch = 10_000

        total_ops = 0
        total_dps = 0
        start_time = time.perf_counter()

        while (time.perf_counter() - start_time) < duration_secs:
            result = self.walk(
                test_point, 0, jump_table, dp_mask, ops_per_batch
            )
            total_ops += result.operations
            total_dps += len(result.distinguished_points)
            test_point = result.final_point

        elapsed = time.perf_counter() - start_time
        ops_per_sec = int(total_ops / elapsed) if elapsed > 0 else 0
        self._ops_per_second = ops_per_sec

        return {
            "backend": self.backend.name if self.backend else "python",
            "duration_secs": round(elapsed, 2),
            "total_operations": total_ops,
            "ops_per_second": ops_per_sec,
            "distinguished_points": total_dps,
        }
