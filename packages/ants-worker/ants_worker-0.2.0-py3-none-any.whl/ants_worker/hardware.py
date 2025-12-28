"""
Hardware detection utilities for ants-worker.

Detects:
  - CPU: Intel, AMD (including Ryzen AI)
  - GPU: NVIDIA CUDA, AMD ROCm, Apple Metal
  - NPU: AMD XDNA, Intel NPU, Apple Neural Engine

Provides detailed hardware info for optimal backend selection.
"""

import os
import platform
import subprocess
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class AcceleratorType(Enum):
    NONE = "none"
    CUDA = "cuda"           # NVIDIA GPU
    ROCM = "rocm"           # AMD GPU (ROCm/HIP)
    METAL = "metal"         # Apple GPU
    XDNA = "xdna"           # AMD NPU
    INTEL_NPU = "intel_npu" # Intel NPU
    ANE = "ane"             # Apple Neural Engine


@dataclass
class CPUInfo:
    """CPU information."""
    name: str = "Unknown"
    vendor: str = "Unknown"
    cores: int = 1
    threads: int = 1
    architecture: str = "Unknown"
    is_ryzen_ai: bool = False
    ryzen_ai_model: Optional[str] = None

    @classmethod
    def detect(cls) -> "CPUInfo":
        """Detect CPU information."""
        info = cls()
        info.architecture = platform.machine()
        info.cores = os.cpu_count() or 1
        info.threads = info.cores  # Simplified

        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    for line in cpuinfo.split("\n"):
                        if line.startswith("model name"):
                            info.name = line.split(":")[1].strip()
                            break
                        elif line.startswith("vendor_id"):
                            info.vendor = line.split(":")[1].strip()

                # Check for Ryzen AI
                name_lower = info.name.lower()
                if "ryzen" in name_lower:
                    info.vendor = "AMD"
                    if "ai" in name_lower or "max" in name_lower:
                        info.is_ryzen_ai = True
                        # Extract model
                        if "max 395" in name_lower:
                            info.ryzen_ai_model = "Max 395"
                        elif "max 385" in name_lower:
                            info.ryzen_ai_model = "Max 385"
                        elif "9 hx 370" in name_lower:
                            info.ryzen_ai_model = "9 HX 370"

            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    info.name = result.stdout.strip()
                    if "Apple" in info.name:
                        info.vendor = "Apple"
                    elif "Intel" in info.name:
                        info.vendor = "Intel"

            elif platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        info.name = lines[1].strip()
                        if "AMD" in info.name:
                            info.vendor = "AMD"
                            if "Ryzen" in info.name and ("AI" in info.name or "Max" in info.name):
                                info.is_ryzen_ai = True
                        elif "Intel" in info.name:
                            info.vendor = "Intel"

        except Exception:
            pass

        return info


@dataclass
class GPUInfo:
    """GPU information."""
    name: str = "Unknown"
    vendor: str = "Unknown"
    memory_gb: float = 0.0
    accelerator_type: AcceleratorType = AcceleratorType.NONE
    device_id: int = 0
    compute_capability: Optional[str] = None

    @classmethod
    def detect_all(cls) -> List["GPUInfo"]:
        """Detect all available GPUs."""
        gpus = []

        # Check NVIDIA CUDA
        try:
            import torch
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    name = torch.cuda.get_device_name(i)
                    props = torch.cuda.get_device_properties(i)
                    gpu = cls(
                        name=name,
                        vendor="NVIDIA" if "AMD" not in name.upper() else "AMD",
                        memory_gb=props.total_memory / (1024**3),
                        accelerator_type=AcceleratorType.CUDA if "AMD" not in name.upper() else AcceleratorType.ROCM,
                        device_id=i,
                        compute_capability=f"{props.major}.{props.minor}",
                    )
                    gpus.append(gpu)
        except ImportError:
            pass

        # Check CuPy CUDA
        if not gpus:
            try:
                import cupy as cp
                count = cp.cuda.runtime.getDeviceCount()
                for i in range(count):
                    props = cp.cuda.runtime.getDeviceProperties(i)
                    gpu = cls(
                        name=props["name"].decode(),
                        vendor="NVIDIA",
                        memory_gb=props["totalGlobalMem"] / (1024**3),
                        accelerator_type=AcceleratorType.CUDA,
                        device_id=i,
                    )
                    gpus.append(gpu)
            except ImportError:
                pass

        # Check AMD via PyOpenCL
        if not gpus:
            try:
                import pyopencl as cl
                for platform in cl.get_platforms():
                    if "AMD" in platform.name.upper():
                        for i, device in enumerate(platform.get_devices(device_type=cl.device_type.GPU)):
                            gpu = cls(
                                name=device.name,
                                vendor="AMD",
                                memory_gb=device.global_mem_size / (1024**3),
                                accelerator_type=AcceleratorType.ROCM,
                                device_id=i,
                            )
                            gpus.append(gpu)
            except ImportError:
                pass

        # Check Apple Metal
        if platform.system() == "Darwin" and not gpus:
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True, text=True
                )
                if "Apple" in result.stdout or "M1" in result.stdout or "M2" in result.stdout or "M3" in result.stdout:
                    gpu = cls(
                        name="Apple Silicon GPU",
                        vendor="Apple",
                        accelerator_type=AcceleratorType.METAL,
                    )
                    gpus.append(gpu)
            except Exception:
                pass

        return gpus


