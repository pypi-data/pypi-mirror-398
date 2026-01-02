"""GPU monitoring utilities for agent tasks."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional, Protocol

LOG = logging.getLogger("services.gpu_monitor")


def _megabytes(bytes_value: float) -> float:
    return bytes_value / (1024 * 1024)


def _milliwatts_to_watts(milliwatts: float) -> float:
    return milliwatts / 1000.0


def _get_process_name(pid: int) -> Optional[str]:
    """Get process name by PID using psutil.

    Args:
        pid: Process ID

    Returns:
        Process name if available, None otherwise
    """
    if pid <= 0:
        return None
    try:
        import psutil
        proc = psutil.Process(pid)
        return proc.name()
    except ImportError:
        LOG.debug("psutil not available, cannot get process name")
        return None
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        # Process may have terminated or we don't have permission
        return None
    except Exception as e:
        LOG.debug("Failed to get process name for PID %d: %s", pid, e)
        return None


def _get_process_user(pid: int) -> Optional[str]:
    """Get process owner (username) by PID using psutil.

    Args:
        pid: Process ID

    Returns:
        Username if available, None otherwise
    """
    if pid <= 0:
        return None
    try:
        import psutil
        proc = psutil.Process(pid)
        name = proc.username()
        return name
    except ImportError:
        LOG.debug("psutil not available, cannot get process user")
        return None
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        # Process may have terminated or we don't have permission
        return None
    except Exception as e:
        LOG.debug("Failed to get process user for PID %d: %s", pid, e)
        return None


class NVMLAdapter(Protocol):
    """Subset of the pynvml surface needed by GPUMonitor."""

    def device_count(self) -> int: ...

    def device_handle(self, index: int) -> Any: ...

    def device_name(self, handle: Any) -> str: ...

    def memory_info(self, handle: Any) -> Any: ...

    def utilization_rates(self, handle: Any) -> Any: ...

    def running_processes(self, handle: Any) -> List[Any]: ...

    def temperature(self, handle: Any) -> Optional[float]: ...

    def power_usage(self, handle: Any) -> Optional[float]: ...

    def power_limit(self, handle: Any) -> Optional[float]: ...

    def shutdown(self) -> None: ...


def _load_nvml_adapter() -> Optional[NVMLAdapter]:
    """Lazily import pynvml and provide a thin adapter."""

    try:
        import pynvml
    except ImportError as e:
        LOG.debug("pynvml not available: %s. GPU monitoring disabled.", e)
        return None
    except Exception as e:  # pragma: no cover - optional dependency
        LOG.debug("Failed to import pynvml: %s. GPU monitoring disabled.", e)
        return None

    class _Adapter:
        def __init__(self) -> None:
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                LOG.info("NVML initialized successfully. Found %d GPU(s).", device_count)
            except Exception as e:
                LOG.warning("Failed to initialize NVML: %s. GPU monitoring disabled.", e)
                raise

        def device_count(self) -> int:
            return pynvml.nvmlDeviceGetCount()

        def device_handle(self, index: int) -> Any:
            return pynvml.nvmlDeviceGetHandleByIndex(index)

        def device_name(self, handle: Any) -> str:
            name = pynvml.nvmlDeviceGetName(handle)
            # Handle both bytes (older pynvml) and str (newer pynvml)
            if isinstance(name, bytes):
                return name.decode("utf-8")
            return str(name)

        def memory_info(self, handle: Any) -> Any:
            return pynvml.nvmlDeviceGetMemoryInfo(handle)

        def utilization_rates(self, handle: Any) -> Any:
            return pynvml.nvmlDeviceGetUtilizationRates(handle)

        def running_processes(self, handle: Any) -> List[Any]:
            try:
                return pynvml.nvmlDeviceGetComputeRunningProcesses_v3(handle)
            except AttributeError:
                return pynvml.nvmlDeviceGetComputeRunningProcesses(handle)

        def temperature(self, handle: Any) -> Optional[float]:
            try:
                temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU
                )
            except Exception:
                return None
            return float(temp)

        def power_usage(self, handle: Any) -> Optional[float]:
            try:
                usage_mw = pynvml.nvmlDeviceGetPowerUsage(handle)
            except Exception:
                return None
            if usage_mw is None:
                return None
            return _milliwatts_to_watts(float(usage_mw))

        def power_limit(self, handle: Any) -> Optional[float]:
            limit_mw: Optional[float] = None
            try:
                limit_mw = float(pynvml.nvmlDeviceGetEnforcedPowerLimit(handle))
            except AttributeError:
                try:
                    limit_mw = float(pynvml.nvmlDeviceGetPowerManagementLimit(handle))
                except Exception:
                    limit_mw = None
            except Exception:
                limit_mw = None
            if limit_mw is None:
                return None
            return _milliwatts_to_watts(limit_mw)

        def shutdown(self) -> None:
            pynvml.nvmlShutdown()

    try:
        return _Adapter()
    except Exception as e:
        LOG.debug("Failed to create NVML adapter: %s", e)
        return None


from ..core.models import GPUStats, TaskProcessInfo, ProcessUsage


class GPUMonitor:
    """Periodically polls NVML for GPU + process usage information."""

    def __init__(
        self,
        *,
        poll_interval: float = 1.0,
        history_size: int = 60,
        nvml_adapter: Optional[NVMLAdapter] = None,
        auto_start: bool = True,
    ) -> None:
        self._poll_interval = poll_interval
        self._history: Deque[List[GPUStats]] = deque(maxlen=history_size)
        self._task_registry: Dict[int, TaskProcessInfo] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._callbacks: List[callable] = []  # 添加回调列表

        self._nvml = nvml_adapter if nvml_adapter is not None else _load_nvml_adapter()
        self._available = self._nvml is not None
        self._latest: List[GPUStats] = []
        self._thread: Optional[threading.Thread] = None

        if self._available and auto_start:
            self._thread = threading.Thread(
                target=self._poll_loop,
                name="gpu-monitor",
                daemon=True,
            )
            self._thread.start()

    @property
    def available(self) -> bool:
        return self._available

    def register_task_process(
        self, *, task_id: str, pid: int, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        if pid <= 0:
            raise ValueError("pid must be positive")
        with self._lock:
            self._task_registry[pid] = TaskProcessInfo(
                task_id=task_id, metadata=dict(metadata or {})
            )

    def unregister_task_process(self, pid: int) -> None:
        with self._lock:
            self._task_registry.pop(pid, None)

    def snapshot(self) -> List[GPUStats]:
        with self._lock:
            return [self._clone_stat(stat) for stat in self._latest]

    def history(self) -> List[List[GPUStats]]:
        with self._lock:
            return [[self._clone_stat(stat) for stat in bucket] for bucket in self._history]

    def refresh(self) -> None:
        if not self._available:
            return
        self._record_stats()

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._available and hasattr(self._nvml, "shutdown"):
            try:
                self._nvml.shutdown()
            except Exception:  # pragma: no cover - defensive
                pass

    def register_callback(self, callback: callable) -> None:
        """Register a callback to be called when GPU stats are updated.
        
        Args:
            callback: A callable that takes a List[GPUStats] as argument.
                     Will be called from the monitor thread.
        """
        with self._lock:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: callable) -> None:
        """Unregister a callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def set_poll_interval(self, interval: float) -> None:
        """Dynamically set the polling interval (in seconds).
        
        Args:
            interval: New polling interval in seconds. Must be positive.
        
        Raises:
            ValueError: If interval is not positive.
        """
        if interval <= 0:
            raise ValueError("Poll interval must be positive")
        with self._lock:
            self._poll_interval = interval
        LOG.info("GPU monitor poll interval set to %.2f seconds", interval)

    @property
    def poll_interval(self) -> float:
        """Get the current polling interval in seconds."""
        with self._lock:
            return self._poll_interval

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._record_stats()
            except Exception as e:
                # Disable further polling if NVML fails repeatedly.
                LOG.error(
                    "GPU monitoring failed during polling: %s. "
                    "Disabling GPU monitor. Error type: %s",
                    e,
                    type(e).__name__,
                    exc_info=True,
                )
                self._available = False
                break
            self._stop_event.wait(self._poll_interval)

    def _record_stats(self) -> None:
        stats = self._collect_stats()
        timestamp = time.time()
        for stat in stats:
            stat.timestamp = timestamp
        with self._lock:
            self._latest = stats
            self._history.append([self._clone_stat(stat) for stat in stats])
            # 触发所有注册的回调
            callbacks = list(self._callbacks)
            snapshot = [self._clone_stat(stat) for stat in stats]
        
        # 在锁外调用回调，避免死锁
        for callback in callbacks:
            try:
                callback(snapshot)
            except Exception as e:
                LOG.warning("GPU monitor callback failed: %s", e, exc_info=True)

    def _collect_stats(self) -> List[GPUStats]:
        if not self._nvml:
            return []

        stats: List[GPUStats] = []
        with self._lock:
            registry_snapshot = dict(self._task_registry)
        
        try:
            device_count = self._nvml.device_count()
        except Exception as e:
            LOG.warning("Failed to get GPU device count: %s", e)
            return []
        
        for index in range(device_count):
            try:
                handle = self._nvml.device_handle(index)
            except Exception as e:
                LOG.warning("Failed to get handle for GPU %d: %s", index, e)
                continue

            try:
                memory = self._nvml.memory_info(handle)
            except Exception as e:
                LOG.warning("Failed to get memory info for GPU %d: %s", index, e)
                continue

            utilization = None
            try:
                util_rates = self._nvml.utilization_rates(handle)
                utilization = float(getattr(util_rates, "gpu", util_rates))
            except Exception:
                pass

            try:
                name = self._nvml.device_name(handle)
            except Exception as e:
                LOG.warning("Failed to get name for GPU %d: %s", index, e)
                name = f"GPU {index}"
                
            try:
                temperature_c = self._nvml.temperature(handle)
            except Exception as e:
                LOG.warning("Failed to get temperature for GPU %d: %s", index, e)
                temperature_c = None
                
            try:
                power_usage_w = self._nvml.power_usage(handle)
            except Exception as e:
                LOG.warning("Failed to get power usage for GPU %d: %s", index, e)
                power_usage_w = None
                
            try:
                power_limit_w = self._nvml.power_limit(handle)
            except Exception as e:
                LOG.warning("Failed to get power limit for GPU %d: %s", index, e)
                power_limit_w = None

            gpu_stat = GPUStats(
                index=index,
                name=name,
                total_memory_mb=_megabytes(memory.total),
                used_memory_mb=_megabytes(memory.used),
                free_memory_mb=_megabytes(memory.free),
                utilization=utilization,
                temperature_c=temperature_c,
                power_usage_w=power_usage_w,
                power_limit_w=power_limit_w,
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_processes=[],
                external_processes=[],
            )

            try:
                processes = self._nvml.running_processes(handle)
            except Exception:
                processes = []

            for proc in processes:
                pid = int(getattr(proc, "pid", -1) or -1)

                # Prefer None when the NVML struct does not expose a memory field
                used_mem_raw = getattr(proc, "usedGpuMemory", None)
                if used_mem_raw is None:
                    # try alternative names that some NVML builds/platforms expose
                    for attr in ("gpuMemory", "usedGpuMemoryBytes", "usedMemory"):
                        try:
                            alt = getattr(proc, attr, None)
                        except Exception:
                            alt = None
                        if alt is not None:
                            used_mem_raw = alt
                            break

                try:
                    memory_mb_value: Optional[float]
                    if used_mem_raw is None:
                        memory_mb_value = None
                    else:
                        memory_mb_value = _megabytes(float(used_mem_raw))
                except Exception:
                    memory_mb_value = None

                proc_info = registry_snapshot.get(pid)
                process_name = _get_process_name(pid)
                process_user = _get_process_user(pid)
                process_usage = ProcessUsage(
                    pid=pid,
                    memory_mb=memory_mb_value,
                    task_id=proc_info.task_id if proc_info else None,
                    metadata=dict(proc_info.metadata) if proc_info else {},
                    name=process_name,
                    user=process_user,
                )
                if proc_info:
                    gpu_stat.task_processes.append(process_usage)
                else:
                    gpu_stat.external_processes.append(process_usage)

            stats.append(gpu_stat)
        return stats

    @staticmethod
    def _clone_stat(stat: GPUStats) -> GPUStats:
        return GPUStats(
            index=stat.index,
            name=stat.name,
            total_memory_mb=stat.total_memory_mb,
            used_memory_mb=stat.used_memory_mb,
            free_memory_mb=stat.free_memory_mb,
            utilization=stat.utilization,
            temperature_c=stat.temperature_c,
            power_usage_w=stat.power_usage_w,
            power_limit_w=stat.power_limit_w,
            timestamp=stat.timestamp,
            task_processes=[
                ProcessUsage(
                    pid=p.pid,
                    memory_mb=p.memory_mb,
                    task_id=p.task_id,
                    metadata=dict(p.metadata),
                    name=p.name,
                    user=p.user,
                )
                for p in stat.task_processes
            ],
            external_processes=[
                ProcessUsage(
                    pid=p.pid,
                    memory_mb=p.memory_mb,
                    task_id=p.task_id,
                    metadata=dict(p.metadata),
                    name=p.name,
                    user=p.user,
                )
                for p in stat.external_processes
            ],
        )



