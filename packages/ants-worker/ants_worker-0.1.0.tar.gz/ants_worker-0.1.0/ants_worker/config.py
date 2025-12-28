"""
Configuration management for ants-worker.

Loads from ~/.ants/config.json or environment variables.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Default gateway
DEFAULT_GATEWAY = "https://api.ants-at-work.com"


@dataclass
class Config:
    """Worker configuration."""

    # Gateway settings (primary)
    gateway_url: str = DEFAULT_GATEWAY
    gateway_token: Optional[str] = None
    worker_id: Optional[str] = None

    # Queen agent address (legacy/Agentverse)
    queen: str = "agent1qf8y7rmu6z5eftzw8m4xmk964enuh3096ezn8cfs6j2rzkxtwcynzzkv3mk"

    # Worker wallet for rewards
    wallet: Optional[str] = None

    # Compute settings
    gpu: str = "auto"  # auto | true | false
    threads: int = 0  # 0 = all available

    # Logging
    verbose: bool = False

    # Distinguished point mask (2^20 = ~1M points between DPs)
    dp_bits: int = 20

    @classmethod
    def config_path(cls) -> Path:
        """Get config file path."""
        return Path.home() / ".ants" / "config.json"

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load config from file and environment."""
        config = cls()

        # Try default path
        if path is None:
            path = cls.config_path()

        # Load from JSON if exists
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            except json.JSONDecodeError:
                pass

        # Environment overrides
        if gateway_url := os.environ.get("GATEWAY_URL"):
            config.gateway_url = gateway_url
        if gateway_token := os.environ.get("GATEWAY_TOKEN"):
            config.gateway_token = gateway_token
        if queen := os.environ.get("ANTS_QUEEN"):
            config.queen = queen
        if wallet := os.environ.get("ANTS_WALLET"):
            config.wallet = wallet
        if gpu := os.environ.get("ANTS_GPU"):
            config.gpu = gpu
        if threads := os.environ.get("ANTS_THREADS"):
            config.threads = int(threads)
        if verbose := os.environ.get("ANTS_VERBOSE"):
            config.verbose = verbose.lower() in ("1", "true", "yes")

        return config

    def save(self, path: Optional[Path] = None) -> None:
        """Save config to file."""
        if path is None:
            path = self.config_path()

        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "gateway_url": self.gateway_url,
            "gateway_token": self.gateway_token,
            "worker_id": self.worker_id,
            "queen": self.queen,
            "wallet": self.wallet,
            "gpu": self.gpu,
            "threads": self.threads,
            "verbose": self.verbose,
            "dp_bits": self.dp_bits,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @property
    def dp_mask(self) -> int:
        """Distinguished point mask."""
        return (1 << self.dp_bits) - 1

    @property
    def is_registered(self) -> bool:
        """Check if worker has registered with gateway."""
        return self.gateway_token is not None
