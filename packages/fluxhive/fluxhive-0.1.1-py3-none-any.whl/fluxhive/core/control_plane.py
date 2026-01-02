"""
Networking utilities for connecting the FluxHive agent to the control server.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

import time
import websockets
from websockets.client import WebSocketClientProtocol

from ..utils.config import get_or_create_agent_key_pair, _get_host_unique_id
from ..utils.crypto import sign_agent_id
from ..services.gpu_monitor import GPUStats
from ..services.gpu_service import GPUService
from .manager import TaskManager
from .models import CommandGroup, GPUSnapshotMessage, Task, TaskStatus


LOG = logging.getLogger("core.control_plane")


class ControlPlaneEventPublisher:
    """Thread-safe helper that puts events onto the outbound queue."""

    def __init__(self, loop: asyncio.AbstractEventLoop, queue: "asyncio.Queue[Dict[str, Any]]") -> None:
        self._loop = loop
        self._queue = queue

    async def publish(self, event: Dict[str, Any]) -> None:
        fut = asyncio.run_coroutine_threadsafe(self._queue.put(event), self._loop)
        await asyncio.wrap_future(fut)


class TaskLogStreamer:
    """Forwards stdout/stderr chunks to the control plane."""

    def __init__(self, publisher: ControlPlaneEventPublisher) -> None:
        self._publisher = publisher

    async def emit(self, task_id: str, stream: str, data: str, run_id: Optional[str] = None) -> None:
        line = data.rstrip("\r\n")
        if not line:
            return
        await self._publisher.publish(
            {
                "type": "task-log",
                "task_id": task_id,
                "run_id": run_id,
                "stream": stream,
                "line": line,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


class TaskStatusReporter:
    """Callback injected into TaskManager for status updates."""

    def __init__(self, publisher: ControlPlaneEventPublisher) -> None:
        self._publisher = publisher

    async def __call__(self, task: Task) -> None:
        payload = {
            "type": "task.status",
            "task_id": task.id,
            "status": task.status.value,
            "return_code": task.return_code,
            "error": task.error,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        }
        # Include run_id if present on Task (propagated from dispatch). Do not use metadata.
        if getattr(task, "run_id", None):
            payload["run_id"] = task.run_id
        await self._publisher.publish(payload)


@dataclass
class ControlPlaneConfig:
    ws_url: str
    agent_id: str
    api_key: str
    label: Optional[str] = None
    reconnect_interval: float = 3.0


class ControlPlaneClient:
    """Maintains the WebSocket session to the control server."""

    def __init__(
        self,
        config: ControlPlaneConfig,
        task_manager: TaskManager,
        outbound_queue: "asyncio.Queue[Dict[str, Any]]",
    ) -> None:
        self._config = config
        self._manager = task_manager
        self._outbound = outbound_queue
        self._stop = asyncio.Event()
        self._connected = asyncio.Event()
        self._current_websocket: Optional[WebSocketClientProtocol] = None
        self._gpu_callback: Optional[callable] = None
        self._private_key, self._public_key_pem = get_or_create_agent_key_pair()

    async def run_forever(self) -> None:
        backoff = self._config.reconnect_interval
        while not self._stop.is_set():
            try:
                headers = self._build_headers()
                # print(headers)
                LOG.debug(
                    "Connecting to control server ws_url=%s agent_id=%s has_api_key=%s",
                    self._config.ws_url,
                    self._config.agent_id,
                    bool(self._config.api_key),
                )
                async with websockets.connect(
                    self._config.ws_url,
                    additional_headers=headers,
                ) as websocket:
                    LOG.info("Connected to control server ws_url=%s", self._config.ws_url)
                    self._connected.set()
                    await self._session_loop(websocket)
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover - network errors
                error_msg = str(exc)
                # Check for authentication/authorization errors (400, 403, 1008, or "rejected")
                if "400" in error_msg or "403" in error_msg or "rejected" in error_msg.lower() or "1008" in error_msg:
                    LOG.error(
                        "Authentication failed (policy violation). Check your API key. ws_url=%s error=%s",
                        self._config.ws_url,
                        error_msg,
                    )
                elif "getaddrinfo failed" in error_msg or "11001" in error_msg:
                    LOG.error(
                        "DNS resolution failed. Cannot resolve hostname in URL: %s error=%s",
                        self._config.ws_url,
                        error_msg,
                    )
                    LOG.error(
                        "Please check:\n"
                        "  1. Is the control server running?\n"
                        "  2. Is the 'control_base_url' in your config correct?\n"
                        "  3. Can you reach the server from this machine? (try: ping <hostname>)\n"
                        "  4. For localhost, try: http://127.0.0.1:8000 or http://localhost:8000"
                    )
                else:
                    LOG.error("Control connection failed: %s", exc)
                self._connected.clear()
                await asyncio.sleep(backoff)

    async def close(self) -> None:
        self._stop.set()

    def _get_platform_release(self) -> tuple[str, str]:
        """
        Get platform system and detailed release information.
        
        Returns:
            Tuple of (system, release) where system is the OS name and release is detailed version string.
        """
        system = platform.system()
        
        if system == "Windows":
            # Windows: Get version and edition info
            try:
                version = platform.version()  # e.g., '10.0.19045'
                release = platform.release()  # e.g., '10' or '11'
                
                # Try to get edition (Home, Pro, Enterprise, etc.)
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE, 
                        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
                    )
                    try:
                        edition, _ = winreg.QueryValueEx(key, "EditionID")
                        display_version, _ = winreg.QueryValueEx(key, "DisplayVersion")
                        return (system, f"Windows {release} {edition} ({display_version})")
                    except OSError:
                        # DisplayVersion or EditionID might not exist
                        return (system, f"Windows {release} ({version})")
                    finally:
                        winreg.CloseKey(key)
                except (ImportError, OSError) as e:
                    LOG.debug("Failed to read Windows registry: %s", e)
                    return (system, f"Windows {release} ({version})")
            except Exception as e:
                LOG.debug("Failed to get Windows version: %s", e)
                return (system, platform.platform())
        
        elif system == "Linux":
            # Linux: Try to get distribution info
            try:
                # Try using distro package (more reliable)
                import distro
                name = distro.name(pretty=True)  # e.g., "Ubuntu 20.04.6 LTS"
                if name:
                    return (system, name)
            except ImportError:
                LOG.debug("distro package not available, falling back to /etc/os-release")
            
            # Fallback: try reading /etc/os-release
            try:
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    info = {}
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            info[key] = value.strip('"')
                    
                    # Try PRETTY_NAME first, then fallback to NAME + VERSION
                    if "PRETTY_NAME" in info:
                        return (system, info["PRETTY_NAME"])
                    elif "NAME" in info and "VERSION" in info:
                        return (system, f"{info['NAME']} {info['VERSION']}")
                    elif "NAME" in info:
                        return (system, info["NAME"])
            except (OSError, IOError) as e:
                LOG.debug("Failed to read /etc/os-release: %s", e)
            
            # Last resort: return kernel version
            return (system, f"Linux {platform.release()}")
        
        elif system == "Darwin":
            # macOS: Get version
            try:
                mac_ver = platform.mac_ver()[0]
                if mac_ver:
                    # Convert version to macOS name if possible
                    major_version = int(mac_ver.split('.')[0])
                    if major_version >= 14:
                        return (system, f"macOS {mac_ver} (Sonoma or later)")
                    elif major_version == 13:
                        return (system, f"macOS {mac_ver} (Ventura)")
                    elif major_version == 12:
                        return (system, f"macOS {mac_ver} (Monterey)")
                    elif major_version == 11:
                        return (system, f"macOS {mac_ver} (Big Sur)")
                    elif major_version == 10:
                        minor = int(mac_ver.split('.')[1])
                        if minor == 15:
                            return (system, f"macOS {mac_ver} (Catalina)")
                        elif minor == 14:
                            return (system, f"macOS {mac_ver} (Mojave)")
                    return (system, f"macOS {mac_ver}")
            except (ValueError, IndexError) as e:
                LOG.debug("Failed to parse macOS version: %s", e)
            
            return (system, f"macOS {platform.release()}")
        
        else:
            # Other systems: use platform.platform()
            return (system, platform.platform())

    def _build_headers(self) -> Dict[str, str]:
        """
        Build WebSocket authentication headers.
        
        Uses API key authentication.
        Also includes cryptographic signature for agent identity verification.
        """
        headers = {
            "x-fluxhive-agent": self._config.agent_id,
            "x-fluxhive-api-key": self._config.api_key,
        }
        
        LOG.debug("Using API key authentication")
        
        if self._config.label:
            headers["x-fluxhive-label"] = self._config.label
            LOG.debug("Including label in WebSocket headers: %s", self._config.label)
        else:
            LOG.debug("No label configured, not including x-fluxhive-label header")
        
        # Add platform information with detailed release info
        system, release = self._get_platform_release()
        headers["x-fluxhive-platform"] = system  # Windows, Linux, Darwin, etc.
        headers["x-fluxhive-platform-release"] = release
        headers["x-fluxhive-host-fingerprint"] = _get_host_unique_id()

        
        # Add cryptographic signature for agent identity verification
        try:
            timestamp = time.time()
            signature = sign_agent_id(self._private_key, self._config.agent_id, self._config.api_key, timestamp)
            headers["x-fluxhive-signature"] = signature
            headers["x-fluxhive-timestamp"] = str(timestamp)
            headers["x-fluxhive-public-key-b64"] = base64.urlsafe_b64encode( self._public_key_pem.encode("utf-8") ).decode("ascii")
            LOG.debug("Including cryptographic signature for identity verification")
        except Exception as e:
            LOG.warning("Failed to generate signature, identity verification disabled: %s", str(e))
        
        return headers

    async def _session_loop(self, websocket: WebSocketClientProtocol) -> None:
        self._current_websocket = websocket
        
        # 注册 GPU 更新回调
        gpu_service = GPUService.instance()
        if gpu_service.monitor.available:
            self._register_gpu_callback(websocket, gpu_service)
            # 立即发送一次初始快照
            await self._send_gpu_snapshot(websocket, gpu_service)
        
        try:
            receiver = asyncio.create_task(self._consume_socket(websocket))
            sender = asyncio.create_task(self._flush_events(websocket))
            done, pending = await asyncio.wait(
                {receiver, sender},
                return_when=asyncio.FIRST_EXCEPTION,
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                if task.exception():
                    raise task.exception()
        finally:
            # 取消注册回调
            if self._gpu_callback:
                gpu_service = GPUService.instance()
                if gpu_service.monitor.available:
                    self._unregister_gpu_callback(gpu_service)
            self._current_websocket = None

    def _register_gpu_callback(self, websocket: WebSocketClientProtocol, gpu_service: GPUService) -> None:
        """Register callback for GPU updates."""
        loop = asyncio.get_event_loop()
        
        def on_gpu_update(stats: List[GPUStats]) -> None:
            """Callback called from monitor thread when GPU stats update."""
            if not self._current_websocket or self._stop.is_set():
                return
            
            # 使用 Pydantic 模型创建消息
            message = GPUSnapshotMessage.create(
                agent_id=self._config.agent_id,
                gpu_stats=stats,
            )
            
            # 从线程安全地调度到事件循环
            try:
                asyncio.run_coroutine_threadsafe(
                    self._send_gpu_message_safe(websocket, message),
                    loop
                )
            except Exception as e:
                LOG.debug("Failed to schedule GPU message: %s", e)
        
        gpu_service.monitor.register_callback(on_gpu_update)
        self._gpu_callback = on_gpu_update

    def _unregister_gpu_callback(self, gpu_service: GPUService) -> None:
        """Unregister GPU update callback."""
        if self._gpu_callback:
            gpu_service.monitor.unregister_callback(self._gpu_callback)
            self._gpu_callback = None

    async def _send_gpu_message_safe(
        self, websocket: WebSocketClientProtocol, message: GPUSnapshotMessage
    ) -> None:
        """Safely send GPU message, handling connection errors."""
        try:
            await websocket.send(json.dumps(message.to_dict()))
        except Exception as exc:
            LOG.debug("Failed to send GPU snapshot: %s", exc)

    async def _consume_socket(self, websocket: WebSocketClientProtocol) -> None:
        async for raw in websocket:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                LOG.warning("Dropped malformed control-plane message: %s", raw)
                continue
            await self._handle_message(message)

    async def _flush_events(self, websocket: WebSocketClientProtocol) -> None:
        retry_buffer: Optional[Dict[str, Any]] = None
        while True:
            event = retry_buffer or await self._outbound.get()
            try:
                await websocket.send(json.dumps(event))
                retry_buffer = None
            except Exception:
                retry_buffer = event
                raise

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        msg_type = message.get("type")
        if msg_type == "task.dispatch":
            # Pass the whole message so we can extract run_id and include it in task metadata
            await self._handle_task_dispatch(message)
        elif msg_type == "task.cancel":
            task_id = message.get("task_id")
            if task_id:
                cancelled = self._manager.cancel(task_id)
                await self._outbound.put(
                    {
                        "type": "task.status",
                        "task_id": task_id,
                        "status": TaskStatus.CANCELLED.value if cancelled else TaskStatus.PENDING.value,
                    }
                )
        elif msg_type == "gpu.request":
            LOG.debug("Received GPU request from control server")
            await self._handle_gpu_request()
        elif msg_type == "gpu.monitor.set_interval":
            await self._handle_gpu_monitor_set_interval(message)
        else:
            LOG.warning("Unknown control-plane message: %s", message)

    async def _handle_task_dispatch(self, message: Dict[str, Any]) -> None:
        payload = message.get("task") or {}
        run_id = message.get("run_id")
        commands = payload.get("commands") or []
        if not commands:
            LOG.warning("Ignoring dispatch without commands: %s", payload)
            return
        workdir = payload.get("workdir")
        command_group = CommandGroup(
            commands=commands,
            env=payload.get("env") or {},
            workdir=Path(workdir) if workdir else None,
        )
        metadata = payload.get("metadata") or {}
        task_id = payload.get("id")
        task = self._manager.submit(
            command_group,
            metadata=metadata,
            run_id=run_id,
            task_id=task_id,
        )
        LOG.info(
            "Accepted task from control plane task_id=%s commands=%d",
            task.id,
            len(command_group.commands),
        )

    async def _handle_gpu_request(self) -> None:
        """Handle GPU request from control server - immediately send GPU snapshot."""
        if not self._current_websocket:
            LOG.warning("Received GPU request but no active websocket connection")
            return
        gpu_service = GPUService.instance()
        # Always send a response, even if GPU monitor is unavailable
        await self._send_gpu_snapshot(self._current_websocket, gpu_service, force=True)

    async def _handle_gpu_monitor_set_interval(self, message: Dict[str, Any]) -> None:
        """Handle GPU monitor interval setting from control server.
        
        Args:
            message: Message containing 'interval' field (in seconds)
        """
        interval = message.get("interval")
        if interval is None:
            LOG.warning("Received gpu.monitor.set_interval without interval field")
            await self._outbound.put(
                {
                    "type": "gpu.monitor.set_interval.response",
                    "success": False,
                    "error": "Missing 'interval' field",
                }
            )
            return
        
        try:
            interval_float = float(interval)
            if interval_float <= 0:
                raise ValueError("Interval must be positive")
            
            gpu_service = GPUService.instance()
            gpu_service.set_poll_interval(interval_float)
            
            LOG.info("GPU monitor interval set to %.2f seconds", interval_float)
            await self._outbound.put(
                {
                    "type": "gpu.monitor.set_interval.response",
                    "success": True,
                    "interval": interval_float,
                }
            )
        except (ValueError, TypeError) as e:
            LOG.warning("Invalid interval value: %s", e)
            await self._outbound.put(
                {
                    "type": "gpu.monitor.set_interval.response",
                    "success": False,
                    "error": str(e),
                }
            )
        except Exception as e:
            LOG.error("Failed to set GPU monitor interval: %s", e, exc_info=True)
            await self._outbound.put(
                {
                    "type": "gpu.monitor.set_interval.response",
                    "success": False,
                    "error": f"Internal error: {str(e)}",
                }
            )

    async def _send_gpu_snapshot(self, websocket: WebSocketClientProtocol, gpu_service: GPUService, force: bool = False) -> None:
        """Send GPU snapshot to control server.
        
        Args:
            websocket: The WebSocket connection to send the message on
            gpu_service: The GPU service instance
            force: If True, send an empty snapshot even if GPU monitor is unavailable
        """
        if not gpu_service.monitor.available:
            if not force:
                return
            # Send empty snapshot when forced and monitor unavailable
            LOG.warning(
                "GPU monitor unavailable. Possible reasons: "
                "pynvml not installed, no NVIDIA GPU, or NVML initialization failed. "
                "Sending empty GPU snapshot."
            )
            message = GPUSnapshotMessage.create(
                agent_id=self._config.agent_id,
                gpu_stats=[],
            )
            try:
                await websocket.send(json.dumps(message.to_dict()))
            except Exception as exc:
                LOG.debug("Failed to send GPU snapshot: %s", exc)
            return
        
        try:
            stats = gpu_service.snapshot()
            
            # 使用 Pydantic 模型创建消息
            message = GPUSnapshotMessage.create(
                agent_id=self._config.agent_id,
                gpu_stats=stats,
            )
            await websocket.send(json.dumps(message.to_dict()))
        except Exception as exc:
            LOG.debug("Failed to send GPU snapshot: %s", exc)

