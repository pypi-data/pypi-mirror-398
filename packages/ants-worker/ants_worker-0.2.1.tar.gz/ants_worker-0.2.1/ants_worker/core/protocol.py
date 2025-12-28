"""
Protocol - Message types for Queen <-> Worker communication.

Minimal, serializable, no secrets.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Tuple, Optional
import json


@dataclass
class Work:
    """
    Work package from Queen.

    Worker receives only what it needs to compute.
    No target info, no context, just math.
    """
    job_id: str
    start_point_hex: str      # Compressed EC point
    start_distance: int       # Starting scalar offset
    jump_sizes: List[int]     # Jump table (32 integers)
    dp_mask: int              # Distinguished point mask
    ops_limit: int = 1_000_000

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, s: str) -> "Work":
        return cls(**json.loads(s))


@dataclass
class Result:
    """
    Result from Worker.

    Contains distinguished points found during walk.
    """
    job_id: str
    worker_id: str
    distinguished_points: List[Tuple[str, int]]  # (point_hex, distance)
    operations: int
    elapsed_ms: int
    final_point_hex: str
    final_distance: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, s: str) -> "Result":
        return cls(**json.loads(s))


@dataclass
class Heartbeat:
    """
    Periodic heartbeat from Worker.
    """
    worker_id: str
    backend: str
    ops_per_second: int
    total_ops: int
    total_dps: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class WorkerInfo:
    """
    Worker capability announcement.
    """
    worker_id: str
    platform: str
    backend: str
    ops_per_second: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))
