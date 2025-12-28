"""
Local Cloud Plugin - Run workers on local machine.

Good for testing and office machines.
"""

import os
import sys
import subprocess
import uuid
from typing import List, Dict
from pathlib import Path

from ants_worker.plugins.registry import CloudPlugin, register_cloud


@register_cloud
class LocalPlugin(CloudPlugin):
    """
    Run workers as local processes.

    Uses subprocess to spawn worker processes.
    """

    def __init__(self):
        self._processes: Dict[str, subprocess.Popen] = {}

    @property
    def name(self) -> str:
        return "local"

    @classmethod
    def is_configured(cls) -> bool:
        return True  # Always available

    def launch(self, count: int = 1, gpu: bool = True) -> List[str]:
        """Launch local worker processes."""
        instance_ids = []

        for _ in range(count):
            instance_id = f"local-{uuid.uuid4().hex[:8]}"

            cmd = [
                sys.executable, "-m", "ants_worker.cli",
                "start",
            ]
            if gpu:
                cmd.append("--gpu")

            # Start in background
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            self._processes[instance_id] = proc
            instance_ids.append(instance_id)

        return instance_ids

    def terminate(self, instance_ids: List[str]) -> None:
        """Terminate local processes."""
        for iid in instance_ids:
            if iid in self._processes:
                proc = self._processes[iid]
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                del self._processes[iid]

    def list_instances(self) -> List[dict]:
        """List running local instances."""
        instances = []
        dead = []

        for iid, proc in self._processes.items():
            poll = proc.poll()
            if poll is None:
                instances.append({
                    "id": iid,
                    "status": "running",
                    "pid": proc.pid,
                })
            else:
                dead.append(iid)

        # Clean up dead processes
        for iid in dead:
            del self._processes[iid]

        return instances

    def get_cost_per_hour(self, gpu: bool = True) -> float:
        """Local is free (electricity only)."""
        return 0.0

    def info(self) -> dict:
        return {
            "name": self.name,
            "running": len(self._processes),
        }
