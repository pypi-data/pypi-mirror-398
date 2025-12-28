"""
Ants Worker - Distributed compute for the colony.

Install: pip install ants-worker
Run: ants-worker join

Supports:
  - NVIDIA CUDA (cupy)
  - AMD ROCm/HIP (torch, pyopencl)
  - AMD XDNA NPU (Ryzen AI)
  - Apple Metal
  - Multi-core CPU

For AMD Ryzen AI systems:
  ants-worker join --workers 16
  ants-worker info --detailed
"""

__version__ = "0.2.1"

from ants_worker.config import Config
from ants_worker.core import Worker, Point, G, Work, Result

__all__ = ["Config", "Worker", "Point", "G", "Work", "Result", "__version__"]
