"""
Plugin registry - discovers and loads plugins.
"""

from typing import Dict, Optional, Type, List
from abc import ABC, abstractmethod

# Plugin registries
_compute_plugins: Dict[str, Type["ComputePlugin"]] = {}
_cloud_plugins: Dict[str, Type["CloudPlugin"]] = {}


class ComputePlugin(ABC):
    """
    Base class for compute plugins.

    Implement this to add a new compute backend (CPU, CUDA, Metal, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name (e.g., 'cpu', 'cuda', 'metal')."""
        pass

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if this backend is available on this system."""
        pass

    @classmethod
    def priority(cls) -> int:
        """Priority for auto-detection (higher = preferred). Default 0."""
        return 0

    @abstractmethod
    def walk(
        self,
        start_point: "Point",
        start_distance: int,
        jump_table: "JumpTable",
        dp_mask: int,
        max_ops: int,
    ) -> "WalkResult":
        """Perform kangaroo walk."""
        pass

    def info(self) -> dict:
        """Get backend info."""
        return {"name": self.name}


class CloudPlugin(ABC):
    """
    Base class for cloud plugins.

    Implement this to add a new cloud provider (Vast.ai, Lambda, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name (e.g., 'vastai', 'lambda', 'local')."""
        pass

    @classmethod
    @abstractmethod
    def is_configured(cls) -> bool:
        """Check if this provider is configured (API keys, etc.)."""
        pass

    @abstractmethod
    def launch(self, count: int = 1, gpu: bool = True) -> List[str]:
        """
        Launch worker instances.

        Returns list of instance IDs.
        """
        pass

    @abstractmethod
    def terminate(self, instance_ids: List[str]) -> None:
        """Terminate instances."""
        pass

    @abstractmethod
    def list_instances(self) -> List[dict]:
        """List running instances."""
        pass

    @abstractmethod
    def get_cost_per_hour(self, gpu: bool = True) -> float:
        """Get cost per hour in USD."""
        pass


def register_compute(plugin_class: Type[ComputePlugin]) -> Type[ComputePlugin]:
    """Register a compute plugin."""
    instance = plugin_class()
    _compute_plugins[instance.name] = plugin_class
    return plugin_class


def register_cloud(plugin_class: Type[CloudPlugin]) -> Type[CloudPlugin]:
    """Register a cloud plugin."""
    instance = plugin_class()
    _cloud_plugins[instance.name] = plugin_class
    return plugin_class


def get_compute(name: str) -> Optional[ComputePlugin]:
    """Get compute plugin by name."""
    if name in _compute_plugins:
        return _compute_plugins[name]()
    return None


def get_cloud(name: str) -> Optional[CloudPlugin]:
    """Get cloud plugin by name."""
    if name in _cloud_plugins:
        return _cloud_plugins[name]()
    return None


def list_compute() -> List[dict]:
    """List all compute plugins."""
    result = []
    for name, cls in _compute_plugins.items():
        result.append({
            "name": name,
            "available": cls.is_available(),
            "priority": cls.priority(),
        })
    return sorted(result, key=lambda x: -x["priority"])


def list_cloud() -> List[dict]:
    """List all cloud plugins."""
    result = []
    for name, cls in _cloud_plugins.items():
        result.append({
            "name": name,
            "configured": cls.is_configured(),
        })
    return result


def auto_detect_compute() -> Optional[ComputePlugin]:
    """Auto-detect best available compute backend."""
    available = [
        (cls.priority(), cls)
        for cls in _compute_plugins.values()
        if cls.is_available()
    ]
    if not available:
        return None

    # Sort by priority (highest first)
    available.sort(key=lambda x: -x[0])
    return available[0][1]()


def load_builtin_plugins():
    """Load built-in plugins."""
    # Import triggers registration via decorators
    from ants_worker.plugins.compute import cpu

    # GPU/Accelerator plugins (priority order: kangaroo > cuda > amd_rocm > amd_npu > metal)
    try:
        from ants_worker.plugins.compute import kangaroo_bin
    except ImportError:
        pass  # Kangaroo binary not installed
    try:
        from ants_worker.plugins.compute import cuda
    except ImportError:
        pass  # CUDA not available
    try:
        from ants_worker.plugins.compute import amd_rocm
    except ImportError:
        pass  # AMD ROCm not available
    try:
        from ants_worker.plugins.compute import amd_npu
    except ImportError:
        pass  # AMD NPU not available
    try:
        from ants_worker.plugins.compute import metal
    except ImportError:
        pass  # Metal not available

    # Cloud plugins
    from ants_worker.plugins.cloud import local
    try:
        from ants_worker.plugins.cloud import vastai
    except ImportError:
        pass
    try:
        from ants_worker.plugins.cloud import lambda_
    except ImportError:
        pass


# Load plugins on import
load_builtin_plugins()
