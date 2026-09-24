import shutil
from pathlib import Path

from sentinel.config import settings
from sentinel.graph.workflow import build_workflow
from sentinel.reporting.markdown import write_report
from sentinel.schemas.state import RuntimeState


def run_scan(
    project: Path,
    *,
    output: Path | None = None,
    max_retries: int | None = None,
    mock: bool = False,
    scout_only: bool = False,
) -> RuntimeState:
    """Run a local Foundry audit and persist its report ledger.

    Callers pass paths, never commands. The workflow's allowlisted runner owns
    every subprocess invocation.
    """
    project = project.resolve()
    if not project.is_dir() or not (project / "foundry.toml").is_file():
        raise ValueError("Project must be a directory containing foundry.toml")
    state = RuntimeState(
        project_path=str(project),
        mock_mode=mock,
        max_retries=settings.max_retries if max_retries is None else max_retries,
        scout_only=scout_only,
    )
    state.feedback.append(f"Maximum patch retries configured: {state.max_retries}")
    workspace: Path | None = None
    try:
        final_state = RuntimeState.model_validate(build_workflow().invoke(state))
        workspace = Path(final_state.workspace_path) if final_state.workspace_path else None
        final_state.workspace_path = None
        write_report(final_state, output or settings.output_dir)
        return final_state
    finally:
        if workspace:
            shutil.rmtree(workspace, ignore_errors=True)
