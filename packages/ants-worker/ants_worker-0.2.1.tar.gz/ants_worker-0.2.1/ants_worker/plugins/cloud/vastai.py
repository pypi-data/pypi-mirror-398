"""
Vast.ai Cloud Plugin - Cheap GPU rentals.

Requires: pip install vastai
Configure: vastai set api-key YOUR_KEY
"""

import os
import json
import subprocess
from typing import List, Optional

from ants_worker.plugins.registry import CloudPlugin, register_cloud


def _run_vastai(*args) -> dict:
    """Run vastai CLI command."""
    try:
        result = subprocess.run(
            ["vastai", *args, "--raw"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except FileNotFoundError:
        raise RuntimeError("vastai CLI not found. Install with: pip install vastai")
    except json.JSONDecodeError:
        return {"output": result.stdout}


@register_cloud
class VastaiPlugin(CloudPlugin):
    """
    Vast.ai GPU rental.

    Cheap P2P GPU marketplace. ~$0.20/hr for RTX 4090.
    """

    # Default search criteria
    DEFAULT_GPU = "RTX_4090"
    DEFAULT_IMAGE = "antsatwork/worker:latest"

    def __init__(self):
        self._api_key: Optional[str] = os.environ.get("VASTAI_API_KEY")

    @property
    def name(self) -> str:
        return "vastai"

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Vast.ai is configured."""
        # Check environment
        if os.environ.get("VASTAI_API_KEY"):
            return True

        # Check vastai config
        try:
            result = subprocess.run(
                ["vastai", "show", "user", "--raw"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def search_offers(
        self,
        gpu_name: str = DEFAULT_GPU,
        num_gpus: int = 1,
        min_ram: int = 16,
        max_price: float = 1.0,
    ) -> List[dict]:
        """Search for available GPU offers."""
        query = f"gpu_name={gpu_name} num_gpus={num_gpus} gpu_ram>={min_ram} dph<={max_price}"

        try:
            result = _run_vastai("search", "offers", query, "--order", "dph")
            return result if isinstance(result, list) else []
        except Exception as e:
            return []

    def launch(self, count: int = 1, gpu: bool = True) -> List[str]:
        """
        Launch Vast.ai instances.

        Finds cheapest matching offer and launches.
        """
        instance_ids = []

        # Find offers
        offers = self.search_offers(
            gpu_name=self.DEFAULT_GPU if gpu else "any",
        )

        if not offers:
            raise RuntimeError("No matching Vast.ai offers found")

        for i in range(count):
            if i >= len(offers):
                break

            offer = offers[i]
            offer_id = offer.get("id")

            # Launch instance
            result = _run_vastai(
                "create", "instance", str(offer_id),
                "--image", self.DEFAULT_IMAGE,
                "--disk", "10",
                "--onstart-cmd", "ants-worker start --gpu",
            )

            instance_id = result.get("new_contract")
            if instance_id:
                instance_ids.append(f"vast-{instance_id}")

        return instance_ids

    def terminate(self, instance_ids: List[str]) -> None:
        """Terminate Vast.ai instances."""
        for iid in instance_ids:
            # Extract contract ID
            contract_id = iid.replace("vast-", "")
            try:
                _run_vastai("destroy", "instance", contract_id)
            except Exception:
                pass  # Best effort

    def list_instances(self) -> List[dict]:
        """List running Vast.ai instances."""
        try:
            result = _run_vastai("show", "instances")
            instances = result if isinstance(result, list) else []
            return [
                {
                    "id": f"vast-{inst.get('id')}",
                    "status": inst.get("actual_status", "unknown"),
                    "gpu": inst.get("gpu_name"),
                    "cost_per_hour": inst.get("dph_total", 0),
                }
                for inst in instances
            ]
        except Exception:
            return []

    def get_cost_per_hour(self, gpu: bool = True) -> float:
        """Estimated cost per hour."""
        if not gpu:
            return 0.05  # CPU only

        # Check current market
        offers = self.search_offers(gpu_name=self.DEFAULT_GPU)
        if offers:
            return offers[0].get("dph_total", 0.30)
        return 0.30  # Default estimate

    def info(self) -> dict:
        instances = self.list_instances()
        total_cost = sum(i.get("cost_per_hour", 0) for i in instances)
        return {
            "name": self.name,
            "configured": self.is_configured(),
            "running_instances": len(instances),
            "cost_per_hour": total_cost,
        }
