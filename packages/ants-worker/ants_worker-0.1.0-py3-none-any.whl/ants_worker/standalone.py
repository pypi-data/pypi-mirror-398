"""
Standalone mode - run without Agentverse.

For testing and local GPU machines that just crunch numbers.
Reports results via HTTP to a simple endpoint.
"""

import time
import json
import random
import hashlib
from typing import Optional, Callable
from dataclasses import asdict
from urllib.request import Request, urlopen
from urllib.error import URLError

from ants_worker.config import Config
from ants_worker.core import Worker, Work, Result, Point, G
from ants_worker.core.crypto import multiply, JumpTable


class StandaloneRunner:
    """
    Run worker without Agentverse.

    Generates its own work, reports to HTTP endpoint.
    Good for testing and simple deployments.
    """

    def __init__(
        self,
        worker: Worker,
        config: Optional[Config] = None,
        report_url: Optional[str] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        self.worker = worker
        self.config = config or Config.load()
        self.report_url = report_url or "http://localhost:8000/results"
        self.on_status = on_status or print

        # Default work parameters
        self.dp_mask = (1 << self.config.dp_bits) - 1
        self.ops_per_batch = 100_000
        self.jump_table = JumpTable(num_jumps=32, mean_jump=2**25)

    def generate_work(self) -> Work:
        """Generate random work package."""
        # Random starting point
        k = random.randint(1, 2**64)
        start_point = multiply(G, k)

        return Work(
            job_id=hashlib.sha256(f"{time.time()}-{k}".encode()).hexdigest()[:16],
            start_point_hex=start_point.to_hex(),
            start_distance=0,
            jump_sizes=self.jump_table.to_list(),
            dp_mask=self.dp_mask,
            ops_limit=self.ops_per_batch,
        )

    def report_result(self, result: Result) -> bool:
        """Report result to HTTP endpoint."""
        try:
            data = json.dumps(asdict(result)).encode()
            req = Request(
                self.report_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except URLError:
            return False  # Endpoint not available, continue anyway

    def run(self, max_batches: int = 0):
        """
        Run standalone worker.

        Args:
            max_batches: 0 = run forever
        """
        self.on_status(f"Worker {self.worker.worker_id} starting standalone mode")
        self.on_status(f"Backend: {self.worker.backend.name if self.worker.backend else 'python'}")
        self.on_status(f"Report URL: {self.report_url}")
        self.on_status("")

        batch = 0
        total_ops = 0
        total_dps = 0
        start_time = time.time()

        try:
            while max_batches == 0 or batch < max_batches:
                # Generate and process work
                work = self.generate_work()
                result = self.worker.process(work)

                # Update stats
                batch += 1
                total_ops += result.operations
                total_dps += len(result.distinguished_points)

                # Report (fire and forget)
                if result.distinguished_points:
                    self.report_result(result)

                # Status update every 10 batches
                if batch % 10 == 0:
                    elapsed = time.time() - start_time
                    ops_per_sec = int(total_ops / elapsed) if elapsed > 0 else 0
                    self.on_status(
                        f"Batch {batch}: {total_ops:,} ops, "
                        f"{total_dps} DPs, "
                        f"{ops_per_sec:,} ops/s"
                    )

        except KeyboardInterrupt:
            self.on_status("\nShutting down...")

        elapsed = time.time() - start_time
        self.on_status(f"\nTotal: {total_ops:,} ops in {elapsed:.1f}s")
        self.on_status(f"Distinguished points: {total_dps}")


def run_standalone(
    config: Optional[Config] = None,
    report_url: Optional[str] = None,
    on_status: Optional[Callable[[str], None]] = None,
):
    """Quick standalone runner."""
    from ants_worker.plugins import auto_detect_compute

    compute = auto_detect_compute()
    worker = Worker(compute_backend=compute)

    runner = StandaloneRunner(
        worker=worker,
        config=config,
        report_url=report_url,
        on_status=on_status,
    )
    runner.run()
