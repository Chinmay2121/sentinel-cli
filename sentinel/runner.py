import subprocess
import time
from collections.abc import Sequence
from pathlib import Path

from sentinel.schemas.execution import ExecutionResult

ALLOWED_COMMANDS = frozenset({"solc", "slither", "aderyn", "forge", "cast", "docker"})


class ControlledRunner:
    """Run only framework-owned local developer tools; never executes LLM commands."""

    def __init__(self, timeout_seconds: int = 120) -> None:
        self.timeout_seconds = timeout_seconds

    def run(self, command: Sequence[str], cwd: Path) -> ExecutionResult:
        if not command or Path(command[0]).name not in ALLOWED_COMMANDS:
            raise ValueError(f"Command is not allowlisted: {command!r}")
        cwd = cwd.resolve()
        if not cwd.is_dir():
            raise ValueError(f"Working directory does not exist: {cwd}")
        started = time.monotonic()
        try:
            completed = subprocess.run(
                list(command), cwd=cwd, capture_output=True, text=True,
                timeout=self.timeout_seconds, check=False,
            )
            return ExecutionResult(
                command=list(command), cwd=str(cwd), exit_code=completed.returncode,
                stdout=completed.stdout, stderr=completed.stderr,
                duration_seconds=time.monotonic() - started,
                success=completed.returncode == 0,
            )
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(
                command=list(command), cwd=str(cwd), exit_code=None,
                stdout=exc.stdout or "", stderr=exc.stderr or "",
                duration_seconds=time.monotonic() - started, timed_out=True,
            )
        except OSError as exc:
            return ExecutionResult.failed(list(command), str(cwd), str(exc))
