"""Explicit local release-gate policy evaluation."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from sentinel.comparison import compare_ledgers
from sentinel.schemas.state import RuntimeState

RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}


@dataclass(frozen=True)
class GateDecision:
    status: str
    reasons: list[str]


def load_policy(path: Path) -> dict[str, object]:
    document = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    if not isinstance(document, dict):
        raise TypeError("Policy must be a mapping")
    return document


def evaluate_policy(current: RuntimeState, policy: dict[str, object], baseline: RuntimeState | None = None) -> GateDecision:
    threshold = str(policy.get("block_severity", "critical")).lower()
    minimum_rank = RANK.get(threshold, RANK["critical"])
    findings = current.findings
    if baseline:
        introduced = compare_ledgers(baseline, current)["introduced"]
        finding_ids = {item["id"] for item in introduced}
        findings = [item for item in findings if item.id in finding_ids]
    reasons = [
        f"{item.severity} finding: {item.detector} at {item.file or 'unknown'}"
        for item in findings
        if item.status.value not in {"discarded", "verified"} and RANK.get(item.severity, 0) >= minimum_rank
    ]
    if policy.get("require_complete_coverage", False) and any(run.status not in {"completed", "skipped"} for run in current.analyzer_runs):
        reasons.append("scanner coverage is incomplete")
    return GateDecision(status="blocked" if reasons else "passed", reasons=reasons)
