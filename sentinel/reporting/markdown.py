from datetime import UTC, datetime
from pathlib import Path

from sentinel.schemas.state import RuntimeState


def render_report(state: RuntimeState) -> str:
    lines = [
        "# Sentinel Security Audit",
        "",
        "## Project",
        f"`{state.project_path}`",
        "",
        "## Execution Summary",
        f"- Final state: **{state.final_verification_state}**",
        f"- Source files: {len(state.source_files)}",
        f"- Runtime: {state.gas_metrics.get('duration_seconds', 'not measured')}",
        "",
        "## Static Analysis Findings",
        "| ID | Source | Severity | Location | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for finding in state.findings:
        location = f"{finding.file}:{finding.line}" if finding.file else "unknown"
        lines.append(f"| {finding.id} | {finding.source} | {finding.severity} | {location} | {finding.status} |")
    lines.extend([
        "",
        "## Semantic Scout Analysis",
        *[f"- {result}" for result in state.scout_results],
        "",
        "## Judge Verification",
        f"- Build: {state.judge_result.build_passed if state.judge_result else 'not run'}",
        f"- Exploit defense: {state.judge_result.exploit_neutralized if state.judge_result else 'not run'}",
        f"- Regression: {state.judge_result.regression_passed if state.judge_result else 'not run'}",
        f"- Verified: {state.judge_result.verified if state.judge_result else 'not run'}",
        "",
        "## Retry History",
        f"Attempts recorded: {len(state.retry_history)}",
        "",
        "## Gas Comparison",
        "Gas comparison unavailable for this execution unless measured by Foundry.",
        "",
        "## Final Outcome",
        f"**{state.final_verification_state}**",
        "",
    ])
    return "\n".join(lines)


def write_report(state: RuntimeState, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output_dir / f"sentinel-report-{stamp}.md"
    report_path.write_text(render_report(state), encoding="utf-8")
    state.final_report_path = str(report_path)
    return report_path
