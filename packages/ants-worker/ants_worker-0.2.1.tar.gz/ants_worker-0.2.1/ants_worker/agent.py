"""
Agent connection to Queen via Fetch.ai uAgents.

Receives work packages, sends results.
"""

import uuid
from typing import Optional, Callable

from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

from ants_worker.config import Config
from ants_worker.core import Worker, Work, Result, Point, JumpTable


# Message models for Agentverse protocol

class WorkAssignment(Model):
    """Work package from Queen."""
    job_id: str
    start_point_hex: str
    start_distance: int
    jump_sizes: list[int]
    dp_mask: int
    ops_limit: int


class WorkResultMsg(Model):
    """Result sent to Queen."""
    job_id: str
    worker_id: str
    distinguished_points: list[tuple[str, int]]
    operations: int
    elapsed_ms: int
    final_point_hex: str
    final_distance: int


class HeartbeatMsg(Model):
    """Periodic heartbeat to Queen."""
    worker_id: str
    backend: str
    total_ops: int
    total_dps: int
    ops_per_second: int


class WorkerAgent:
    """
    Worker agent that connects to Queen.

    Handles communication, delegates computation to Worker.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        worker: Optional[Worker] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        self.config = config or Config.load()
        self.on_status = on_status or (lambda s: None)

        # Use provided worker or create new one
        self.worker = worker or Worker()
        self.worker_id = self.worker.worker_id

        # Create uAgent
        self.agent = Agent(
            name=self.worker_id,
            seed=self.worker_id,
        )

        # Register handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up message handlers."""

        @self.agent.on_event("startup")
        async def on_startup(ctx: Context):
            self.on_status(f"Worker {self.worker_id} started")
            self.on_status(f"Address: {ctx.agent.address}")
            backend_name = self.worker.backend.name if self.worker.backend else "python"
            self.on_status(f"Backend: {backend_name}")

            # Fund if needed
            await fund_agent_if_low(ctx.agent.wallet.address())

        @self.agent.on_message(model=WorkAssignment)
        async def handle_work(ctx: Context, sender: str, msg: WorkAssignment):
            self.on_status(f"Received work: {msg.job_id}")

            # Convert to Work
            work = Work(
                job_id=msg.job_id,
                start_point_hex=msg.start_point_hex,
                start_distance=msg.start_distance,
                jump_sizes=msg.jump_sizes,
                dp_mask=msg.dp_mask,
                ops_limit=msg.ops_limit,
            )

            # Process
            result = self.worker.process(work)

            # Send result
            result_msg = WorkResultMsg(
                job_id=result.job_id,
                worker_id=result.worker_id,
                distinguished_points=result.distinguished_points,
                operations=result.operations,
                elapsed_ms=result.elapsed_ms,
                final_point_hex=result.final_point_hex,
                final_distance=result.final_distance,
            )

            await ctx.send(sender, result_msg)
            self.on_status(
                f"Completed {msg.job_id}: "
                f"{result.operations} ops, "
                f"{len(result.distinguished_points)} DPs"
            )

        @self.agent.on_interval(period=60.0)
        async def send_heartbeat(ctx: Context):
            """Send periodic heartbeat to Queen."""
            heartbeat = self.worker.heartbeat()

            msg = HeartbeatMsg(
                worker_id=heartbeat.worker_id,
                backend=heartbeat.backend,
                total_ops=heartbeat.total_ops,
                total_dps=heartbeat.total_dps,
                ops_per_second=heartbeat.ops_per_second,
            )

            await ctx.send(self.config.queen, msg)

    def run(self):
        """Run the agent (blocking)."""
        self.agent.run()

    async def run_async(self):
        """Run the agent (async)."""
        await self.agent.run_async()


def create_worker(
    config: Optional[Config] = None,
    worker: Optional[Worker] = None,
    on_status: Optional[Callable[[str], None]] = None,
) -> WorkerAgent:
    """Create a worker agent."""
    return WorkerAgent(config=config, worker=worker, on_status=on_status)
