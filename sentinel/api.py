"""Local-only review API for Sentinel reports and scan execution."""
from pathlib import Path

import typer
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from sentinel.config import settings
from sentinel.schemas.state import RuntimeState
from sentinel.service import run_scan

app = FastAPI(title="Sentinel Local Review API", version="0.1.0")


class ScanRequest(BaseModel):
    project_path: str = Field(min_length=1)
    mock: bool = False
    scout_only: bool = False
    max_retries: int = Field(default=settings.max_retries, ge=0, le=5)


class ScanResponse(BaseModel):
    final_state: str
    report_path: str | None
    ledger_name: str | None
    findings: int
    confirmed: int
    feedback: list[str]


def _reports() -> list[Path]:
    output = settings.output_dir.resolve()
    return sorted(output.glob("sentinel-report-*.json"), reverse=True) if output.is_dir() else []


def _response(state: RuntimeState) -> ScanResponse:
    return ScanResponse(
        final_state=state.final_verification_state,
        report_path=state.final_report_path,
        ledger_name=Path(state.final_report_path).with_suffix(".json").name if state.final_report_path else None,
        findings=len(state.findings),
        confirmed=sum(f.status.value == "confirmed" for f in state.findings),
        feedback=state.feedback,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "scope": "local-only"}


@app.post("/scans", response_model=ScanResponse)
def create_scan(request: ScanRequest) -> ScanResponse:
    try:
        state = run_scan(
            Path(request.project_path), mock=request.mock,
            scout_only=request.scout_only, max_retries=request.max_retries,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _response(state)


@app.get("/scans")
def list_scans() -> list[ScanResponse]:
    records: list[ScanResponse] = []
    for path in _reports():
        try:
            records.append(_response(RuntimeState.model_validate_json(path.read_text(encoding="utf-8"))))
        except ValueError:
            continue
    return records


@app.get("/scans/{report_name}")
def get_scan(report_name: str) -> RuntimeState:
    if Path(report_name).name != report_name or not report_name.endswith(".json"):
        raise HTTPException(status_code=404, detail="Report not found")
    path = settings.output_dir.resolve() / report_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    return RuntimeState.model_validate_json(path.read_text(encoding="utf-8"))


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(Path(__file__).with_name("web") / "index.html")


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the API on loopback by default; it is not an authentication service."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    typer.run(main)
