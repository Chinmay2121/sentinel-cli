from pathlib import Path

import typer

from sentinel.config import settings
from sentinel.graph.workflow import build_workflow
from sentinel.reporting.markdown import write_report
from sentinel.schemas.state import RuntimeState

app = typer.Typer(help="Sentinel: closed-loop smart-contract security research CLI.")


@app.callback()
def main() -> None:
    """Run Sentinel commands."""


@app.command()
def scan(
    project: Path = typer.Argument(..., exists=True, file_okay=False),  # noqa: B008
    output: Path = typer.Option(settings.output_dir, "--output"),  # noqa: B008
    max_retries: int = typer.Option(settings.max_retries, "--max-retries", min=0, max=5),
    mock: bool = typer.Option(False, "--mock"),
    verbose: bool = typer.Option(False, "--verbose"),
    no_docker: bool = typer.Option(False, "--no-docker"),
) -> None:
    del verbose, no_docker
    if not (project / "foundry.toml").is_file():
        raise typer.BadParameter("Project must contain foundry.toml")
    state = RuntimeState(project_path=str(project.resolve()), mock_mode=mock, max_retries=max_retries)
    state.retry_count = 0
    state.feedback.append(f"Maximum patch retries configured: {max_retries}")
    result = build_workflow().invoke(state)
    final_state = RuntimeState.model_validate(result)
    report_path = write_report(final_state, output)
    typer.echo(f"Sentinel completed: {final_state.final_verification_state}")
    typer.echo(f"Audit report: {report_path}")


if __name__ == "__main__":
    app()
