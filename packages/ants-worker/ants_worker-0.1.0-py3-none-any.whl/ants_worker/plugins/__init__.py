"""
Plugin system for ants-worker.

Compute plugins: CPU, CUDA, Metal, ROCm
Cloud plugins: local, vastai, lambda, runpod, aws
"""

from ants_worker.plugins.registry import (
    register_compute,
    register_cloud,
    get_compute,
    get_cloud,
    list_compute,
    list_cloud,
    auto_detect_compute,
)

__all__ = [
    "register_compute",
    "register_cloud",
    "get_compute",
    "get_cloud",
    "list_compute",
    "list_cloud",
    "auto_detect_compute",
]
