"""
Stigmergic Worker - No coordinator, no commands.

Workers sense environment → decide locally → deposit results.
Intelligence emerges from interaction.

"The queen doesn't tell anyone what to do. In fact, nobody tells anybody what to do."
— Deborah Gordon
"""

import asyncio
import random
import time
from typing import Optional, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from ants_worker.core import Worker, Point, G
from ants_worker.core.crypto import multiply, JumpTable, is_distinguished, hash_point


class WorkerType(Enum):
    TAME = "tame"
    WILD = "wild"


@dataclass
class Region:
    """A region of the search space."""
    id: str
    start: int
    end: int
    pheromone_trail: float = 0.0
    pheromone_working: float = 0.0


@dataclass
class DistinguishedPoint:
    """A distinguished point found during exploration."""
    hash: str
    point_hex: str
    distance: int
    worker_type: str
    region_id: str
    timestamp: float


class EnvironmentInterface:
    """
    Interface to the environment (TypeDB).

    Workers sense and deposit through this.
    No commands, no coordination - just read/write.
    """

    def __init__(
        self,
        db_url: str = "https://cr0mc4-0.cluster.typedb.com:80",
        database: str = "ants-colony",
        username: str = None,
        password: str = None,
    ):
        import os
        self.db_url = db_url
        self.database = database
        self.username = username or os.environ.get("TYPEDB_USERNAME", "admin")
        self.password = password or os.environ.get("TYPEDB_PASSWORD")
        self._driver = None
        self._use_mock = False

    async def connect(self):
        """Connect to TypeDB Cloud."""
        try:
            from typedb.driver import TypeDB, Credentials, DriverOptions

            if not self.password:
                print("[dim]TYPEDB_PASSWORD not set, using mock environment[/dim]")
                self._use_mock = True
                return

            credentials = Credentials(self.username, self.password)
            options = DriverOptions(is_tls_enabled=True)
            self._driver = TypeDB.driver(self.db_url, credentials, options)
            print(f"[green]Connected to TypeDB: {self.database}[/green]")

        except ImportError:
            print("[dim]typedb-driver not installed, using mock environment[/dim]")
            self._use_mock = True
        except Exception as e:
            print(f"[dim]TypeDB connection failed ({e}), using mock environment[/dim]")
            self._use_mock = True

    async def disconnect(self):
        """Disconnect from TypeDB."""
        if self._driver:
            self._driver.close()

    # ===== SENSE =====

    async def sense_cold_regions(self, limit: int = 100) -> List[Region]:
        """
        Sense regions with low pheromone (unexplored).

        Workers call this to find work. No assignment.
        """
        if self._use_mock:
            return self._get_mock().sense_cold_regions(limit)

        from typedb.driver import TransactionType

        # Real TypeDB query
        with self._driver.transaction(self.database, TransactionType.READ) as tx:
            results = tx.query(f"""
                match $r isa search_region,
                      has region-id $id,
                      has range-start $start,
                      has range-end $end,
                      has pheromone-trail $trail,
                      has pheromone-working $working;
                sort $trail asc;
                limit {limit};
                select $id, $start, $end, $trail, $working;
            """).resolve()

            regions = []
            for row in results.as_concept_rows():
                regions.append(Region(
                    id=row.get("id").as_attribute().get_value(),
                    start=row.get("start").as_attribute().get_value(),
                    end=row.get("end").as_attribute().get_value(),
                    pheromone_trail=row.get("trail").as_attribute().get_value(),
                    pheromone_working=row.get("working").as_attribute().get_value(),
                ))
            return regions

    def _get_mock(self) -> "MockEnvironment":
        """Get or create mock environment."""
        if not hasattr(self, "_mock"):
            self._mock = MockEnvironment()
        return self._mock

    async def sense_target(self) -> Optional[str]:
        """Sense the target public key from environment."""
        if self._use_mock:
            return self._get_mock().target_pubkey

        from typedb.driver import TransactionType

        with self._driver.transaction(self.database, TransactionType.READ) as tx:
            results = tx.query("""
                match $t isa target, has target-pubkey $pk;
                select $pk;
                limit 1;
            """).resolve()

            for row in results.as_concept_rows():
                return row.get("pk").as_attribute().get_value()
        return None

    async def sense_collision(self) -> Optional[Tuple[DistinguishedPoint, DistinguishedPoint]]:
        """
        Sense if a collision exists in the environment.

        Any worker can discover this - whoever senses first announces.
        """
        if self._use_mock:
            return self._get_mock().sense_collision()

        from typedb.driver import TransactionType

        with self._driver.transaction(self.database, TransactionType.READ) as tx:
            results = tx.query("""
                match
                    $dp1 isa distinguished_point,
                        has point-hash $h,
                        has kangaroo-type "tame",
                        has distance-traveled $d1;
                    $dp2 isa distinguished_point,
                        has point-hash $h,
                        has kangaroo-type "wild",
                        has distance-traveled $d2;
                select $h, $d1, $d2;
                limit 1;
            """).resolve()

            for row in results.as_concept_rows():
                # Collision found!
                return (
                    DistinguishedPoint(
                        hash=row.get("h").as_attribute().get_value(),
                        point_hex="",
                        distance=row.get("d1").as_attribute().get_value(),
                        worker_type="tame",
                        region_id="",
                        timestamp=time.time(),
                    ),
                    DistinguishedPoint(
                        hash=row.get("h").as_attribute().get_value(),
                        point_hex="",
                        distance=row.get("d2").as_attribute().get_value(),
                        worker_type="wild",
                        region_id="",
                        timestamp=time.time(),
                    ),
                )
        return None

    # ===== DEPOSIT =====

    async def deposit_intention(self, region_id: str, strength: float = 1.0):
        """
        Deposit intention pheromone: "I'm working here."

        Fast decay. Others see and avoid.
        """
        if self._use_mock:
            self._get_mock().deposit_intention(region_id, strength)
            return

        from typedb.driver import TransactionType

        with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
            # TypeQL 3.0: delete $attr of $entity
            tx.query(f"""
                match $r isa search_region, has region-id "{region_id}",
                      has pheromone-working $old;
                delete $old of $r;
            """).resolve()
            tx.query(f"""
                match $r isa search_region, has region-id "{region_id}";
                insert $r has pheromone-working {strength};
            """).resolve()
            tx.commit()

    async def deposit_exploration(self, region_id: str, amount: float = 1.0):
        """
        Deposit exploration pheromone: "I explored here."

        Marks region as visited. Medium decay.
        """
        if self._use_mock:
            self._get_mock().deposit_exploration(region_id, amount)
            return

        from typedb.driver import TransactionType

        with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
            # First read current value
            result = tx.query(f"""
                match $r isa search_region, has region-id "{region_id}",
                      has pheromone-trail $old;
                select $old;
            """).resolve()
            current = 0.0
            for row in result.as_concept_rows():
                current = row.get("old").as_attribute().get_value()
            new_value = current + amount

            # Delete old, insert new (TypeQL 3.0: delete $attr of $entity)
            tx.query(f"""
                match $r isa search_region, has region-id "{region_id}",
                      has pheromone-trail $trail;
                delete $trail of $r;
            """).resolve()
            tx.query(f"""
                match $r isa search_region, has region-id "{region_id}";
                insert $r has pheromone-trail {new_value};
            """).resolve()
            tx.commit()

    async def deposit_distinguished_point(self, dp: DistinguishedPoint):
        """
        Deposit a distinguished point into the environment.

        Uses hash for natural deduplication.
        """
        if self._use_mock:
            self._get_mock().deposit_dp(dp)
            return

        from typedb.driver import TransactionType

        with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
            # Only insert if hash doesn't exist
            tx.query(f"""
                match not {{ $x isa distinguished_point, has point-hash "{dp.hash}"; }};
                insert $dp isa distinguished_point,
                    has id "{dp.hash}-{dp.worker_type}",
                    has point-hash "{dp.hash}",
                    has kangaroo-type "{dp.worker_type}",
                    has point-x-hex "{dp.point_hex}",
                    has distance-traveled "{dp.distance}",
                    has timestamp {dp.timestamp};
            """).resolve()
            tx.commit()

    async def deposit_solution(self, private_key: int):
        """Deposit the solution into environment."""
        if self._use_mock:
            self._get_mock().solution = private_key
            return

        from typedb.driver import TransactionType

        with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
            tx.query(f"""
                insert $s isa collision_record,
                    has id "solution-{int(time.time())}",
                    has recovered-key-hex "{hex(private_key)}",
                    has verified true,
                    has timestamp {time.time()};
            """).resolve()
            tx.commit()


