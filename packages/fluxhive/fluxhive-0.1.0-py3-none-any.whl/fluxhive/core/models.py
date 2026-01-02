"""Data models shared across FlowHive agent components."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..services.gpu_monitor import GPUStats


class TaskStatus(str, Enum):
    """Execution lifecycle for a task."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class CommandGroup:
    """A logical group of shell commands with shared execution context."""

    commands: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    workdir: Optional[Path] = None

    def __post_init__(self) -> None:
        if not self.commands:
            raise ValueError("CommandGroup requires at least one command")


@dataclass(slots=True)
class Task:
    """A tracked unit of work to be executed by the agent."""

    command_group: CommandGroup
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Run identifier propagated from control server. Stored as a first-class
    # attribute instead of inside metadata to avoid coupling runtime fields
    # with user-defined metadata.
    run_id: Optional[str] = None
    shell_id: Optional[str] = None
    id: str = field(default_factory=lambda: uuid4().hex)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    return_code: Optional[int] = None
    stdout_path: Optional[Path] = None
    stderr_path: Optional[Path] = None
    error: Optional[str] = None

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_finished(self, status: TaskStatus, return_code: Optional[int]) -> None:
        self.status = status
        self.return_code = return_code
        self.finished_at = datetime.utcnow()


@dataclass(slots=True)
class ProcessUsage:
    pid: int
    memory_mb: Optional[float]
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    name: Optional[str] = None
    user: Optional[str] = None


@dataclass(slots=True)
class GPUStats:
    index: int
    name: str
    total_memory_mb: float
    used_memory_mb: float
    free_memory_mb: float
    utilization: Optional[float]
    temperature_c: Optional[float]
    power_usage_w: Optional[float]
    power_limit_w: Optional[float]
    timestamp: float
    task_processes: List[ProcessUsage] = field(default_factory=list)
    external_processes: List[ProcessUsage] = field(default_factory=list)


@dataclass(slots=True)
class TaskProcessInfo:
    task_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class GPUSnapshotMessage(BaseModel):
    """Pydantic model for GPU snapshot WebSocket messages."""

    type: str = Field(default="gpu.snapshot", description="Message type")
    agent_id: str = Field(..., description="Agent identifier")
    gpus: List[Dict[str, Any]] = Field(default_factory=list, description="List of GPU statistics")
    timestamp: str = Field(..., description="ISO format timestamp")

    @classmethod
    def create(
        cls,
        agent_id: str,
        gpu_stats: List[GPUStats],  # type: ignore[name-defined]
    ) -> "GPUSnapshotMessage":
        """Create a GPU snapshot message from agent_id and GPU stats."""
        from ..services.gpu_monitor import GPUStats
        
        # Convert GPU stats to dicts and format timestamps
        gpu_dicts = []
        for gpu_stat in gpu_stats:
            gpu_dict = asdict(gpu_stat)
            # Format timestamp from float to ISO string
            if "timestamp" in gpu_dict and isinstance(gpu_dict["timestamp"], (int, float)):
                gpu_dict["timestamp"] = datetime.fromtimestamp(
                    gpu_dict["timestamp"], tz=timezone.utc
                ).isoformat()
            gpu_dicts.append(gpu_dict)
        
        return cls(
            agent_id=agent_id,
            gpus=gpu_dicts,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()


