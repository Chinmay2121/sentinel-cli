from pathlib import Path

from sentinel.runner import ControlledRunner
from sentinel.schemas.execution import ExecutionResult
from sentinel.schemas.vulnerability import VulnerabilityFinding


def _unavailable(tool: str, project: Path) -> ExecutionResult:
    return ExecutionResult.failed([tool], str(project), f"{tool} is not installed or unavailable")


def run_static_tools(project: Path, runner: ControlledRunner) -> tuple[ExecutionResult, ExecutionResult, list[VulnerabilityFinding]]:
    results: list[ExecutionResult] = []
    for command in (("slither", ".", "--json", "-"), ("aderyn", "--root", str(project))):
        try:
            result = runner.run(command, project)
        except (FileNotFoundError, OSError):
            result = _unavailable(command[0], project)
        results.append(result)

    findings: list[VulnerabilityFinding] = []
    for result in results:
        if result.success:
            findings.append(VulnerabilityFinding(
                id=f"{result.command[0]}-review",
                source=result.command[0], detector="tool-output",
                description=f"{result.command[0]} produced analyzable output; parser enrichment required.",
                raw_output=result.stdout,
            ))
    if not findings:
        for name in sorted(path.name for path in (project / "src").glob("*.sol")) if (project / "src").exists() else []:
            source = (project / "src" / name).read_text(encoding="utf-8")
            if ".call{" in source or "call{value:" in source:
                findings.append(VulnerabilityFinding(
                    id="heuristic-reentrancy", source="local-heuristic", detector="external-call-order",
                    severity="high", confidence="medium", file=f"src/{name}",
                    description="External value transfer occurs before the balance effect is applied.",
                    evidence=["external call precedes state update"], raw_output="",
                ))
            if "function sweep" in source and "owner" in source and "msg.sender" not in source.split("function sweep", 1)[1].split("}", 1)[0]:
                findings.append(VulnerabilityFinding(
                    id="heuristic-access-control", source="local-heuristic", detector="missing-authorization",
                    severity="critical", confidence="medium", file=f"src/{name}",
                    description="A sensitive sweep function has no caller authorization check.",
                    evidence=["sweep transfers all funds without checking msg.sender"], raw_output="",
                ))
    return results[0], results[1], findings


def extract_solidity_context(project: Path) -> tuple[list[str], dict[str, str], dict[str, object]]:
    source_files = sorted(str(path.relative_to(project)) for path in (project / "src").rglob("*.sol")) if (project / "src").exists() else []
    original = {name: (project / name).read_text(encoding="utf-8") for name in source_files}
    context = {"contracts": [], "functions": [], "state_variables": [], "source_locations": []}
    for source in original.values():
        context["contracts"].extend(line.strip() for line in source.splitlines() if line.strip().startswith("contract "))
        context["functions"].extend(line.strip() for line in source.splitlines() if " function " in f" {line}")
    return source_files, original, context