@dataclass
class NPUInfo:
    """NPU (Neural Processing Unit) information."""
    name: str = "Unknown"
    vendor: str = "Unknown"
    tops: int = 0  # Tera Operations Per Second
    accelerator_type: AcceleratorType = AcceleratorType.NONE
    available: bool = False

    @classmethod
    def detect(cls) -> Optional["NPUInfo"]:
        """Detect NPU availability."""
        # Check AMD XDNA (Ryzen AI)
        cpu = CPUInfo.detect()
        if cpu.is_ryzen_ai:
            # Check for NPU driver
            npu_available = False

            if platform.system() == "Linux":
                npu_available = (
                    os.path.exists("/dev/accel0") or
                    os.path.exists("/dev/amdxdna") or
                    os.path.exists("/sys/class/accel")
                )
            elif platform.system() == "Windows":
                # Check DirectML NPU
                try:
                    import onnxruntime as ort
                    if "DmlExecutionProvider" in ort.get_available_providers():
                        npu_available = True
                except ImportError:
                    pass

            if npu_available or cpu.is_ryzen_ai:
                # Estimate TOPS based on model
                tops_map = {
                    "Max 395": 126,
                    "Max 385": 77,
                    "9 HX 370": 50,
                }
                tops = tops_map.get(cpu.ryzen_ai_model, 16)

                return cls(
                    name=f"AMD XDNA NPU ({cpu.ryzen_ai_model or 'Ryzen AI'})",
                    vendor="AMD",
                    tops=tops,
                    accelerator_type=AcceleratorType.XDNA,
                    available=npu_available,
                )

        # Check Apple Neural Engine
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "hw.optional.arm64"],
                    capture_output=True, text=True
                )
                if result.returncode == 0 and "1" in result.stdout:
                    return cls(
                        name="Apple Neural Engine",
                        vendor="Apple",
                        tops=15,  # Approximate for M1/M2
                        accelerator_type=AcceleratorType.ANE,
                        available=True,
                    )
            except Exception:
                pass

        return None


