# FluxHive Agent

> User Server Agent - The compute node component of FluxHive distributed GPU task scheduling platform

[![License: Non-Commercial Copyleft](https://img.shields.io/badge/License-Non--Commercial%20Copyleft-blue.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/fluxhive.svg)](https://badge.fury.io/py/fluxhive)

## Overview

FluxHive Agent is the compute node component that runs on GPU servers. It connects to the Control Server via WebSocket and handles:

- **Node Registration & Heartbeat**: Automatically registers with Control Server and maintains connection health
- **Task Execution**: Receives and executes tasks (Python scripts, shell commands, distributed training jobs)
- **GPU Monitoring**: Real-time GPU metrics collection (utilization, memory, processes) via NVML
- **Log Streaming**: Streams stdout/stderr logs back to Control Server in real-time
- **Resource Management**: Intelligent task scheduling based on GPU memory availability and priorities

## Directory Structure

```
agent/
├── fluxhive/
│   ├── core/              # Core agent logic
│   │   ├── task.py        # Task models and state machine
│   │   ├── executor.py    # Task execution engine (subprocess, torchrun)
│   │   ├── task_manager.py # Task scheduler and manager
│   │   └── gpu_monitor.py # GPU monitoring via NVML
│   ├── cli/               # Command-line interface
│   │   └── fluxhive.py    # Main CLI entry point
│   └── __init__.py
├── scripts/               # Demo and testing scripts
│   ├── demo_task_manager.py
│   └── demo_shell_test.py
├── tests/                 # Pytest test cases
├── pyproject.toml         # Package configuration
├── requirements.txt       # Python dependencies
└── README.md
```

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install fluxhive
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/Dramwig/FluxHive.git
cd FluxHive/agent

# Create virtual environment
python -m venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Requirements

- Python 3.10 or higher
- NVIDIA GPU with CUDA drivers (for GPU monitoring)
- Operating System: Linux, Windows, or macOS

## Quick Start

### 1. Configure Agent

After installation, configure the agent to connect to your Control Server:

```bash
# Set user credentials
fluxhive config user.username "your-username"
fluxhive config user.email "your-email@example.com"
fluxhive config user.password "your-password"

# Set Control Server URL
fluxhive config control_base_url "http://127.0.0.1:8001"

# Set agent label (optional, for identification)
fluxhive config label "gpu-server-01"

# Verify configuration
fluxhive config
```

### 2. Start Agent

```bash
fluxhive run
```

The agent will:
- Automatically register with the Control Server
- Start GPU monitoring (if NVIDIA GPU is available)
- Begin listening for task assignments
- Send periodic heartbeats

### 3. Test Locally (Without Control Server)

For quick testing of task execution without a Control Server:

```bash
cd agent
python scripts/demo_task_manager.py
```

Run custom commands:

```bash
python scripts/demo_task_manager.py "python -c \"print('Hello FluxHive!')\"" --timeout 10
```

Logs will be saved to `.agent_logs/` directory.

## Configuration

### WebSocket Connection

The agent communicates with Control Server via WebSocket. The protocol is automatically determined from the `control_base_url`:

- `http://` → `ws://` (Plain WebSocket)
- `https://` → `wss://` (Secure WebSocket, recommended for production)

### Production Configuration Example

```bash
# Use HTTPS/WSS for secure communication (recommended)
fluxhive config control_base_url "https://your-control-server.com"
fluxhive config user.username "prod-user"
fluxhive config user.password "secure-password"
fluxhive config label "prod-gpu-node-01"
```

### Configuration File Location

Configuration is stored in:
- **Linux/macOS**: `~/.config/fluxhive/config.toml`
- **Windows**: `%USERPROFILE%\.config\fluxhive\config.toml`

### Environment Variables

You can also use environment variables (they override config file):

```bash
export FLUXHIVE_CONTROL_URL="http://127.0.0.1:8001"
export FLUXHIVE_USERNAME="your-username"
export FLUXHIVE_PASSWORD="your-password"
fluxhive run
```

## Key Features

### GPU Monitoring
- **Real-time Metrics**: GPU utilization, memory usage, temperature, power consumption
- **Process Tracking**: Per-process GPU memory allocation
- **NVML Integration**: Direct access to NVIDIA Management Library
- **Multi-GPU Support**: Automatic detection and monitoring of all available GPUs

### Task Scheduling
- **Memory-Aware Scheduling**: Tasks scheduled based on available GPU memory
- **Priority Queue**: Support for task priorities and fair scheduling
- **Concurrent Execution**: Multiple tasks can run simultaneously if resources allow
- **Retry Mechanism**: Automatic retry for failed tasks with configurable policies

### Task Execution
- **Multiple Executors**: Support for `subprocess`, `torchrun`, and shell commands
- **Environment Variables**: Inject custom environment variables per task
- **Container Support**: Execute tasks in containerized environments
- **Distributed Training**: Native support for PyTorch distributed training via `torchrun`

### Reliability
- **OOM Recovery**: Automatic detection and handling of out-of-memory errors
- **Heartbeat Service**: Periodic health checks (1-5s interval) with Control Server
- **Graceful Shutdown**: Proper cleanup of running tasks on agent shutdown
- **Log Streaming**: Real-time stdout/stderr streaming to Control Server

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FluxHive Agent                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │   CLI Tool   │   │ Task Manager │   │  GPU Monitor    │  │
│  │  (fluxhive)  │   │              │   │   (NVML)        │  │
│  └──────┬───────┘   └──────┬───────┘   └────────┬────────┘  │
│         │                  │                    │           │
│         └──────────────────┼────────────────────┘           │
│                            │                                │
│                   ┌────────▼────────┐                       │
│                   │  WebSocket      │                       │
│                   │  Client         │                       │
│                   └────────┬────────┘                       │
└────────────────────────────┼────────────────────────────────┘
                             │
                             │ ws:// or wss://
                             │
                   ┌─────────▼──────────┐
                   │  Control Server    │
                   │  (FastAPI + WS)    │
                   └────────────────────┘
```

## CLI Commands

```bash
# Configuration management
fluxhive config                          # Show all configuration
fluxhive config <key> <value>            # Set configuration value
fluxhive config <key>                    # Get configuration value

# Run agent
fluxhive run                             # Start agent and connect to Control Server

# Examples
fluxhive config user.username "alice"
fluxhive config control_base_url "https://control.example.com"
fluxhive run
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test
pytest tests/test_task_manager.py

# Run with coverage
pytest --cov=fluxhive tests/
```

### Building Package

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to PyPI (maintainers only)
twine upload dist/*
```

## License

This Agent component is licensed under the **FluxHive Agent Non-Commercial Copyleft License v1.0**. See [LICENSE](./LICENSE) for details.

### License Highlights

- ✅ **Open Source**: You may view, modify, and distribute the source code
- ❌ **Non-Commercial**: Commercial use is prohibited (separate commercial license required)
- 🔒 **Copyleft**: Modifications and derivative works must remain open source; closed-source distribution is prohibited
- 📋 **Copyleft Mechanism**: Similar to Linux's GPL license, ensuring code remains open source

**Note**: This applies only to the Agent component. The Control Server and Web Client are proprietary software and not covered by this license.

---

Made with ❤️ by the FluxHive Team
