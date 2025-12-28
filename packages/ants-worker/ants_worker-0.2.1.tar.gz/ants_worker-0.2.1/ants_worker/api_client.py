"""
API Client - Connect to Gateway instead of TypeDB directly.

Workers use this to interact with the colony without seeing database credentials.

Usage:
    from ants_worker.api_client import GatewayClient
    
    client = GatewayClient(
        gateway_url="https://gateway.ants.work",
        token="your-worker-token",
    )
    
    regions = await client.get_regions()
"""

import os
import time
import httpx
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Region:
    id: str
    start: str
    end: str
    pheromone_trail: float
    pheromone_working: float


@dataclass
class Target:
    pubkey: str
    puzzle_level: int
    address: str


@dataclass
class DistinguishedPoint:
    hash: str
    point_hex: str
    distance: str
    worker_type: str
    region_id: str
    timestamp: float = 0.0


@dataclass
class Collision:
    tame_hash: str
    tame_distance: str
    wild_hash: str
    wild_distance: str


class GatewayClient:
    """
    Client for the Ants Gateway API.
    
    Replaces direct TypeDB connection for workers.
    """
    
    def __init__(
        self,
        gateway_url: str = None,
        token: str = None,
        timeout: float = 30.0,
    ):
        self.gateway_url = (
            gateway_url or 
            os.environ.get("GATEWAY_URL", "http://localhost:8000")
        ).rstrip("/")
        
        self.token = token or os.environ.get("GATEWAY_TOKEN")
        if not self.token:
            raise ValueError("GATEWAY_TOKEN not set")
        
        self.timeout = timeout
        self._client = None
    
    async def connect(self):
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.gateway_url,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=self.timeout,
        )
        
        # Verify connection
        response = await self._client.get("/health")
        if response.status_code != 200:
            raise ConnectionError(f"Gateway health check failed: {response.text}")
        
        data = response.json()
        if not data.get("connected"):
            print(f"[yellow]Gateway connected but database unavailable[/yellow]")
        else:
            print(f"[green]Connected to Gateway: {self.gateway_url}[/green]")
    
    async def disconnect(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
    
    # ===== SENSE =====
    
    async def sense_cold_regions(self, limit: int = 50) -> List[Region]:
        """Get regions with low pheromone."""
        response = await self._client.get(f"/regions?limit={limit}")
        response.raise_for_status()
        
        return [
            Region(
                id=r["region_id"],
                start=r["start"],
                end=r["end"],
                pheromone_trail=r["pheromone_trail"],
                pheromone_working=r["pheromone_working"],
            )
            for r in response.json()
        ]
    
    async def sense_target(self) -> Optional[str]:
        """Get target public key."""
        response = await self._client.get("/target")
        response.raise_for_status()
        
        data = response.json()
        if data:
            return data["pubkey"]
        return None
    
    async def sense_collision(self) -> Optional[tuple]:
        """Check for collision."""
        response = await self._client.get("/collision")
        response.raise_for_status()
        
        data = response.json()
        if data:
            return (
                DistinguishedPoint(
                    hash=data["tame_hash"],
                    point_hex="",
                    distance=data["tame_distance"],
                    worker_type="tame",
                    region_id="",
                ),
                DistinguishedPoint(
                    hash=data["wild_hash"],
                    point_hex="",
                    distance=data["wild_distance"],
                    worker_type="wild",
                    region_id="",
                ),
            )
        return None
    
    # ===== DEPOSIT =====
    
    async def deposit_intention(self, region_id: str, strength: float = 1.0):
        """Mark intention pheromone."""
        response = await self._client.post(
            "/intention",
            json={"region_id": region_id, "strength": strength},
        )
        response.raise_for_status()
    
    async def deposit_exploration(self, region_id: str, amount: float = 1.0):
        """Mark exploration pheromone."""
        response = await self._client.post(
            "/exploration",
            json={"region_id": region_id, "amount": amount},
        )
        response.raise_for_status()
    
    async def deposit_distinguished_point(self, dp: DistinguishedPoint):
        """Deposit a distinguished point."""
        response = await self._client.post(
            "/dp",
            json={
                "hash": dp.hash,
                "point_hex": dp.point_hex,
                "distance": str(dp.distance),
                "worker_type": dp.worker_type,
                "region_id": dp.region_id,
            },
        )
        response.raise_for_status()
    
    async def deposit_solution(self, private_key: int):
        """
        Handle solution found.

        SECURITY: Never log or transmit the private key!
        This should trigger local sweep only.
        """
        # SECURITY: Do NOT print or log the private key
        # The key should be used locally for immediate sweep
        print("[green]SOLUTION FOUND![/green]")
        print("[yellow]SWEEP FUNDS IMMEDIATELY - Key in memory only[/yellow]")
        # TODO: Implement local sweep via private mempool
        # NEVER send private_key over network or store in database


class GatewayEnvironment:
    """
    Environment interface using Gateway API.
    
    Drop-in replacement for EnvironmentInterface.
    """
    
    def __init__(
        self,
        gateway_url: str = None,
        token: str = None,
    ):
        self._client = GatewayClient(gateway_url=gateway_url, token=token)
        self._use_mock = False
    
    async def connect(self):
        try:
            await self._client.connect()
        except Exception as e:
            print(f"[dim]Gateway unavailable ({e}), using mock[/dim]")
            self._use_mock = True
    
    async def disconnect(self):
        await self._client.disconnect()
    
    # Proxy all methods to client
    async def sense_cold_regions(self, limit: int = 100):
        if self._use_mock:
            from ants_worker.stigmergic import MockEnvironment
            return MockEnvironment().sense_cold_regions(limit)
        return await self._client.sense_cold_regions(limit)
    
    async def sense_target(self):
        if self._use_mock:
            return None
        return await self._client.sense_target()
    
    async def sense_collision(self):
        if self._use_mock:
            return None
        return await self._client.sense_collision()
    
    async def deposit_intention(self, region_id: str, strength: float = 1.0):
        if self._use_mock:
            return
        await self._client.deposit_intention(region_id, strength)
    
    async def deposit_exploration(self, region_id: str, amount: float = 1.0):
        if self._use_mock:
            return
        await self._client.deposit_exploration(region_id, amount)
    
    async def deposit_distinguished_point(self, dp):
        if self._use_mock:
            return
        await self._client.deposit_distinguished_point(dp)
    
    async def deposit_solution(self, private_key: int):
        if self._use_mock:
            return
        await self._client.deposit_solution(private_key)
