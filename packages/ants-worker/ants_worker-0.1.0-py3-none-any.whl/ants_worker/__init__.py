"""
Ants Worker - Distributed compute for the colony.

Install: pip install ants-worker
Run: ants-worker start
"""

__version__ = "0.1.0"

from ants_worker.config import Config
from ants_worker.core import Worker, Point, G, Work, Result

__all__ = ["Config", "Worker", "Point", "G", "Work", "Result", "__version__"]
