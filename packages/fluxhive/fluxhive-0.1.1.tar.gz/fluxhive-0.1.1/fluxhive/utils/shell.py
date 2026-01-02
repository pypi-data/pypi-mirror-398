"""Persistent shell abstraction for reusing execution context across tasks."""

from __future__ import annotations

import asyncio
import os
import signal
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional
from uuid import uuid4

from ..core.exceptions import TaskExecutionError
from ..core.models import CommandGroup, Task

if TYPE_CHECKING:
    from ..core.control_plane import TaskLogStreamer
    from ..services.gpu_monitor import GPUMonitor


DEBUG_ENV = "FLUXHIVE_SHELL_DEBUG"
DEBUG_LOG = Path(".agent_logs") / "persistent_shell.debug.log"


class PersistentShell:
    """Long-lived shell process that executes command groups sequentially."""

    MARKER_PREFIX = "__FLUXHIVE_DONE__"
    STATUS_VAR = "__FLUXHIVE_STATUS__"

    def __init__(
        self,
        *,
        shell_id: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        workdir: Optional[Path] = None,
        log_streamer: Optional["TaskLogStreamer"] = None,
        gpu_monitor: Optional["GPUMonitor"] = None,
    ) -> None:
        self.id = shell_id or uuid4().hex
        self._env = env or {}
        self._workdir = workdir
        self._log_streamer = log_streamer
        self._gpu_monitor = gpu_monitor

        self._process: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()
        self._closed = False
        self._registered_pid: Optional[int] = None
        self._debug_enabled = bool(os.environ.get(DEBUG_ENV))

    async def run(
        self,
        *,
        task: Task,
        command_group: CommandGroup,
        stdout_path: Path,
        stderr_path: Path,
        cancel_event: asyncio.Event,
    ) -> None:
        if self._closed:
            raise TaskExecutionError("Shell already closed")

        async with self._lock:
            process = await self._ensure_process()
            marker = f"{self.MARKER_PREFIX}{uuid4().hex}"
            env_prefix, env_suffix = self._build_env_wrappers(command_group.env)
            combined = self._chain_commands(command_group.commands)
            commands = env_prefix + [
                combined,
                self._store_status_command(),
            ]
            commands += env_suffix
            commands.append(self._marker_command(marker))
            commands.append(self._clear_status_command())

            await self._send_commands(process, commands)
            self._debug(f"sent commands: {commands}")
            return_code = await self._drain_until_marker(
                process=process,
                marker=marker,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                task=task,
                cancel_event=cancel_event,
            )
            if return_code != 0:
                raise TaskExecutionError(
                    f"Shell command group failed with code {return_code}",
                    return_code=return_code,
                )

    async def close(self) -> None:
        self._closed = True
        async with self._lock:
            if not self._process:
                return
            try:
                await self._terminate_process(self._process)
            finally:
                self._process = None
                if self._registered_pid is not None and self._gpu_monitor:
                    try:
                        self._gpu_monitor.unregister_task_process(self._registered_pid)
                    except Exception:
                        pass
                self._registered_pid = None

    async def _ensure_process(self) -> asyncio.subprocess.Process:
        if self._process and self._process.returncode is None:
            return self._process

        cmd = self._shell_command()
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._env,
            cwd=str(self._workdir) if self._workdir else None,
        )

        if self._gpu_monitor and self._gpu_monitor.available:
            try:
                self._gpu_monitor.register_task_process(
                    task_id=f"shell:{self.id}",
                    pid=self._process.pid,
                    metadata={"workdir": str(self._workdir) if self._workdir else None},
                )
                self._registered_pid = self._process.pid
            except Exception:
                self._registered_pid = None

        return self._process

    async def _send_commands(
        self,
        process: asyncio.subprocess.Process,
        commands: list[str],
    ) -> None:
        assert process.stdin is not None
        newline = b"\r\n" if os.name == "nt" else b"\n"
        for command in commands:
            process.stdin.write(command.rstrip("\r\n").encode() + newline)
        await process.stdin.drain()

    async def _drain_until_marker(
        self,
        *,
        process: asyncio.subprocess.Process,
        marker: str,
        stdout_path: Path,
        stderr_path: Path,
        task: Task,
        cancel_event: asyncio.Event,
    ) -> int:
        done_event = asyncio.Event()
        stdout_task = asyncio.create_task(
            self._consume_stdout(
                process,
                marker,
                stdout_path,
                task=task,
                done_event=done_event,
                cancel_event=cancel_event,
            )
        )
        stderr_task = asyncio.create_task(
            self._consume_stderr(
                process,
                stderr_path,
                task=task,
                done_event=done_event,
                cancel_event=cancel_event,
            )
        )

        try:
            return await stdout_task
        finally:
            done_event.set()
            stderr_task.cancel() # ensure stderr is drained
            await asyncio.gather(stderr_task, return_exceptions=True)

    async def _consume_stdout(
        self,
        process: asyncio.subprocess.Process,
        marker: str,
        target: Path,
        *,
        task: Task,
        done_event: asyncio.Event,
        cancel_event: asyncio.Event,
    ) -> int:
        assert process.stdout is not None
        marker_bytes = marker.encode()
        with target.open("ab") as handle:
            while True:
                line = await self._readline_with_cancel(
                    process.stdout, cancel_event
                )
                self._debug(f"stdout raw: {line!r}")
                if line is None:
                    continue
                if not line:
                    raise TaskExecutionError("Shell terminated unexpectedly")
                marker_index = line.find(marker_bytes)
                if marker_index != -1:
                    before_marker = line[:marker_index]
                    tail = line[marker_index + len(marker_bytes) :]
                    newline_bytes = b""
                    if tail.endswith(b"\r\n"):
                        newline_bytes = b"\r\n"
                    elif tail.endswith(b"\n"):
                        newline_bytes = b"\n"
                    flushed = before_marker + newline_bytes
                    if flushed:
                        handle.write(flushed)
                        if self._log_streamer:
                            run_id = getattr(task, "run_id", None)
                            await self._log_streamer.emit(
                                task_id=task.id,
                                stream="stdout",
                                data=flushed.decode(errors="ignore"),
                                run_id=run_id,
                            )
                    done_event.set()
                    marker_text = line[marker_index:].decode(errors="ignore")
                    self._debug(f"marker line: {marker_text!r}")
                    return self._parse_marker_line(marker_text, marker)
                handle.write(line)
                if self._log_streamer:
                            run_id = getattr(task, "run_id", None)
                            await self._log_streamer.emit(
                                task_id=task.id,
                                stream="stdout",
                                data=line.decode(errors="ignore"),
                                run_id=run_id,
                            )

    async def _consume_stderr(
        self,
        process: asyncio.subprocess.Process,
        target: Path,
        *,
        task: Task,
        done_event: asyncio.Event,
        cancel_event: asyncio.Event,
    ) -> None:
        assert process.stderr is not None
        with target.open("ab") as handle:
            while True:
                timeout = 0.2 if done_event.is_set() else None
                line = await self._readline_with_cancel(
                    process.stderr, cancel_event, timeout=timeout
                )
                self._debug(f"stderr raw: {line!r}")
                if line is None:
                    if done_event.is_set():
                        break
                    continue
                if not line:
                    if done_event.is_set():
                        break
                    raise TaskExecutionError("Shell stderr closed unexpectedly")
                text = line.decode(errors="ignore")
                handle.write(line)
                if self._log_streamer:
                    run_id = getattr(task, "run_id", None)
                    await self._log_streamer.emit(
                        task_id=task.id,
                        stream="stderr",
                        data=text,
                        run_id=run_id,
                    )

    async def _readline_with_cancel(
        self,
        reader: asyncio.StreamReader,
        cancel_event: asyncio.Event,
        timeout: Optional[float] = None,
    ) -> Optional[bytes]:
        loop = asyncio.get_running_loop()
        line_task = loop.create_task(reader.readline())
        cancel_task = loop.create_task(cancel_event.wait())
        timeout_task: Optional[asyncio.Task] = None
        tasks = {line_task, cancel_task}
        if timeout is not None:
            timeout_task = loop.create_task(asyncio.sleep(timeout))
            tasks.add(timeout_task)

        try:
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        if cancel_task in done:
            for task in pending:
                task.cancel()
            line_task.cancel()
            if timeout_task:
                timeout_task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            await self._handle_cancelled()
            raise TaskExecutionError("Task cancelled", return_code=None)

        if timeout_task and timeout_task in done:
            line_task.cancel()
            cancel_task.cancel()
            await asyncio.gather(line_task, cancel_task, return_exceptions=True)
            return None

        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        return await line_task

    async def _handle_cancelled(self) -> None:
        if not self._process:
            return
        await self._terminate_process(self._process)
        self._process = None
        if self._registered_pid is not None and self._gpu_monitor:
            try:
                self._gpu_monitor.unregister_task_process(self._registered_pid)
            except Exception:
                pass
        self._registered_pid = None

    async def _terminate_process(self, process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return

        if os.name == "nt":
            process.terminate()
        else:
            process.send_signal(signal.SIGTERM)

        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

    def _build_env_wrappers(
        self, env: Dict[str, str]
    ) -> tuple[list[str], list[str]]:
        if not env:
            return ([], [])
        if os.name == "nt":
            setup = [f'set "{key}={value}"' for key, value in env.items()]
            teardown = [f'set "{key}="' for key in env.keys()]
        else:
            from shlex import quote

            setup = [f"export {key}={quote(value)}" for key, value in env.items()]
            teardown = [f"unset {key}" for key in env.keys()]
        return setup, teardown

    def _marker_command(self, marker: str) -> str:
        if os.name == "nt":
            return f'echo {marker} %{self.STATUS_VAR}%'
        return f'printf "{marker} %s\\n" "${self.STATUS_VAR}"'

    def _store_status_command(self) -> str:
        if os.name == "nt":
            return f"set {self.STATUS_VAR}=%errorlevel%"
        return f"{self.STATUS_VAR}=$?"

    def _clear_status_command(self) -> str:
        if os.name == "nt":
            return f"set {self.STATUS_VAR}="
        return f"unset {self.STATUS_VAR}"

    @staticmethod
    def _chain_commands(commands: list[str]) -> str:
        if len(commands) == 1:
            return commands[0]
        return " && ".join(commands)

    def _shell_command(self) -> list[str]:
        if os.name == "nt":
            return ["cmd.exe", "/Q", "/K"]
        shell = os.environ.get("SHELL")
        if shell:
            return [shell, "-i"]
        return ["/bin/sh"]

    def _parse_marker_line(self, line: str, marker: str) -> int:
        try:
            parts = line.strip().split()
            return int(parts[-1])
        except Exception:
            raise TaskExecutionError(f"Invalid marker output: {line}")

    def _debug(self, message: str) -> None:
        if not self._debug_enabled:
            return
        try:
            DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
            with DEBUG_LOG.open("a", encoding="utf-8") as handle:
                handle.write(f"[shell {self.id}] {message}\n")
        except Exception:
            pass


__all__ = ["PersistentShell"]

