"""
CLI for ants-worker.

Usage:
    ants-worker start              # Start worker
    ants-worker info               # Show system info
    ants-worker benchmark          # Run benchmark
    ants-worker plugins            # List plugins
    ants-worker cloud launch       # Launch cloud workers
    ants-worker cloud list         # List running workers
    ants-worker cloud terminate    # Terminate workers
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ants_worker import __version__
from ants_worker.config import Config

console = Console()


@click.group()
@click.version_option(version=__version__)
def main():
    """Ants Worker - Distributed compute for the colony."""
    pass


@main.command()
@click.option("--type", "-t", "worker_type", default="tame", help="Worker type: tame or wild")
@click.option("--workers", "-w", default=0, help="Number of parallel workers (0=auto)")
@click.option("--backend", "-b", default=None, help="Compute backend (cpu, cuda, amd_rocm, amd_npu)")
def join(worker_type, workers, backend):
    """
    Join the colony. Auto-registers and starts working.

    \b
    This is the easiest way to contribute:
      pip install ants-worker
      ants-worker join

    \b
    For AMD Ryzen AI systems:
      ants-worker join --workers 16  # Use all cores
      ants-worker join -b amd_npu    # Force NPU backend

    Your API key is saved to ~/.ants/config.json
    """
    import platform
    import asyncio
    import httpx

    config = Config.load()

    # Check if already registered
    if not config.is_registered:
        console.print("[cyan]Registering with colony...[/cyan]")

        # Collect system info
        hostname = platform.node()
        plat = f"{platform.system()} {platform.release()}"

        # Try to detect GPU
        gpu_info = "unknown"
        try:
            from ants_worker.plugins import auto_detect_compute
            compute = auto_detect_compute()
            if compute and compute.name != "cpu":
                gpu_info = compute.name
        except Exception:
            pass

        # Register with gateway
        try:
            resp = httpx.post(
                f"{config.gateway_url}/register",
                json={
                    "hostname": hostname,
                    "platform": plat,
                    "gpu": gpu_info,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            config.gateway_token = data["token"]
            config.worker_id = data["worker_id"]
            config.save()

            console.print(f"[green]Registered![/green] Worker ID: {data['worker_id']}")
            console.print(f"[dim]Config saved to {Config.config_path()}[/dim]")

        except httpx.RequestError as e:
            console.print(f"[red]Failed to register: {e}[/red]")
            console.print(f"[dim]Gateway: {config.gateway_url}[/dim]")
            return
        except httpx.HTTPStatusError as e:
            console.print(f"[red]Registration failed: {e.response.text}[/red]")
            return

    else:
        console.print(f"[green]Already registered[/green] as {config.worker_id}")

    # Detect hardware and set optimal workers
    num_workers = workers
    selected_backend = backend

    if num_workers == 0 or not selected_backend:
        try:
            from ants_worker.hardware import detect_hardware
            hw = detect_hardware()
            if num_workers == 0:
                num_workers = hw.recommend_workers()
            if not selected_backend:
                selected_backend = hw.recommend_backend()

            if hw.cpu.is_ryzen_ai:
                console.print(f"[bold cyan]Detected: AMD {hw.cpu.ryzen_ai_model}[/bold cyan]")
                if hw.npu:
                    console.print(f"[cyan]NPU: {hw.npu.tops} TOPS[/cyan]")
                if hw.unified_memory:
                    console.print(f"[cyan]Memory: {hw.memory_gb:.0f}GB Unified[/cyan]")
        except ImportError:
            num_workers = 1
            selected_backend = "cpu"

    # Now start working
    console.print(Panel.fit(
        f"[bold green]Joining Colony[/bold green]\n"
        f"Worker: {config.worker_id}\n"
        f"Type: {worker_type}\n"
        f"Backend: {selected_backend}\n"
        f"Parallel Workers: {num_workers}\n"
        f"Gateway: {config.gateway_url}",
        border_style="green",
    ))
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    from ants_worker.api_client import GatewayEnvironment
    from ants_worker.stigmergic import StigmergicWorker, WorkerType
    from ants_worker.plugins import get_compute

    async def run():
        env = GatewayEnvironment(
            gateway_url=config.gateway_url,
            token=config.gateway_token,
        )
        await env.connect()

        # Get compute backend
        compute = get_compute(selected_backend) if selected_backend else None

        wtype = WorkerType.TAME if worker_type == "tame" else WorkerType.WILD
        worker = StigmergicWorker(
            worker_type=wtype,
            environment=env,
            on_status=console.print,
            compute_backend=compute,
            num_workers=num_workers,
        )

        try:
            await worker.run(max_cycles=0)
        finally:
            await env.disconnect()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Leaving colony...[/yellow]")


@main.command()
def status():
    """Show your worker status and contribution stats."""
    import httpx

    config = Config.load()

    if not config.is_registered:
        console.print("[yellow]Not registered yet.[/yellow]")
        console.print("Run: ants-worker join")
        return

    table = Table(title="Worker Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Worker ID", config.worker_id or "unknown")
    table.add_row("Gateway", config.gateway_url)
    table.add_row("Config", str(Config.config_path()))

    # Try to get stats from gateway
    try:
        resp = httpx.get(
            f"{config.gateway_url}/health",
            headers={"Authorization": f"Bearer {config.gateway_token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            table.add_row("Connection", "[green]OK[/green]")
        else:
            table.add_row("Connection", "[yellow]Degraded[/yellow]")
    except Exception:
        table.add_row("Connection", "[red]Failed[/red]")

    console.print(table)


@main.command()
def leave():
    """Unregister from the colony and delete local config."""
    config = Config.load()

    if not config.is_registered:
        console.print("[yellow]Not registered.[/yellow]")
        return

    config_path = Config.config_path()
    if config_path.exists():
        config_path.unlink()
        console.print(f"[green]Left the colony.[/green] Deleted {config_path}")
    else:
        console.print("[yellow]Config file not found.[/yellow]")


@main.command()
@click.option("--gpu/--cpu-only", default=None, help="Force GPU or CPU mode")
@click.option("--backend", "-b", help="Specific backend (cpu, cuda, metal)")
@click.option("--threads", "-t", default=0, help="CPU threads (0=all)")
@click.option("--daemon", "-d", is_flag=True, help="Run in background")
@click.option("--queen", "-q", help="Queen agent address")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def start(gpu, backend, threads, daemon, queen, verbose):
    """Start the worker and connect to Queen (legacy Agentverse mode)."""
    from ants_worker.plugins import auto_detect_compute, get_compute
    from ants_worker.core import Worker

    config = Config.load()

    # Apply CLI overrides
    if gpu is not None:
        config.gpu = "true" if gpu else "false"
    if threads:
        config.threads = threads
    if queen:
        config.queen = queen
    if verbose:
        config.verbose = verbose

    # Show startup banner
    console.print(Panel.fit(
        f"[bold green]Ants Worker v{__version__}[/bold green]\n"
        f"Joining the swarm...",
        border_style="green",
    ))

    # Get compute backend
    if backend:
        compute = get_compute(backend)
        if not compute:
            console.print(f"[red]Unknown backend: {backend}[/red]")
            return
    else:
        compute = auto_detect_compute()

    if compute:
        console.print(f"Backend: [cyan]{compute.name}[/cyan]")
    else:
        console.print("Backend: [yellow]python (fallback)[/yellow]")

    console.print(f"Queen: [dim]{config.queen[:20]}...[/dim]")

    if daemon:
        console.print("[yellow]Daemon mode not yet implemented[/yellow]")
        return

    # Create worker
    worker = Worker(compute_backend=compute)

    # Start agent connection
    try:
        from ants_worker.agent import create_worker
        agent = create_worker(
            config=config,
            worker=worker,
            on_status=lambda m: console.print(f"[dim]{m}[/dim]") if verbose else None,
        )
        console.print("[green]Connected. Waiting for work...[/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        agent.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            raise


@main.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed hardware info")
def info(detailed):
    """Show system and backend info."""
    import platform
    import os
    from ants_worker.plugins import list_compute, list_cloud

    if detailed:
        # Use full hardware detection
        try:
            from ants_worker.hardware import detect_hardware
            hw = detect_hardware()

            # CPU Info
            cpu_table = Table(title="CPU")
            cpu_table.add_column("Property", style="cyan")
            cpu_table.add_column("Value", style="green")
            cpu_table.add_row("Name", hw.cpu.name)
            cpu_table.add_row("Vendor", hw.cpu.vendor)
            cpu_table.add_row("Cores", str(hw.cpu.cores))
            cpu_table.add_row("Architecture", hw.cpu.architecture)
            if hw.cpu.is_ryzen_ai:
                cpu_table.add_row("Ryzen AI", f"[bold green]{hw.cpu.ryzen_ai_model}[/bold green]")
            console.print(cpu_table)

            # Memory
            mem_table = Table(title="Memory")
            mem_table.add_column("Property", style="cyan")
            mem_table.add_column("Value", style="green")
            mem_table.add_row("Total", f"{hw.memory_gb:.1f} GB")
            mem_table.add_row("Type", "[bold green]Unified[/bold green]" if hw.unified_memory else "Standard")
            console.print(mem_table)

            # GPUs
            if hw.gpus:
                gpu_table = Table(title="GPUs")
                gpu_table.add_column("ID", style="cyan")
                gpu_table.add_column("Name", style="green")
                gpu_table.add_column("Memory", style="yellow")
                gpu_table.add_column("Type", style="magenta")
                for gpu in hw.gpus:
                    gpu_table.add_row(
                        str(gpu.device_id),
                        gpu.name,
                        f"{gpu.memory_gb:.1f} GB",
                        gpu.accelerator_type.value,
                    )
                console.print(gpu_table)

            # NPU
            if hw.npu:
                npu_table = Table(title="NPU (Neural Processing Unit)")
                npu_table.add_column("Property", style="cyan")
                npu_table.add_column("Value", style="green")
                npu_table.add_row("Name", hw.npu.name)
                npu_table.add_row("Performance", f"[bold green]{hw.npu.tops} TOPS[/bold green]")
                npu_table.add_row("Available", "[green]Yes[/green]" if hw.npu.available else "[yellow]Driver needed[/yellow]")
                console.print(npu_table)

            # Recommendations
            rec_table = Table(title="Recommendations")
            rec_table.add_column("Property", style="cyan")
            rec_table.add_column("Value", style="green")
            rec_table.add_row("Best Backend", f"[bold]{hw.recommend_backend()}[/bold]")
            rec_table.add_row("Optimal Workers", str(hw.recommend_workers()))
            console.print(rec_table)

        except ImportError as e:
            console.print(f"[yellow]Hardware detection not available: {e}[/yellow]")

    else:
        # Basic system info
        table = Table(title="System Info")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Platform", platform.system())
        table.add_row("Architecture", platform.machine())
        table.add_row("CPU Cores", str(os.cpu_count()))
        table.add_row("Python", platform.python_version())

        console.print(table)

    # Compute plugins
    compute_table = Table(title="Compute Backends")
    compute_table.add_column("Name", style="cyan")
    compute_table.add_column("Available", style="green")
    compute_table.add_column("Priority", style="yellow")

    for plugin in list_compute():
        avail = "[green]Yes[/green]" if plugin["available"] else "[red]No[/red]"
        compute_table.add_row(
            plugin["name"],
            avail,
            str(plugin["priority"]),
        )

    console.print(compute_table)

    # Cloud plugins
    cloud_table = Table(title="Cloud Providers")
    cloud_table.add_column("Name", style="cyan")
    cloud_table.add_column("Configured", style="green")

    for plugin in list_cloud():
        cloud_table.add_row(
            plugin["name"],
            "Yes" if plugin["configured"] else "No",
        )

    console.print(cloud_table)


@main.command()
def plugins():
    """List available plugins."""
    from ants_worker.plugins import list_compute, list_cloud

    console.print("[bold]Compute Plugins[/bold]")
    for p in list_compute():
        status = "[green]available[/green]" if p["available"] else "[red]unavailable[/red]"
        console.print(f"  {p['name']}: {status} (priority {p['priority']})")

    console.print("\n[bold]Cloud Plugins[/bold]")
    for p in list_cloud():
        status = "[green]configured[/green]" if p["configured"] else "[yellow]not configured[/yellow]"
        console.print(f"  {p['name']}: {status}")


@main.command()
@click.option("--duration", "-d", default=5, help="Benchmark duration (seconds)")
@click.option("--backend", "-b", help="Specific backend to test")
def benchmark(duration, backend):
    """Run performance benchmark."""
    from ants_worker.plugins import auto_detect_compute, get_compute
    from ants_worker.core import Worker

    console.print(f"[cyan]Running benchmark for {duration}s...[/cyan]")

    # Get backend
    if backend:
        compute = get_compute(backend)
    else:
        compute = auto_detect_compute()

    worker = Worker(compute_backend=compute)
    results = worker.benchmark(duration_secs=duration)

    table = Table(title="Benchmark Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Backend", results["backend"])
    table.add_row("Duration", f"{results['duration_secs']}s")
    table.add_row("Operations", f"{results['total_operations']:,}")
    table.add_row("Ops/Second", f"{results['ops_per_second']:,}")
    table.add_row("Distinguished Points", f"{results['distinguished_points']:,}")

    console.print(table)

    # Performance assessment
    ops = results["ops_per_second"]
    if ops > 100_000_000:
        rating = "[bold green]Excellent (GPU)[/bold green]"
    elif ops > 10_000_000:
        rating = "[green]Great[/green]"
    elif ops > 1_000_000:
        rating = "[yellow]Good[/yellow]"
    else:
        rating = "[red]Slow (consider GPU)[/red]"

    console.print(f"\nPerformance: {rating}")


# Cloud commands group
@main.group()
def cloud():
    """Manage cloud workers."""
    pass


@cloud.command("list")
@click.option("--provider", "-p", help="Specific provider (vastai, lambda, local)")
def cloud_list(provider):
    """List running cloud instances."""
    from ants_worker.plugins import list_cloud, get_cloud

    if provider:
        providers = [provider]
    else:
        providers = [p["name"] for p in list_cloud() if p["configured"]]

    if not providers:
        console.print("[yellow]No cloud providers configured[/yellow]")
        return

    for pname in providers:
        plugin = get_cloud(pname)
        if not plugin:
            continue

        instances = plugin.list_instances()
        if not instances:
            console.print(f"[dim]{pname}: no instances[/dim]")
            continue

        table = Table(title=f"{pname.upper()} Instances")
        table.add_column("ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        for inst in instances:
            details = []
            if "gpu" in inst:
                details.append(inst["gpu"])
            if "cost_per_hour" in inst:
                details.append(f"${inst['cost_per_hour']:.2f}/hr")
            table.add_row(
                inst["id"],
                inst.get("status", "unknown"),
                " | ".join(details) if details else "-",
            )

        console.print(table)


@cloud.command("launch")
@click.argument("provider")
@click.option("--count", "-n", default=1, help="Number of instances")
@click.option("--gpu/--no-gpu", default=True, help="Request GPU instances")
def cloud_launch(provider, count, gpu):
    """Launch cloud workers."""
    from ants_worker.plugins import get_cloud

    plugin = get_cloud(provider)
    if not plugin:
        console.print(f"[red]Unknown provider: {provider}[/red]")
        console.print("Available: local, vastai, lambda")
        return

    if not plugin.is_configured():
        console.print(f"[red]{provider} is not configured[/red]")
        if provider == "vastai":
            console.print("Run: vastai set api-key YOUR_KEY")
        elif provider == "lambda":
            console.print("Set: export LAMBDA_API_KEY=your_key")
        return

    console.print(f"[cyan]Launching {count} worker(s) on {provider}...[/cyan]")

    try:
        instance_ids = plugin.launch(count=count, gpu=gpu)
        console.print(f"[green]Launched {len(instance_ids)} instance(s):[/green]")
        for iid in instance_ids:
            console.print(f"  {iid}")

        cost = plugin.get_cost_per_hour(gpu=gpu) * len(instance_ids)
        console.print(f"\n[yellow]Estimated cost: ${cost:.2f}/hour[/yellow]")

    except Exception as e:
        console.print(f"[red]Launch failed: {e}[/red]")


@cloud.command("terminate")
@click.argument("instance_ids", nargs=-1)
@click.option("--provider", "-p", help="Provider (required if ID doesn't include prefix)")
@click.option("--all", "terminate_all", is_flag=True, help="Terminate all instances")
def cloud_terminate(instance_ids, provider, terminate_all):
    """Terminate cloud instances."""
    from ants_worker.plugins import get_cloud, list_cloud

    if terminate_all:
        # Terminate all across all providers
        for p in list_cloud():
            if p["configured"]:
                plugin = get_cloud(p["name"])
                instances = plugin.list_instances()
                if instances:
                    ids = [i["id"] for i in instances]
                    plugin.terminate(ids)
                    console.print(f"[yellow]Terminated {len(ids)} on {p['name']}[/yellow]")
        return

    if not instance_ids:
        console.print("[red]Specify instance IDs or use --all[/red]")
        return

    # Group by provider
    by_provider = {}
    for iid in instance_ids:
        # Detect provider from prefix
        if iid.startswith("vast-"):
            pname = "vastai"
        elif iid.startswith("lambda-"):
            pname = "lambda"
        elif iid.startswith("local-"):
            pname = "local"
        elif provider:
            pname = provider
        else:
            console.print(f"[red]Can't detect provider for {iid}, use --provider[/red]")
            continue

        if pname not in by_provider:
            by_provider[pname] = []
        by_provider[pname].append(iid)

    # Terminate
    for pname, ids in by_provider.items():
        plugin = get_cloud(pname)
        if plugin:
            plugin.terminate(ids)
            console.print(f"[yellow]Terminated {len(ids)} on {pname}[/yellow]")


@cloud.command("cost")
def cloud_cost():
    """Show cloud cost estimates."""
    from ants_worker.plugins import list_cloud, get_cloud

    table = Table(title="Cloud Cost Estimates")
    table.add_column("Provider", style="cyan")
    table.add_column("GPU $/hr", style="green")
    table.add_column("CPU $/hr", style="yellow")
    table.add_column("Running", style="magenta")

    for p in list_cloud():
        if not p["configured"]:
            continue

        plugin = get_cloud(p["name"])
        instances = plugin.list_instances()

        table.add_row(
            p["name"],
            f"${plugin.get_cost_per_hour(gpu=True):.2f}",
            f"${plugin.get_cost_per_hour(gpu=False):.2f}",
            str(len(instances)),
        )

    console.print(table)


@main.command()
@click.option("--batches", "-n", default=0, help="Number of batches (0=forever)")
@click.option("--report-url", "-r", help="URL to report results")
def standalone(batches, report_url):
    """Run in standalone mode (no Agentverse)."""
    from ants_worker.plugins import auto_detect_compute
    from ants_worker.core import Worker
    from ants_worker.standalone import StandaloneRunner

    compute = auto_detect_compute()
    worker = Worker(compute_backend=compute)

    runner = StandaloneRunner(
        worker=worker,
        report_url=report_url,
        on_status=console.print,
    )
    runner.run(max_batches=batches)


@main.command()
@click.option("--type", "-t", "worker_type", default="tame", help="Worker type: tame or wild")
@click.option("--cycles", "-n", default=0, help="Number of cycles (0=forever)")
@click.option("--db-url", default="https://cr0mc4-0.cluster.typedb.com:80", help="TypeDB address")
@click.option("--database", default="ants-colony", help="Database name")
def stigmergic(worker_type, cycles, db_url, database):
    """
    Run in stigmergic mode - sense environment, decide locally, deposit results.

    No coordinator. No commands. Intelligence emerges.

    \b
    The worker will:
      1. SENSE cold regions (low pheromone)
      2. DECIDE which region to explore (probabilistic)
      3. MARK intention ("I'm working here")
      4. WORK (kangaroo jumps)
      5. DEPOSIT distinguished points
      6. MARK explored (strengthen pheromone)
      7. CHECK for collisions
      8. REPEAT
    """
    import asyncio
    from ants_worker.stigmergic import run_stigmergic

    console.print(Panel.fit(
        f"[bold green]Stigmergic Mode[/bold green]\n"
        f"Type: {worker_type}\n"
        f"No coordinator. Sensing environment directly.",
        border_style="green",
    ))

    console.print(f"[dim]Database: {db_url}/{database}[/dim]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]\n")

    try:
        asyncio.run(run_stigmergic(
            worker_type=worker_type,
            db_url=db_url,
            database=database,
            max_cycles=cycles,
            on_status=console.print,
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")


@main.command()
@click.option("--type", "-t", "worker_type", default="tame", help="Worker type: tame or wild")
@click.option("--cycles", "-n", default=0, help="Number of cycles (0=forever)")
@click.option("--gateway", "-g", default=None, help="Gateway URL (default: GATEWAY_URL env)")
@click.option("--token", default=None, help="Worker token (default: GATEWAY_TOKEN env)")
def gateway(worker_type, cycles, gateway, token):
    """
    Run via Gateway (SECURE) - workers never see database credentials.

    \b
    Requires:
      - GATEWAY_URL or --gateway: Gateway server address
      - GATEWAY_TOKEN or --token: Your worker token

    \b
    Example:
      export GATEWAY_URL=https://gateway.ants.work
      export GATEWAY_TOKEN=your-token-here
      ants-worker gateway -t tame
    """
    import os
    import asyncio
    from ants_worker.api_client import GatewayEnvironment
    from ants_worker.stigmergic import StigmergicWorker, WorkerType

    gateway_url = gateway or os.environ.get("GATEWAY_URL")
    worker_token = token or os.environ.get("GATEWAY_TOKEN")

    if not gateway_url:
        console.print("[red]Error: GATEWAY_URL not set[/red]")
        console.print("Set environment variable or use --gateway option")
        return

    if not worker_token:
        console.print("[red]Error: GATEWAY_TOKEN not set[/red]")
        console.print("Set environment variable or use --token option")
        return

    console.print(Panel.fit(
        f"[bold cyan]Gateway Mode (Secure)[/bold cyan]\n"
        f"Type: {worker_type}\n"
        f"Gateway: {gateway_url}\n"
        f"Token: {worker_token[:8]}...",
        border_style="cyan",
    ))
    console.print(f"[dim]Press Ctrl+C to stop[/dim]\n")

    async def run():
        env = GatewayEnvironment(gateway_url=gateway_url, token=worker_token)
        await env.connect()

        wtype = WorkerType.TAME if worker_type == "tame" else WorkerType.WILD
        worker = StigmergicWorker(
            worker_type=wtype,
            environment=env,
            on_status=console.print,
        )

        try:
            await worker.run(max_cycles=cycles)
        finally:
            await env.disconnect()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")


@main.command()
@click.option("--set", "set_values", nargs=2, multiple=True, help="Set config value")
@click.option("--show", is_flag=True, help="Show current config")
def config(set_values, show):
    """View or edit configuration."""
    cfg = Config.load()

    if set_values:
        for key, value in set_values:
            if hasattr(cfg, key):
                current = getattr(cfg, key)
                if isinstance(current, bool):
                    value = value.lower() in ("true", "1", "yes")
                elif isinstance(current, int):
                    value = int(value)
                setattr(cfg, key, value)
                console.print(f"Set {key} = {value}")
            else:
                console.print(f"[red]Unknown config key: {key}[/red]")

        cfg.save()
        console.print("[green]Config saved[/green]")

    if show or not set_values:
        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("queen", cfg.queen[:40] + "...")
        table.add_row("wallet", cfg.wallet or "(not set)")
        table.add_row("gpu", cfg.gpu)
        table.add_row("threads", str(cfg.threads))
        table.add_row("verbose", str(cfg.verbose))
        table.add_row("dp_bits", str(cfg.dp_bits))

        console.print(table)


if __name__ == "__main__":
    main()
