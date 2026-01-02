import os
import sys
import time
from pathlib import Path

import pytest

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from core.manager import TaskManager
from core.models import CommandGroup, TaskStatus


def python_command(code: str) -> str:
    escaped = code.replace('"', r'\"')
    return f'"{sys.executable}" -c "{escaped}"'


def change_dir_command(path: Path) -> str:
    if os.name == "nt":
        return f'cd /d "{path}"'
    return f'cd "{path}"'


@pytest.fixture()
def manager(tmp_path: Path):
    mgr = TaskManager(log_dir=tmp_path / "logs", max_parallel=2)
    # mgr = TaskManager(max_parallel=2)
    yield mgr
    mgr.shutdown()


def test_task_completes_successfully(manager: TaskManager):
    command = python_command("print('hello')")
    task = manager.submit(CommandGroup(commands=[command]))

    assert manager.wait(task.id, timeout=15)

    assert task.status == TaskStatus.SUCCESS
    assert task.return_code == 0
    assert task.stdout_path and task.stdout_path.exists()
    assert task.stderr_path and task.stderr_path.exists()
    assert "hello" in task.stdout_path.read_text()


def test_task_can_be_cancelled(manager: TaskManager):
    command = python_command("import time; time.sleep(10)")
    task = manager.submit(CommandGroup(commands=[command]))

    # ensure the task has time to start
    time.sleep(0.5)
    assert manager.cancel(task.id)

    assert manager.wait(task.id, timeout=15)
    assert task.status == TaskStatus.CANCELLED


def test_commands_share_single_shell_context(manager: TaskManager, tmp_path: Path):
    workdir = tmp_path
    nested = workdir / "nested"
    nested.mkdir()

    change_dir = change_dir_command(nested)

    check_command = python_command(
        (
            "from pathlib import Path; import sys; "
            f"expected = Path(r\"{nested}\").resolve(); "
            "current = Path.cwd().resolve(); "
            "print(current); "
            "sys.exit(0 if current == expected else 1)"
        )
    )

    task = manager.submit(
        CommandGroup(
            commands=[change_dir, check_command],
            workdir=workdir,
        )
    )

    assert manager.wait(task.id, timeout=15)
    assert task.status == TaskStatus.SUCCESS
    
def test_commands_share_single_shell_context2(manager: TaskManager, tmp_path: Path):
    workdir = tmp_path
    nested = workdir / "nested"
    nested.mkdir()

    change_dir = change_dir_command(nested)

    check_commands = [
        "cd ..",
        "cd",
        "cd ..",
        "cd",
    ]

    task = manager.submit(
        CommandGroup(
            commands=check_commands,
            workdir=workdir,
        )
    )

    assert manager.wait(task.id, timeout=15)
    assert task.status == TaskStatus.SUCCESS


def test_shell_reuse_preserves_working_directory(
    manager: TaskManager, tmp_path: Path
):
    nested = tmp_path / "persistent"
    nested.mkdir()

    change_dir = change_dir_command(nested)
    task1 = manager.submit(
        CommandGroup(commands=[change_dir], workdir=tmp_path),
        use_shell=True,
    )
    assert task1.shell_id

    check_cwd = python_command(
        (
            "from pathlib import Path; import sys; "
            f"expected = Path(r\"{nested}\").resolve(); "
            "current = Path.cwd().resolve(); "
            "print(current); "
            "sys.exit(0 if current == expected else 1)"
        )
    )

    task2 = manager.append_to_shell(
        task1.shell_id,
        CommandGroup(commands=[check_cwd]),
    )

    assert manager.wait(task1.id, timeout=15)
    assert manager.wait(task2.id, timeout=15)
    assert task1.status == TaskStatus.SUCCESS
    assert task2.status == TaskStatus.SUCCESS
    assert task2.stdout_path and str(nested.resolve()) in task2.stdout_path.read_text()


def test_shell_executes_multiple_command_groups(manager: TaskManager, tmp_path: Path):
    target_file = tmp_path / "sequence.txt"

    def append_line(value: int) -> str:
        return python_command(
            (
                "from pathlib import Path; "
                f"path = Path(r\"{target_file}\"); "
                "path.parent.mkdir(parents=True, exist_ok=True); "
                f"with path.open('a') as handle: handle.write('{value}\\n')"
            )
        )

    task1 = manager.submit(
        CommandGroup(commands=[append_line(1)]),
        use_shell=True,
    )
    shell_id = task1.shell_id
    assert shell_id

    task2 = manager.append_to_shell(
        shell_id,
        CommandGroup(commands=[append_line(2)]),
    )
    task3 = manager.append_to_shell(
        shell_id,
        CommandGroup(commands=[append_line(3)]),
    )

    for task in (task1, task2, task3):
        assert manager.wait(task.id, timeout=15)
        assert task.status == TaskStatus.SUCCESS

    assert target_file.read_text() == "1\n2\n3\n"


def test_shell_auto_cleanup_after_tasks_finish(
    manager: TaskManager, tmp_path: Path
):
    task = manager.submit(
        CommandGroup(commands=[python_command("print('done')")]),
        use_shell=True,
    )
    shell_id = task.shell_id
    assert shell_id in manager._shells

    assert manager.wait(task.id, timeout=15)
    assert task.status == TaskStatus.SUCCESS

    # Allow the manager loop to finish closing the shell if needed.
    deadline = time.time() + 5
    while shell_id in manager._shells and time.time() < deadline:
        time.sleep(0.05)

    assert shell_id not in manager._shells
