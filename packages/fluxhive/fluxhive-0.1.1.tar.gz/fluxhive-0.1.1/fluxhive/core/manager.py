"""High-level interface for submitting and tracking tasks."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Awaitable, Callable, Dict, Optional
from uuid import uuid4
import warnings

from .exceptions import TaskExecutionError
from ..services.gpu_monitor import GPUMonitor
from ..services.gpu_service import GPUService
from .models import CommandGroup, Task, TaskStatus
from .runner import AsyncCommandRunner

if TYPE_CHECKING:
    from .control_plane import TaskLogStreamer
    from .shell import PersistentShell


class TaskManager:
    """Thread-safe task submission and monitoring interface."""

    def __init__(
        self,
        log_dir: Path | str = Path(".agent_logs"),
        max_parallel: int = 2,
        gpu_monitor: Optional[GPUMonitor] = None,
        status_hook: Optional[Callable[[Task], Awaitable[None]]] = None,
        log_streamer: Optional["TaskLogStreamer"] = None,
    ) -> None:
        self.log_dir = Path(log_dir)
        self.max_parallel = max_parallel
        if gpu_monitor is None:
            gpu_monitor = GPUService.instance().monitor
        self._gpu_monitor = gpu_monitor
        self._status_hook = status_hook
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._run_loop,
            name="fluxhive-agent-loop",
            daemon=True,
        )
        self._loop_thread.start()

        self._semaphore = asyncio.run_coroutine_threadsafe(
            self._create_semaphore(), self._loop
        ).result()
        self._runner = AsyncCommandRunner(
            self.log_dir,
            gpu_monitor=self._gpu_monitor,
            log_streamer=log_streamer,
        )
        self._tasks: Dict[str, Task] = {}
        self._cancel_events: Dict[str, asyncio.Event] = {}
        self._futures: Dict[str, asyncio.Future] = {}
        self._shells: Dict[str, "PersistentShell"] = {}
        self._shell_refs: Dict[str, int] = {}
        self._shell_lock = threading.Lock()

    async def _create_semaphore(self) -> asyncio.Semaphore:
        return asyncio.Semaphore(self.max_parallel)

    def submit(
        self,
        command_group: CommandGroup,
        metadata: Optional[dict] = None,
        *,
        run_id: Optional[str] = None,
        task_id: Optional[str] = None,
        use_shell: bool = False,
        shell_id: Optional[str] = None,
    ) -> Task:
        task_kwargs = {}
        if task_id:
            task_kwargs["id"] = task_id
        task = Task(command_group=command_group, metadata=metadata or {}, **task_kwargs)
        # Propagate run_id as a top-level Task attribute (do not store in metadata)
        if run_id is not None:
            task.run_id = run_id
        if shell_id or use_shell:
            task.shell_id = self._acquire_shell(shell_id, command_group.workdir)
        self._tasks[task.id] = task

        cancel_event = asyncio.Event()
        self._cancel_events[task.id] = cancel_event

        future = asyncio.run_coroutine_threadsafe(
            self._execute(task, cancel_event), self._loop
        )
        self._futures[task.id] = future
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task.status in {TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED}:
            return False

        cancel_event = self._cancel_events.get(task_id)
        if cancel_event:
            self._loop.call_soon_threadsafe(cancel_event.set)
        return True

    def shutdown(self) -> None:
        """Stop the background loop."""
        for task_id, cancel_event in list(self._cancel_events.items()):
            self._loop.call_soon_threadsafe(cancel_event.set)
            self._tasks[task_id].mark_finished(TaskStatus.CANCELLED, None)

        for shell in list(self._shells.values()):
            asyncio.run_coroutine_threadsafe(shell.close(), self._loop).result()
        self._shells.clear()
        self._shell_refs.clear()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._loop_thread.join(timeout=5)

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def wait(self, task_id: str, timeout: Optional[float] = None) -> bool:
        future = self._futures.get(task_id)
        if not future:
            return False
        future.result(timeout=timeout)
        return True

    async def _execute(self, task: Task, cancel_event: asyncio.Event) -> None:
        try:
            async with self._semaphore:
                task.mark_running()
                await self._notify_status(task)
                try:
                    shell = self._get_shell(task.shell_id)
                    await self._runner.run(task, cancel_event, shell=shell)
                except TaskExecutionError as exc:
                    task.error = str(exc)
                    new_status = (
                        TaskStatus.CANCELLED
                        if "cancelled" in str(exc).lower()
                        else TaskStatus.FAILED
                    )
                    task.mark_finished(new_status, getattr(exc, "return_code", None))
                    return
                except asyncio.CancelledError:
                    task.mark_finished(TaskStatus.CANCELLED, return_code=None)
                else:
                    task.mark_finished(TaskStatus.SUCCESS, return_code=0)
        finally:
            if task.shell_id:
                shell = self._release_shell(task.shell_id)
                if shell:
                    await shell.close()
            await self._notify_status(task)
            self._futures.pop(task.id, None)
            self._cancel_events.pop(task.id, None)

    async def _notify_status(self, task: Task) -> None:
        if not self._status_hook:
            return
        try:
            await self._status_hook(task)
        except Exception:
            # Status hooks should never break task execution.
            pass

    def append_to_shell(
        self,
        shell_id: str,
        command_group: CommandGroup,
        metadata: Optional[dict] = None,
        *,
        task_id: Optional[str] = None,
    ) -> Task:
        with self._shell_lock:
            exists = shell_id in self._shells
        if not exists:
            raise ValueError(f"Shell '{shell_id}' does not exist")
        return self.submit(
            command_group=command_group,
            metadata=metadata,
            task_id=task_id,
            shell_id=shell_id,
        )

    def _acquire_shell(
        self, shell_id: Optional[str], workdir: Optional[Path]
    ) -> str:
        with self._shell_lock:
            if shell_id and shell_id in self._shells:
                self._shell_refs[shell_id] += 1
                return shell_id
            elif shell_id:
                # warnings.warn(f"Shell '{shell_id}' does not exist")
                raise ValueError(f"Shell '{shell_id}' does not exist")

            new_id = shell_id or uuid4().hex
            shell = self._runner.create_shell(shell_id=new_id, workdir=workdir)
            self._shells[new_id] = shell
            self._shell_refs[new_id] = 1
            return new_id

    def _get_shell(self, shell_id: Optional[str]):
        if not shell_id:
            return None
        with self._shell_lock:
            return self._shells.get(shell_id)

    def _release_shell(self, shell_id: str):
        with self._shell_lock:
            refs = self._shell_refs.get(shell_id)
            if refs is None:
                return None
            refs -= 1
            if refs > 0:
                self._shell_refs[shell_id] = refs
                return None
            self._shell_refs.pop(shell_id, None)
            return self._shells.pop(shell_id, None)


