"""Run Sentinel Scout against selected SmartBugs Curated cases.

Each dataset source file is copied into a temporary Foundry-shaped project. This
is detection evaluation only: SmartBugs does not supply the tests and patch
oracles required for Sentinel's Red Team → Blue Team verification workflow.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sentinel.service import run_scan  # noqa: E402


def selected_cases(manifest: Path, category: str | None, limit: int | None) -> list[dict[str, object]]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    cases = data["cases"]
    if category:
        wanted = category.upper()
        cases = [case for case in cases if wanted in case["expected_categories"]]
    return cases[:limit] if limit else cases


def write_ground_truth(case_output: Path, case: dict[str, object], state) -> tuple[bool, Path]:
    """Persist dataset labels beside, never as, scanner findings."""
    expected_lines = list(case["expected_vulnerable_lines"])
    scanner_lines = sorted({finding.line for finding in state.findings if finding.line is not None})
    matched = bool(set(expected_lines) & set(scanner_lines))
    payload = {
        "dataset_ground_truth": {
            "expected_vulnerability_types": case["expected_categories"],
            "expected_vulnerable_lines": expected_lines,
            "source_file": case["source_file"],
        },
        "scanner_result": {
            "outcome": state.final_verification_state,
            "reported_lines": scanner_lines,
            "matched_expected_line": matched,
            "finding_count": len(state.findings),
        },
        "remediation": "No .fix.sol is generated for SmartBugs cases unless a reviewed PoC and patch template exists.",
    }
    path = case_output / "dataset-ground-truth.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report = Path(state.final_report_path)
    report.write_text(report.read_text(encoding="utf-8") + "\n".join([
        "## SmartBugs Dataset Ground Truth",
        f"- **Expected vulnerability type:** {', '.join(case['expected_categories'])}.",
        f"- **Dataset-labelled vulnerable line(s):** {', '.join(map(str, expected_lines)) or 'not annotated'}.",
        f"- **Scanner-reported line(s):** {', '.join(map(str, scanner_lines)) or 'none'}.",
        f"- **Expected line matched:** {'yes' if matched else 'no'}.",
        "- **Patch status:** no `.fix.sol` is generated unless the case has a reviewed exploit and patch template.",
        "",
    ]), encoding="utf-8")
    return matched, path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Scout-only Sentinel scans for SmartBugs Curated cases.")
    parser.add_argument("--manifest", type=Path, default=Path("datasets/manifests/smartbugs-curated.json"))
    parser.add_argument("--dataset", type=Path, default=Path("datasets/smartbugs-curated"))
    parser.add_argument("--output", type=Path, default=Path("reports/smartbugs"))
    parser.add_argument("--category", help="One expected SmartBugs category, e.g. REENTRANCY")
    parser.add_argument("--limit", type=int, default=5, help="Number of cases to run; use 0 for all cases")
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be zero or a positive number")
    cases = selected_cases(args.manifest, args.category, None if args.limit == 0 else args.limit)
    if not cases:
        parser.error("No matching SmartBugs cases were found")
    args.output.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    for number, case in enumerate(cases, start=1):
        source = args.dataset / str(case["source_file"])
        if not source.is_file():
            results.append({"id": case["id"], "outcome": "missing_source", "source_file": str(source)})
            continue
        with tempfile.TemporaryDirectory(prefix="sentinel-smartbugs-") as temp:
            project = Path(temp) / "project"
            (project / "src").mkdir(parents=True)
            shutil.copy2(source, project / "src" / source.name)
            (project / "foundry.toml").write_text('[profile.default]\nsrc = "src"\ntest = "test"\n', encoding="utf-8")
            case_output = args.output / str(case["id"])
            state = run_scan(project, output=case_output, scout_only=True)
        matched, ground_truth = write_ground_truth(case_output, case, state)
        results.append({
            "id": case["id"],
            "expected_categories": case["expected_categories"],
            "expected_vulnerable_lines": case["expected_vulnerable_lines"],
            "outcome": state.final_verification_state,
            "finding_count": len(state.findings),
            "matched_expected_line": matched,
            "report": state.final_report_path,
            "ground_truth": str(ground_truth),
        })
        print(f"[{number}/{len(cases)}] {case['id']}: {state.final_verification_state} ({len(state.findings)} finding(s))")
    (args.output / "smartbugs-scan-summary.json").write_text(json.dumps({
        "scan_mode": "scout-only",
        "case_count": len(results),
        "results": results,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Saved benchmark summary to {args.output / 'smartbugs-scan-summary.json'}")


if __name__ == "__main__":
    main()
