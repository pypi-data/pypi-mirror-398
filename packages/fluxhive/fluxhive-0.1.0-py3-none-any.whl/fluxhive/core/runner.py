"""Async subprocess runner with logging and cancellation."""

from __future__ import annotations

import asyncio
import os
import signal
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

from .exceptions import TaskExecutionError
from ..services.gpu_monitor import GPUMonitor
from .models import CommandGroup, Task
from ..utils.shell import PersistentShell

if TYPE_CHECKING:
    from .control_plane import TaskLogStreamer


class AsyncCommandRunner:
    """Executes Task command groups using asyncio subprocesses."""

    def __init__(
        self,
        log_dir: Path,
        base_env: Optional[Dict[str, str]] = None,
        gpu_monitor: Optional[GPUMonitor] = None,
        log_streamer: Optional["TaskLogStreamer"] = None,
    ) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.base_env = base_env or {}
        self._gpu_monitor = gpu_monitor
        self._log_streamer = log_streamer

    async def run(
        self,
        task: Task,
        cancel_event: asyncio.Event,
        shell: Optional[PersistentShell] = None,
    ) -> None:
        """Run commands for the task and persist logs."""

        # Include run id in filenames if present in task metadata to avoid collisions
        run_id = getattr(task, "run_id", None)

        if run_id:
            stdout_path = self.log_dir / f"{task.id}.{run_id}.stdout.log"
            stderr_path = self.log_dir / f"{task.id}.{run_id}.stderr.log"
        else:
            stdout_path = self.log_dir / f"{task.id}.stdout.log"
            stderr_path = self.log_dir / f"{task.id}.stderr.log"
        task.stdout_path = stdout_path
        task.stderr_path = stderr_path

        if shell:
            try:
                await shell.run(
                    task=task,
                    command_group=task.command_group,
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    cancel_event=cancel_event,
                )
            except asyncio.CancelledError:
                raise
            except TaskExecutionError:
                raise
            except Exception as exc:
                raise TaskExecutionError(str(exc)) from exc
            return

        env = os.environ.copy()
        env.update(self.base_env)
        env.update(task.command_group.env)

        combined_command = self._chain_commands(task.command_group.commands)

        try:
            await self._execute_command(
                command=combined_command,
                env=env,
                workdir=task.command_group.workdir,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                cancel_event=cancel_event,
                task=task,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise TaskExecutionError(str(exc)) from exc

    async def _execute_command(
        self,
        command: str,
        env: Dict[str, str],
        workdir: Optional[Path],
        stdout_path: Path,
        stderr_path: Path,
        cancel_event: asyncio.Event,
        task: Task,
    ) -> None:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(workdir) if workdir else None,
        )

        if self._gpu_monitor and self._gpu_monitor.available:
            try:
                self._gpu_monitor.register_task_process(
                    task_id=task.id,
                    pid=process.pid,
                    metadata={
                        "command": command,
                        "task_metadata": dict(task.metadata),
                        "workdir": str(workdir) if workdir else None,
                    },
                )
                registered_pid = process.pid
            except Exception:
                registered_pid = None
        else:
            registered_pid = None

        stdout_task = asyncio.create_task(
            self._drain_stream(
                process.stdout,
                stdout_path,
                task=task,
                stream_name="stdout",
            )
        )
        stderr_task = asyncio.create_task(
            self._drain_stream(
                process.stderr,
                stderr_path,
                task=task,
                stream_name="stderr",
            )
        )

        wait_process = asyncio.create_task(process.wait())
        wait_cancel = asyncio.create_task(cancel_event.wait())

        try:
            done, _ = await asyncio.wait(
                [wait_process, wait_cancel],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if wait_cancel in done:
                await self._terminate_process(process)
                raise TaskExecutionError("Task cancelled", return_code=None)

            return_code = await wait_process

            if return_code != 0:
                raise TaskExecutionError(
                    f"Command '{command}' failed with code {return_code}",
                    return_code=return_code,
                )
        finally:
            wait_process.cancel()
            wait_cancel.cancel()
            await asyncio.gather(
                wait_process, wait_cancel, return_exceptions=True
            )
            await asyncio.gather(
                stdout_task, stderr_task, return_exceptions=True
            )
            if registered_pid is not None and self._gpu_monitor:
                self._gpu_monitor.unregister_task_process(registered_pid)

    @staticmethod
    def _chain_commands(commands: list[str]) -> str:
        """Chain multiple commands so they run in a single shell context."""
        if len(commands) == 1:
            return commands[0]

        # Use && to ensure later commands only run if previous ones succeed.
        return " && ".join(commands)

    def create_shell(
        self, *, shell_id: Optional[str] = None, workdir: Optional[Path] = None
    ) -> PersistentShell:
        env = os.environ.copy()
        env.update(self.base_env)
        if os.name != "nt":
            env.setdefault("PS1", "")
        else:
            env.setdefault("PROMPT", "")
        return PersistentShell(
            shell_id=shell_id,
            env=env,
            workdir=workdir,
            log_streamer=self._log_streamer,
            gpu_monitor=self._gpu_monitor,
        )

    async def _drain_stream(
        self,
        stream: asyncio.StreamReader,
        target: Path,
        *,
        task: Task,
        stream_name: str,
    ) -> None:
        with target.open("ab") as handle:
            while True:
                chunk = await stream.readline()
                if not chunk:
                    break
                handle.write(chunk)
                if self._log_streamer:
                    # Forward run_id when available so control plane can route logs per-run
                    run_id = getattr(task, "run_id", None)
                    await self._log_streamer.emit(
                        task_id=task.id,
                        stream=stream_name,
                        data=chunk.decode(errors="ignore"),
                        run_id=run_id,
                    )

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


