from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from core.gpu_monitor import GPUMonitor
from core.models import CommandGroup, Task
from core.runner import AsyncCommandRunner


def python_command(code: str) -> str:
    escaped = code.replace('"', r"\"")
    return f'"{sys.executable}" -c "{escaped}"'


class FakeProcess:
    def __init__(self, pid: int, used: int) -> None:
        self.pid = pid
        self.usedGpuMemory = used


class FakeNVMLAdapter:
    def __init__(self) -> None:
        self._devices = [
            {
                "name": "Fake GPU",
                "memory": SimpleNamespace(total=8 * 1024**3, used=2 * 1024**3, free=6 * 1024**3),
                "util": SimpleNamespace(gpu=55.0),
                "processes": [
                    FakeProcess(pid=101, used=512 * 1024**2),
                    FakeProcess(pid=202, used=256 * 1024**2),
                ],
            }
        ]
        self.shutdown_called = False

    def device_count(self) -> int:
        return len(self._devices)

    def device_handle(self, index: int) -> int:
        return index

    def device_name(self, handle: int) -> str:
        return self._devices[handle]["name"]

    def memory_info(self, handle: int) -> SimpleNamespace:
        return self._devices[handle]["memory"]

    def utilization_rates(self, handle: int) -> SimpleNamespace:
        return self._devices[handle]["util"]

    def running_processes(self, handle: int):
        return self._devices[handle]["processes"]

    def shutdown(self) -> None:
        self.shutdown_called = True


def test_gpu_monitor_tracks_task_and_external_processes():
    adapter = FakeNVMLAdapter()
    monitor = GPUMonitor(
        poll_interval=0.1, history_size=4, nvml_adapter=adapter, auto_start=False
    )

    monitor.register_task_process(task_id="task-1", pid=101, metadata={"role": "train"})
    monitor.refresh()

    stats = monitor.snapshot()
    assert len(stats) == 1
    gpu = stats[0]
    assert gpu.name == "Fake GPU"
    assert gpu.task_processes and gpu.task_processes[0].pid == 101
    assert gpu.task_processes[0].metadata["role"] == "train"
    assert gpu.external_processes and gpu.external_processes[0].pid == 202

    monitor.unregister_task_process(101)
    monitor.shutdown()
    assert adapter.shutdown_called


class DummyMonitor:
    def __init__(self) -> None:
        self.available = True
        self.registered: list[tuple[str, int, dict]] = []
        self.unregistered: list[int] = []

    def register_task_process(self, *, task_id: str, pid: int, metadata: dict | None = None) -> None:
        self.registered.append((task_id, pid, metadata or {}))

    def unregister_task_process(self, pid: int) -> None:
        self.unregistered.append(pid)


@pytest.mark.asyncio()
async def test_runner_registers_process_with_monitor(tmp_path: Path):
    monitor = DummyMonitor()
    runner = AsyncCommandRunner(log_dir=tmp_path, gpu_monitor=monitor)
    task = Task(
        command_group=CommandGroup(commands=[python_command("print('gpu monitor')")]),
        metadata={"gpu": "any"},
    )

    await runner.run(task, asyncio.Event())

    assert monitor.registered
    task_id, pid, metadata = monitor.registered[0]
    assert task_id == task.id
    assert "command" in metadata
    assert metadata["task_metadata"]["gpu"] == "any"
    assert monitor.unregistered == [pid]


