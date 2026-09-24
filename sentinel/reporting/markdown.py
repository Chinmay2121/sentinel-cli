from datetime import UTC, datetime
from pathlib import Path

from sentinel.schemas.state import RuntimeState


def _tool_message(run) -> str:
    if run.status == "completed":
        return f"{run.tool} finished and reported {run.finding_count} candidate(s)."
    detail = next((item for item in run.diagnostics if item), "No diagnostic was returned.")
    compact = " ".join(detail.splitlines()[:2])[:360]
    return f"{run.tool} did not complete ({run.status}): {compact}"


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
        "## Pipeline Timeline",
        f"- **1. Scout:** {'completed' if state.analyzer_runs and all(run.status == 'completed' for run in state.analyzer_runs) else 'incomplete'} — {len(state.findings)} candidate(s) recorded.",
        f"- **2. Red Team:** {'PoC confirmed' if state.exploit_confirmed else 'not confirmed'} — {'exploit test created' if state.exploit_artifact else 'no exploit test created'}.",
        f"- **3. Blue Team:** {'patch proposed' if state.patch_artifact else 'no patch proposed'}.",
        f"- **4. Judge:** {'verified' if state.judge_result and state.judge_result.verified else 'not run or not verified'}.",
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
        "## Analyzer Coverage",
        *[f"- **{run.tool}** / `{run.target}`: {_tool_message(run)}" for run in state.analyzer_runs],
        "",
        "## Diagnostics",
        *([f"- {message}" for message in state.feedback] or ["- No workflow diagnostics."]),
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
        "## Exploit Artifact",
        f"- Test file: {state.exploit_artifact.test_file if state.exploit_artifact else 'not generated'}",
        "```solidity",
        state.exploit_source or "No exploit source was generated.",
        "```",
        "",
        "## Proposed Patch",
        "```diff",
        state.patch_diff or "No patch was generated.",
        "```",
        "",
        "## Retry History",
        f"Attempts recorded: {len(state.retry_history)}",
        "",
        "## Gas Comparison",
        "Gas comparison unavailable for this execution unless measured by Foundry.",
        "",
        "## How to read this report",
        "- A **candidate** is a scanner or fixture pattern, not a proven exploit.",
        "- **confirmed** means the Red Team's Forge test reproduced the impact.",
        "- **verified** means the Judge built the patched copy, the exploit test failed, and the other tests passed.",
        "- **execution_unavailable** or **analysis_incomplete** means install/configure the listed local tool before treating the absence of findings as meaningful.",
        "",
        "## Final Outcome",
        f"**{state.final_verification_state}**",
        "",
    ])
    return "\n".join(lines)


def write_report(state: RuntimeState, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    report_path = output_dir / f"sentinel-report-{stamp}.md"
    report_path.write_text(render_report(state), encoding="utf-8")
    state.final_report_path = str(report_path)
    report_path.with_suffix(".json").write_text(state.json_ledger(), encoding="utf-8")
    return report_path
