"""Reproducible, label-aware experiment execution for Sentinel research claims."""
from __future__ import annotations

import json
import platform
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Literal

from pydantic import BaseModel, Field

from sentinel.benchmark import summarize_benchmark
from sentinel.config import settings
from sentinel.schemas.state import RuntimeState
from sentinel.service import run_scan

GroundTruth = Literal["vulnerable", "clean", "unknown"]


class ExperimentCase(BaseModel):
    id: str
    project_path: str
    group: Literal["fixture", "held_out", "audit", "clean"]
    vulnerability_class: str = "unspecified"
    ground_truth: GroundTruth = "unknown"


class ExperimentManifest(BaseModel):
    name: str
    cases: list[ExperimentCase] = Field(min_length=1)


class ExperimentProfile(BaseModel):
    name: str
    enabled_analyzers: list[Literal["slither", "mythril"]] = Field(default_factory=lambda: ["slither", "mythril"])
    scout_only: bool = False
    max_retries: int = 5


PROFILES = {
    "slither": ExperimentProfile(name="slither", enabled_analyzers=["slither"], scout_only=True),
    "mythril": ExperimentProfile(name="mythril", enabled_analyzers=["mythril"], scout_only=True),
    "scout-union": ExperimentProfile(name="scout-union", scout_only=True),
    "sentinel-no-red-team": ExperimentProfile(name="sentinel-no-red-team", scout_only=True),
    "sentinel-no-retry": ExperimentProfile(name="sentinel-no-retry", max_retries=0),
    "sentinel-full": ExperimentProfile(name="sentinel-full"),
}


def load_manifest(path: Path) -> ExperimentManifest:
    return ExperimentManifest.model_validate_json(path.read_text(encoding="utf-8"))


def run_experiment(
    manifest_path: Path,
    output_dir: Path,
    profile_name: str,
    *,
    limit: int | None = None,
    mock: bool = False,
    scan: Callable[..., RuntimeState] = run_scan,
) -> dict[str, object]:
    """Run only declared local Foundry projects and report metrics from known labels."""
    if profile_name not in PROFILES:
        raise ValueError(f"Unknown experiment profile: {profile_name}")
    manifest = load_manifest(manifest_path)
    profile = PROFILES[profile_name]
    selected = manifest.cases[:limit] if limit is not None else manifest.cases
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for case in selected:
        project = (manifest_path.parent / case.project_path).resolve() if not Path(case.project_path).is_absolute() else Path(case.project_path)
        started = monotonic()
        try:
            state = scan(
                project, output=output_dir / "ledgers" / profile.name / case.id,
                mock=mock, scout_only=profile.scout_only, max_retries=profile.max_retries,
                experiment_profile=profile.name, enabled_analyzers=profile.enabled_analyzers,
            )
            scan_error = ""
        except ValueError as exc:
            state = None
            scan_error = str(exc)
        detected = bool(state and any(item.source != "novelty-heuristic" for item in state.findings))
        confirmed = bool(state and state.exploit_confirmed)
        verified = bool(state and state.final_verification_state == "verified")
        coverage_complete = bool(state and state.analyzer_runs and all(run.status in {"completed", "skipped"} for run in state.analyzer_runs))
        records.append({
            "case_id": case.id, "group": case.group, "vulnerability_class": case.vulnerability_class,
            "ground_truth": case.ground_truth, "detected": detected, "confirmed": confirmed,
            "verified": verified, "coverage_complete": coverage_complete,
            "outcome": state.final_verification_state if state else "invalid_project",
            "findings": len(state.findings) if state else 0,
            "retries": state.retry_count if state else 0,
            "duration_seconds": round(monotonic() - started, 3),
            "ledger": state.final_report_path if state else None, "error": scan_error,
        })
    known = [row for row in records if row["ground_truth"] != "unknown"]
    measured = [row for row in known if row["coverage_complete"]]
    tp = sum(row["detected"] and row["ground_truth"] == "vulnerable" for row in measured)
    fp = sum(row["detected"] and row["ground_truth"] == "clean" for row in measured)
    fn = sum(not row["detected"] and row["ground_truth"] == "vulnerable" for row in measured)
    tn = sum(not row["detected"] and row["ground_truth"] == "clean" for row in measured)
    metrics = summarize_benchmark(int(tp), int(fp), int(fn), int(tn)).model_dump(mode="json")
    clean_controls = sum(row["ground_truth"] == "clean" for row in measured)
    if not clean_controls:
        metrics["precision"] = None
        metrics["f1_score"] = None
        metrics["false_positive_rate"] = None
    by_class: dict[str, object] = {}
    for label in sorted({str(row["vulnerability_class"]) for row in known}):
        rows = [row for row in known if row["vulnerability_class"] == label]
        by_class[label] = {
            "evaluated": len(rows), "detected": sum(bool(row["detected"]) for row in rows),
            "confirmed": sum(bool(row["confirmed"]) for row in rows), "verified": sum(bool(row["verified"]) for row in rows),
        }
    report = {
        "experiment": manifest.name, "profile": profile.model_dump(mode="json"),
        "created_at": datetime.now(UTC).isoformat(),
        "reproducibility": {
            "platform": platform.platform(), "python": platform.python_version(),
            "llm_provider": settings.llm_provider, "scout_model": settings.scout_model,
            "red_team_model": settings.red_team_model, "blue_team_model": settings.blue_team_model,
            "command_timeout_seconds": settings.command_timeout_seconds,
        },
        "metrics": metrics,
        "metric_scope": {
            "labeled_cases": len(known),
            "completed_labeled_cases": len(measured),
            "incomplete_labeled_cases": len(known) - len(measured),
            "clean_controls": clean_controls,
            "precision_and_f1_available": bool(clean_controls),
        },
        "poC_success_rate": sum(bool(row["confirmed"]) for row in records) / sum(row["ground_truth"] == "vulnerable" for row in records) if any(row["ground_truth"] == "vulnerable" for row in records) else None,
        "validated_repair_rate": sum(bool(row["verified"]) for row in records) / sum(bool(row["confirmed"]) for row in records) if any(bool(row["confirmed"]) for row in records) else None,
        "average_retries": sum(int(row["retries"]) for row in records) / len(records) if records else None,
        "average_duration_seconds": sum(float(row["duration_seconds"]) for row in records) / len(records) if records else None,
        "coverage_complete_cases": sum(bool(row["coverage_complete"]) for row in records),
        "unlabeled_cases": len(records) - len(known), "by_vulnerability_class": by_class, "cases": records,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"sentinel-experiment-{profile.name}-{stamp}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(path)
    return report