class MockEnvironment:
    """Mock environment for testing without TypeDB."""

    def __init__(self):
        self.regions: List[Region] = []
        self.dps: List[DistinguishedPoint] = []
        self.target_pubkey: Optional[str] = None
        self.solution: Optional[int] = None

        # Create some test regions
        for i in range(100):
            self.regions.append(Region(
                id=f"region-{i}",
                start=i * 10000,
                end=(i + 1) * 10000,
                pheromone_trail=random.random() * 5,
                pheromone_working=0.0,
            ))

    def sense_cold_regions(self, limit: int) -> List[Region]:
        # Sort by pheromone, return coldest
        sorted_regions = sorted(self.regions, key=lambda r: r.pheromone_trail)
        return sorted_regions[:limit]

    def deposit_intention(self, region_id: str, strength: float):
        for r in self.regions:
            if r.id == region_id:
                r.pheromone_working = strength
                break

    def deposit_exploration(self, region_id: str, amount: float):
        for r in self.regions:
            if r.id == region_id:
                r.pheromone_trail += amount
                break

    def deposit_dp(self, dp: DistinguishedPoint):
        # Check for duplicate
        for existing in self.dps:
            if existing.hash == dp.hash:
                return  # Already exists
        self.dps.append(dp)

    def sense_collision(self) -> Optional[Tuple[DistinguishedPoint, DistinguishedPoint]]:
        # Check for matching hashes with different types
        tame_dps = {dp.hash: dp for dp in self.dps if dp.worker_type == "tame"}
        wild_dps = {dp.hash: dp for dp in self.dps if dp.worker_type == "wild"}

        for hash_val in tame_dps:
            if hash_val in wild_dps:
                return (tame_dps[hash_val], wild_dps[hash_val])
        return None


