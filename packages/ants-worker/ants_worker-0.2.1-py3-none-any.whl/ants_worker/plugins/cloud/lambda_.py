"""
Lambda Labs Cloud Plugin - Enterprise GPU cloud.

Requires: LAMBDA_API_KEY environment variable
Good for H100s and reliable infrastructure.
"""

import os
import json
from typing import List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from ants_worker.plugins.registry import CloudPlugin, register_cloud


API_BASE = "https://cloud.lambdalabs.com/api/v1"


def _lambda_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make Lambda API request."""
    api_key = os.environ.get("LAMBDA_API_KEY")
    if not api_key:
        raise RuntimeError("LAMBDA_API_KEY not set")

    url = f"{API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"Lambda API error: {e.code} - {error_body}")


@register_cloud
class LambdaPlugin(CloudPlugin):
    """
    Lambda Labs GPU cloud.

    Reliable, good for H100s. ~$2/hr for H100.
    """

    DEFAULT_INSTANCE_TYPE = "gpu_1x_a100"  # or gpu_1x_h100_sxm5

    def __init__(self):
        self._ssh_key_name: Optional[str] = os.environ.get("LAMBDA_SSH_KEY")

    @property
    def name(self) -> str:
        return "lambda"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(os.environ.get("LAMBDA_API_KEY"))

    def list_instance_types(self) -> List[dict]:
        """List available instance types."""
        result = _lambda_request("instance-types")
        types = result.get("data", {})
        return [
            {
                "name": name,
                "gpu": info.get("instance_type", {}).get("gpu_description"),
                "price_per_hour": info.get("instance_type", {}).get("price_cents_per_hour", 0) / 100,
                "available": len(info.get("regions_with_capacity_available", [])) > 0,
            }
            for name, info in types.items()
        ]

    def launch(self, count: int = 1, gpu: bool = True) -> List[str]:
        """Launch Lambda instances."""
        instance_ids = []

        if not self._ssh_key_name:
            # List SSH keys
            keys = _lambda_request("ssh-keys").get("data", [])
            if keys:
                self._ssh_key_name = keys[0].get("name")
            else:
                raise RuntimeError("No SSH keys found. Add one at cloud.lambdalabs.com")

        for _ in range(count):
            data = {
                "instance_type_name": self.DEFAULT_INSTANCE_TYPE,
                "ssh_key_names": [self._ssh_key_name],
                "quantity": 1,
            }

            result = _lambda_request("instance-operations/launch", "POST", data)
            ids = result.get("data", {}).get("instance_ids", [])
            instance_ids.extend([f"lambda-{iid}" for iid in ids])

        return instance_ids

    def terminate(self, instance_ids: List[str]) -> None:
        """Terminate Lambda instances."""
        ids = [iid.replace("lambda-", "") for iid in instance_ids]
        if ids:
            _lambda_request(
                "instance-operations/terminate",
                "POST",
                {"instance_ids": ids}
            )

    def list_instances(self) -> List[dict]:
        """List running Lambda instances."""
        result = _lambda_request("instances")
        instances = result.get("data", [])
        return [
            {
                "id": f"lambda-{inst.get('id')}",
                "status": inst.get("status"),
                "type": inst.get("instance_type", {}).get("name"),
                "ip": inst.get("ip"),
            }
            for inst in instances
        ]

    def get_cost_per_hour(self, gpu: bool = True) -> float:
        """Get cost per hour."""
        types = self.list_instance_types()
        for t in types:
            if t["name"] == self.DEFAULT_INSTANCE_TYPE:
                return t["price_per_hour"]
        return 2.0  # Default H100 estimate

    def info(self) -> dict:
        instances = self.list_instances() if self.is_configured() else []
        return {
            "name": self.name,
            "configured": self.is_configured(),
            "running_instances": len(instances),
        }
