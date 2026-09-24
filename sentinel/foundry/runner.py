from pathlib import Path

from sentinel.runner import ControlledRunner
from sentinel.schemas.execution import ExecutionResult


class FoundryRunner:
    def __init__(self, runner: ControlledRunner) -> None:
        self.runner = runner

    def build(self, project: Path) -> ExecutionResult:
        return self.runner.run(["forge", "build"], project)

    def exploit(self, project: Path, test_name: str = "testExploit") -> ExecutionResult:
        return self.runner.run(["forge", "test", "--match-test", test_name], project)

    def regression(self, project: Path, test_name: str = "testExploit") -> ExecutionResult:
        return self.runner.run(["forge", "test", "--no-match-test", test_name], project)