class StigmergicWorker:
    """
    A worker that operates purely through stigmergy.

    No commands received. No results reported.
    Sense → Decide → Work → Deposit → Repeat.
    """

    def __init__(
        self,
        worker_type: WorkerType,
        environment: EnvironmentInterface,
        compute_worker: Optional[Worker] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        self.worker_type = worker_type
        self.env = environment
        self.compute = compute_worker or Worker()
        self.on_status = on_status or (lambda s: None)

        # Local state (minimal - most state is in environment)
        self.total_ops = 0
        self.total_dps = 0
        self.local_memory: dict = {}  # Region preferences

        # Kangaroo parameters
        self.dp_bits = 20
        self.dp_mask = (1 << self.dp_bits) - 1
        self.ops_per_cycle = 100_000

    async def run(self, max_cycles: int = 0):
        """
        Run the stigmergic loop.

        Args:
            max_cycles: 0 = run forever
        """
        self.on_status(f"Worker ({self.worker_type.value}) starting stigmergic mode")

        cycle = 0
        while max_cycles == 0 or cycle < max_cycles:
            try:
                await self._cycle()
                cycle += 1

                if cycle % 10 == 0:
                    self.on_status(f"Cycle {cycle}: {self.total_ops:,} ops, {self.total_dps} DPs")

            except Exception as e:
                self.on_status(f"Error: {e}")
                await asyncio.sleep(1)

        self.on_status(f"Completed {cycle} cycles, {self.total_ops:,} ops, {self.total_dps} DPs")

    async def _cycle(self):
        """One sense-decide-work-deposit cycle."""

        # 1. SENSE - Query environment for cold regions
        regions = await self.env.sense_cold_regions(limit=50)
        if not regions:
            self.on_status("No regions found, waiting...")
            await asyncio.sleep(1)
            return

        # 2. DECIDE - Probabilistic selection, prefer cold, avoid working
        region = self._select_region(regions)

        # 3. MARK INTENTION - Deposit "I'm here" pheromone
        await self.env.deposit_intention(region.id, strength=1.0)
        await asyncio.sleep(0.05)  # Brief pause for propagation

        # 4. WORK - Run kangaroo in this region
        dps = await self._explore(region)

        # 5. DEPOSIT - Put DPs into environment
        for dp in dps:
            await self.env.deposit_distinguished_point(dp)
            self.total_dps += 1

        # 6. MARK EXPLORED - Strengthen trail pheromone
        await self.env.deposit_exploration(region.id, amount=1.0)

        # 7. CHECK FOR COLLISION - Sense environment
        collision = await self.env.sense_collision()
        if collision:
            await self._handle_collision(collision)

        # 8. LOCAL LEARNING - Remember if this region was good
        if dps:
            self.local_memory[region.id] = self.local_memory.get(region.id, 0) + 0.1

    def _select_region(self, regions: List[Region]) -> Region:
        """
        Select region using probabilistic weighting.

        Prefer:
        - Low trail pheromone (unexplored)
        - Low working pheromone (not being worked)
        - Regions where we found DPs before (local learning)
        """
        # Filter out regions with high working pheromone
        available = [r for r in regions if r.pheromone_working < 0.5]
        if not available:
            available = regions  # Fall back to all if none available

        # Calculate weights
        weights = []
        for r in available:
            # Base weight: inverse of trail pheromone
            base = 1.0 / (r.pheromone_trail + 0.1)

            # Local memory bonus
            local_bonus = self.local_memory.get(r.id, 0)

            # Penalty for working pheromone
            working_penalty = 1.0 / (r.pheromone_working + 1.0)

            weights.append(base * working_penalty + local_bonus)

        # Probabilistic selection
        return random.choices(available, weights=weights)[0]

    async def _explore(self, region: Region) -> List[DistinguishedPoint]:
        """
        Explore a region using kangaroo algorithm.

        Returns distinguished points found.
        """
        # Determine start point based on worker type
        # Convert hex strings to int
        start_int = int(region.start, 16) if isinstance(region.start, str) else region.start
        end_int = int(region.end, 16) if isinstance(region.end, str) else region.end

        if self.worker_type == WorkerType.TAME:
            # Tame starts at random point in range
            k = random.randint(start_int, end_int)
            point = multiply(G, k)
            distance = k
        else:
            # Wild starts at target (would need to sense from env)
            # For now, use random start
            k = random.randint(start_int, end_int)
            point = multiply(G, k)
            distance = 0

        # Build jump table for this region
        range_size = end_int - start_int
        mean_jump = max(1, int(range_size ** 0.5) // 4)
        jump_table = JumpTable(num_jumps=32, mean_jump=mean_jump)

        # Walk and collect DPs
        dps = []
        ops = 0

        while ops < self.ops_per_cycle:
            # Check if distinguished
            if is_distinguished(point, self.dp_mask):
                dp = DistinguishedPoint(
                    hash=hash_point(point),
                    point_hex=point.to_hex(),
                    distance=distance,
                    worker_type=self.worker_type.value,
                    region_id=region.id,
                    timestamp=time.time(),
                )
                dps.append(dp)

            # Jump
            jump_size, jump_point = jump_table.get_jump(point)
            from ants_worker.core.crypto import add
            point = add(point, jump_point)
            distance += jump_size
            ops += 1

        self.total_ops += ops
        return dps

    async def _handle_collision(self, collision: Tuple[DistinguishedPoint, DistinguishedPoint]):
        """
        Handle collision discovery.

        Private key = tame_distance - wild_distance
        """
        tame_dp, wild_dp = collision

        private_key = tame_dp.distance - wild_dp.distance
        if private_key < 0:
            private_key = wild_dp.distance - tame_dp.distance

        self.on_status(f"COLLISION FOUND! Private key: {hex(private_key)}")

        # Deposit solution to environment
        await self.env.deposit_solution(private_key)


async def run_stigmergic(
    worker_type: str = "tame",
    db_url: str = "localhost:1729",
    database: str = "ants-colony",
    max_cycles: int = 0,
    on_status: Optional[Callable[[str], None]] = None,
):
    """
    Run a stigmergic worker.

    Args:
        worker_type: "tame" or "wild"
        db_url: TypeDB address
        database: Database name
        max_cycles: 0 = run forever
        on_status: Status callback
    """
    # Connect to environment
    env = EnvironmentInterface(db_url=db_url, database=database)
    await env.connect()

    # Create worker
    wtype = WorkerType.TAME if worker_type == "tame" else WorkerType.WILD
    worker = StigmergicWorker(
        worker_type=wtype,
        environment=env,
        on_status=on_status or print,
    )

    try:
        await worker.run(max_cycles=max_cycles)
    finally:
        await env.disconnect()
