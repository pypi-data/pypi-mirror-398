"""
CPU Compute Plugin - Pure Python, works everywhere.
"""

import os
from typing import List, Tuple

from ants_worker.plugins.registry import ComputePlugin, register_compute
from ants_worker.core.crypto import Point, JumpTable, add, is_distinguished
from ants_worker.core.worker import WalkResult


@register_compute
class CPUPlugin(ComputePlugin):
    """
    Pure Python CPU backend.

    Works on any platform. ~1M ops/sec.
    """

    def __init__(self, threads: int = 0):
        self.threads = threads or os.cpu_count() or 1

    @property
    def name(self) -> str:
        return "cpu"

    @classmethod
    def is_available(cls) -> bool:
        return True  # Always available

    @classmethod
    def priority(cls) -> int:
        return 0  # Lowest priority (fallback)

    def walk(
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

    def info(self) -> dict:
        return {
            "name": self.name,
            "threads": self.threads,
            "priority": self.priority(),
        }
