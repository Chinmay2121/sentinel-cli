from pathlib import Path

import typer

from sentinel.config import settings
from sentinel.service import run_scan

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
    scout_only: bool = typer.Option(False, "--scout-only", help="Run Slither/Mythril triage without generating tests or patches."),
    verbose: bool = typer.Option(False, "--verbose"),
    no_docker: bool = typer.Option(False, "--no-docker"),
) -> None:
    del verbose, no_docker
    if scout_only:
        typer.echo("Starting tool-only Scout scan (Slither and bounded Mythril); this can take about a minute.")
    else:
        typer.echo("Starting agentic scan: Scout, Red Team, Blue Team, and Judge.")
    try:
        final_state = run_scan(project, output=output, max_retries=max_retries, mock=mock, scout_only=scout_only)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Sentinel completed: {final_state.final_verification_state}")
    typer.echo(f"Audit report: {final_state.final_report_path}")
    if scout_only and final_state.final_verification_state != "scout_complete":
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
