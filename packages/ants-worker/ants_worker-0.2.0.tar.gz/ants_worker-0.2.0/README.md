# Ants Worker

Join the colony. Share your compute.

```bash
pip install ants-worker
ants-worker join
```

That's it. You're now part of the swarm.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           YOUR MACHINE                                   │
│                                                                          │
│   $ ants-worker join                                                    │
│                                                                          │
│   ┌──────────────┐                                                      │
│   │ ants-worker  │──────┐                                               │
│   │              │      │  1. Register → get token                      │
│   │  Kangaroo    │      │  2. Sense cold regions                        │
│   │  Algorithm   │      │  3. Compute distinguished points              │
│   │              │      │  4. Deposit results                           │
│   │  (CPU/GPU)   │      │  5. Check for collision                       │
│   └──────────────┘      │  6. Repeat                                    │
│                         ▼                                                │
└─────────────────────────┼────────────────────────────────────────────────┘
                          │
                          │  HTTPS + Bearer Token
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     api.ants-at-work.com                                 │
│                     (Cloudflare Edge + D1)                               │
│                                                                          │
│   Collision detection happens here. When tame and wild kangaroos        │
│   land on the same point → private key found.                           │
└─────────────────────────────────────────────────────────────────────────┘
```

No manual configuration. No copying tokens. Just join.

## Commands

```bash
ants-worker join           # Register and start working
ants-worker join -t wild   # Run as wild kangaroo (default: tame)
ants-worker status         # Check connection and worker ID
ants-worker leave          # Unregister (delete ~/.ants/config.json)
ants-worker info           # System/GPU info
ants-worker benchmark      # Test performance
```

## Hardware Acceleration

### AMD Ryzen AI (NEU-X, Motus)

Full support for AMD Ryzen AI processors with XDNA NPU:

```bash
# Auto-detects Ryzen AI and optimizes
ants-worker join

# Check detected hardware
ants-worker info --detailed

# Force specific backend
ants-worker join -b amd_npu    # Use NPU
ants-worker join -b amd_rocm   # Use integrated GPU
ants-worker join -b parallel_cpu --workers 16  # Use all CPU cores
```

Supported processors:
- AMD Ryzen AI Max 395 (126 TOPS)
- AMD Ryzen AI Max 385 (77 TOPS)
- AMD Ryzen AI 9 HX 370 (50 TOPS)
- AMD Ryzen AI 300 series

### NVIDIA GPU

```bash
# Install CUDA support
pip install ants-worker[cuda]

# Uses CUDA automatically
ants-worker join
```

### Kangaroo Binary (Fastest)

With Kangaroo binary: ~1B ops/sec.

```bash
# Linux with NVIDIA GPU
git clone https://github.com/JeanLucPons/Kangaroo.git
cd Kangaroo && make gpu=1 && cd ..
export KANGAROO_BIN=$(pwd)/Kangaroo/kangaroo

ants-worker join
```

## Run in Background

### Screen/tmux

```bash
screen -S ants
ants-worker join
# Ctrl+A, D to detach
```

### Systemd (Linux)

```bash
sudo tee /etc/systemd/system/ants-worker.service << 'EOF'
[Unit]
Description=Ants Worker
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ants-worker join
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now ants-worker
```

## Cloud Providers

Works on Vast.ai, Lambda Labs, RunPod, or any Linux machine:

```bash
apt update && apt install -y python3-pip
pip install ants-worker
ants-worker join
```

## What Are We Solving?

Bitcoin Puzzle #71 - a 7.1 BTC bounty.

Target: Find the private key for address `1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU`

The key is between `2^70` and `2^71`. Using Pollard's Kangaroo algorithm across many workers, we find it together.

## Stigmergic Coordination

Workers coordinate through the environment (not direct messaging):

1. **Sense** - Query cold regions (low pheromone = unexplored)
2. **Decide** - Pick a region to explore
3. **Mark** - Deposit "working" pheromone
4. **Work** - Run Kangaroo algorithm
5. **Deposit** - Leave results + exploration pheromone
6. **Repeat**

No central coordinator. Intelligence emerges.

## Architecture

```
                    ┌───────────────────────────────────────┐
                    │           AGENTVERSE                   │
                    │   Queen ◄──► Scouts ◄──► Hunters      │
                    │   (FET economy, agent messaging)       │
                    └─────────────────┬─────────────────────┘
                                      │
                    ┌─────────────────▼─────────────────────┐
                    │    api.ants-at-work.com (CF + D1)     │
                    │    Fast coordination, collision det.  │
                    └─────────────────┬─────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
        ┌──────────┐            ┌──────────┐            ┌──────────┐
        │ Worker 1 │            │ Worker 2 │            │ Worker N │
        └──────────┘            └──────────┘            └──────────┘
                                      │
                    ┌─────────────────▼─────────────────────┐
                    │    TypeDB Cloud (ants-colony)         │
                    │    Permanent storage, patterns         │
                    └───────────────────────────────────────┘
```

## FAQ

**Is this safe?**
Yes. You get a unique token that can only submit work results.

**Resources?**
Minimal bandwidth (~KB/min). CPU/GPU usage configurable. Stop with Ctrl+C.

**Where's my config?**
`~/.ants/config.json` - contains your token and worker ID.

**Tame vs Wild?**
Both needed. Run one of each for maximum contribution:
```bash
ants-worker join -t tame &
ants-worker join -t wild &
```

**How do I check status?**
```bash
ants-worker status
```

## Development

```bash
git clone https://github.com/ants-at-work/ants-worker
cd ants-worker
pip install -e ".[dev]"
pytest
```

See [docs/stigmergy-compute.md](docs/stigmergy-compute.md) for architecture details.

## Links

- Website: https://ants-at-work.com
- Gateway: https://api.ants-at-work.com/health
- Issues: https://github.com/ants-at-work/ants-worker/issues

## License

MIT
