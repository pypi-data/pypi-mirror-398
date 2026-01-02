import asyncio
import os
import sys
from pathlib import Path

import pytest

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from core.exceptions import TaskExecutionError
from core.models import CommandGroup, Task
from core.shell import PersistentShell


def _python_command(code: str) -> str:
    escaped = code.replace('"', r"\"")
    return f'"{sys.executable}" -c "{escaped}"'


def _change_dir_command(path: Path) -> str:
    if os.name == "nt":
        return f'cd /d "{path}"'
    return f'cd "{path}"'


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    if os.name == "nt":
        env.setdefault("PROMPT", "")
    else:
        env.setdefault("PS1", "")
    return env


def _new_task(commands: list[str]) -> Task:
    return Task(command_group=CommandGroup(commands=commands))


def _log_paths(tmp_path: Path, name: str) -> tuple[Path, Path]:
    return tmp_path / f"{name}.stdout.log", tmp_path / f"{name}.stderr.log"


def _run_shell_test(tmp_path: Path, coro_func):
    async def _wrapper():
        shell = PersistentShell(env=_base_env(), workdir=tmp_path)
        try:
            await coro_func(shell)
        finally:
            await shell.close()

    asyncio.run(_wrapper())


def test_persistent_shell_executes_commands(tmp_path: Path):
    stdout_path, stderr_path = _log_paths(tmp_path, "basic")
    command = _python_command("print('hello-shell')")
    task = _new_task([command])

    async def scenario(shell: PersistentShell):
        await shell.run(
            task=task,
            command_group=task.command_group,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            cancel_event=asyncio.Event(),
        )

    _run_shell_test(tmp_path, scenario)

    assert "hello-shell" in stdout_path.read_text()
    assert stderr_path.read_text() == ""


def test_shell_preserves_context_between_runs(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()

    async def scenario(shell: PersistentShell):
        change_dir_task = _new_task([_change_dir_command(nested)])
        stdout_path, stderr_path = _log_paths(tmp_path, "cd")
        await shell.run(
            task=change_dir_task,
            command_group=change_dir_task.command_group,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            cancel_event=asyncio.Event(),
        )

        check_code = (
            "from pathlib import Path; import sys; "
            f"print(Path.cwd().resolve()); "
            f"sys.exit(0 if Path.cwd().resolve() == Path(r\"{nested}\").resolve() else 1)"
        )
        check_task = _new_task([_python_command(check_code)])
        stdout_path, stderr_path = _log_paths(tmp_path, "check")
        await shell.run(
            task=check_task,
            command_group=check_task.command_group,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            cancel_event=asyncio.Event(),
        )

    _run_shell_test(tmp_path, scenario)

    check_stdout = (tmp_path / "check.stdout.log").read_text()
    assert str(nested.resolve()) in check_stdout


def test_shell_raises_for_non_zero_exit(tmp_path: Path):
    stdout_path, stderr_path = _log_paths(tmp_path, "failure")
    failing_task = _new_task(["exit 1" if os.name == "nt" else "false"])

    async def scenario(shell: PersistentShell):
        with pytest.raises(TaskExecutionError):
            await shell.run(
                task=failing_task,
                command_group=failing_task.command_group,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                cancel_event=asyncio.Event(),
            )

    _run_shell_test(tmp_path, scenario)