@dataclass
class HardwareInfo:
    """Complete hardware information."""
    cpu: CPUInfo = field(default_factory=CPUInfo)
    gpus: List[GPUInfo] = field(default_factory=list)
    npu: Optional[NPUInfo] = None
    memory_gb: float = 0.0
    unified_memory: bool = False

    @classmethod
    def detect(cls) -> "HardwareInfo":
        """Detect all hardware."""
        info = cls()
        info.cpu = CPUInfo.detect()
        info.gpus = GPUInfo.detect_all()
        info.npu = NPUInfo.detect()

        # Detect memory
        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal"):
                            kb = int(line.split()[1])
                            info.memory_gb = kb / (1024**2)
                            break
            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    info.memory_gb = int(result.stdout.strip()) / (1024**3)
                    # Apple Silicon has unified memory
                    if info.cpu.vendor == "Apple":
                        info.unified_memory = True
            elif platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "computersystem", "get", "totalphysicalmemory"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        info.memory_gb = int(lines[1].strip()) / (1024**3)
        except Exception:
            pass

        # Check for unified memory (Ryzen AI Max has it)
        if info.cpu.is_ryzen_ai and info.cpu.ryzen_ai_model and "Max" in info.cpu.ryzen_ai_model:
            info.unified_memory = True

        return info

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu": {
                "name": self.cpu.name,
                "vendor": self.cpu.vendor,
                "cores": self.cpu.cores,
                "architecture": self.cpu.architecture,
                "is_ryzen_ai": self.cpu.is_ryzen_ai,
                "ryzen_ai_model": self.cpu.ryzen_ai_model,
            },
            "gpus": [
                {
                    "name": gpu.name,
                    "vendor": gpu.vendor,
                    "memory_gb": gpu.memory_gb,
                    "type": gpu.accelerator_type.value,
                }
                for gpu in self.gpus
            ],
            "npu": {
                "name": self.npu.name,
                "vendor": self.npu.vendor,
                "tops": self.npu.tops,
                "type": self.npu.accelerator_type.value,
                "available": self.npu.available,
            } if self.npu else None,
            "memory_gb": self.memory_gb,
            "unified_memory": self.unified_memory,
        }

    def recommend_backend(self) -> str:
        """Recommend best compute backend."""
        # Priority: Kangaroo binary > CUDA > ROCm > Metal > NPU > Parallel CPU > CPU

        # Check for Kangaroo binary
        kangaroo_bin = os.environ.get("KANGAROO_BIN")
        if kangaroo_bin and os.path.exists(kangaroo_bin):
            return "kangaroo"

        # Check GPUs
        for gpu in self.gpus:
            if gpu.accelerator_type == AcceleratorType.CUDA:
                return "cuda"
            if gpu.accelerator_type == AcceleratorType.ROCM:
                return "amd_rocm"
            if gpu.accelerator_type == AcceleratorType.METAL:
                return "metal"

        # Check NPU (experimental)
        if self.npu and self.npu.available and self.npu.tops >= 50:
            return "amd_npu"

        # Parallel CPU for many-core systems
        if self.cpu.cores >= 8:
            return "parallel_cpu"

        return "cpu"

    def recommend_workers(self) -> int:
        """Recommend number of parallel workers."""
        # For GPU, usually 1-2 workers per GPU
        if self.gpus:
            return max(1, len(self.gpus) * 2)

        # For NPU + CPU combo, use both
        if self.npu and self.npu.available:
            return self.cpu.cores

        # For CPU only, use all cores
        return self.cpu.cores


def detect_hardware() -> HardwareInfo:
    """Convenience function to detect hardware."""
    return HardwareInfo.detect()


def print_hardware_info():
    """Print hardware info to console."""
    info = detect_hardware()

    print(f"\n{'='*50}")
    print("HARDWARE DETECTION")
    print(f"{'='*50}\n")

    print(f"CPU: {info.cpu.name}")
    print(f"  Vendor: {info.cpu.vendor}")
    print(f"  Cores: {info.cpu.cores}")
    if info.cpu.is_ryzen_ai:
        print(f"  Ryzen AI: {info.cpu.ryzen_ai_model}")

    print(f"\nMemory: {info.memory_gb:.1f} GB")
    if info.unified_memory:
        print("  Type: Unified Memory Architecture")

    if info.gpus:
        print("\nGPUs:")
        for gpu in info.gpus:
            print(f"  [{gpu.device_id}] {gpu.name}")
            print(f"      Memory: {gpu.memory_gb:.1f} GB")
            print(f"      Type: {gpu.accelerator_type.value}")

    if info.npu:
        print(f"\nNPU: {info.npu.name}")
        print(f"  Performance: {info.npu.tops} TOPS")
        print(f"  Available: {info.npu.available}")

    print(f"\nRecommended Backend: {info.recommend_backend()}")
    print(f"Recommended Workers: {info.recommend_workers()}")
    print()


if __name__ == "__main__":
    print_hardware_info()
