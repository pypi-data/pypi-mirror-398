"""
Compute plugins - backends for EC point math.

Priority order:
  1. kangaroo (200) - JeanLucPons binary, 1B+ ops/sec
  2. cuda (100) - NVIDIA GPU via CuPy
  3. amd_rocm (90) - AMD GPU via ROCm/HIP
  4. amd_npu (85) - AMD XDNA NPU (Ryzen AI)
  5. parallel_cpu (40) - Multi-threaded CPU
  6. cpu (0) - Pure Python fallback
"""

from ants_worker.plugins.compute.cpu import CPUPlugin

# Import optional plugins (they register themselves if available)

# Kangaroo binary (highest priority)
try:
    from ants_worker.plugins.compute.kangaroo_bin import KangarooBinaryPlugin
except ImportError:
    pass

# NVIDIA CUDA
try:
    from ants_worker.plugins.compute.cuda import CUDAPlugin
except ImportError:
    pass

# AMD ROCm/HIP GPU
try:
    from ants_worker.plugins.compute.amd_rocm import AMDROCmPlugin
except ImportError:
    pass

# AMD XDNA NPU (Ryzen AI)
try:
    from ants_worker.plugins.compute.amd_npu import AMDNPUPlugin, ParallelCPUPlugin
except ImportError:
    pass

# Apple Metal
try:
    from ants_worker.plugins.compute.metal import MetalPlugin
except ImportError:
    pass

__all__ = ["CPUPlugin"]
