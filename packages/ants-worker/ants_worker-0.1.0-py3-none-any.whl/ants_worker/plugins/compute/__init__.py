"""
Compute plugins - backends for EC point math.

Priority order:
  1. kangaroo (200) - JeanLucPons binary, 1B+ ops/sec
  2. cuda (100) - CuPy, needs real kernels
  3. cpu (0) - Pure Python fallback
"""

from ants_worker.plugins.compute.cpu import CPUPlugin

# Import optional plugins (they register themselves if available)
try:
    from ants_worker.plugins.compute.kangaroo_bin import KangarooBinaryPlugin
except ImportError:
    pass

try:
    from ants_worker.plugins.compute.cuda import CUDAPlugin
except ImportError:
    pass

__all__ = ["CPUPlugin"]
