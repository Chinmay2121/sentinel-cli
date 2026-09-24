"""Create a compact, reproducible FORGE-Artifacts benchmark manifest.

The upstream corpus stays in ``datasets/forge-artifacts`` (ignored by Git).  This
script writes only metadata needed to select source projects and compare future
detector output against audit-derived findings.
"""

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("datasets/forge-artifacts"))
    parser.add_argument("--output", type=Path, default=Path("datasets/manifests/forge-artifacts.json"))
    parser.add_argument("--limit", type=int, default=500, help="Deterministic maximum number of projects to retain")
    args = parser.parse_args()

    results = args.dataset / "dataset" / "results"
    dataset_root = args.dataset / "dataset"
    cases: list[dict[str, object]] = []
    categories: Counter[str] = Counter()
    for report in sorted(results.glob("*.json")):
        if len(cases) >= args.limit:
            break
        try:
            document = json.loads(report.read_text(encoding="utf-8"))
            info = document.get("project_info", {})
            projects = info.get("project_path", {})
            versions = info.get("compiler_version", [])
            findings = document.get("findings", [])
        except (OSError, json.JSONDecodeError, AttributeError):
            continue
        if not isinstance(projects, dict) or not isinstance(versions, list) or not isinstance(findings, list):
            continue
        compiler_versions = [version for version in versions if isinstance(version, str)]
        if not any("0.8" in version for version in compiler_versions):
            continue
        expected = []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            category = finding.get("category", {})
            cwes = sorted({code for values in category.values() if isinstance(values, list) for code in values if isinstance(code, str)}) if isinstance(category, dict) else []
            categories.update(cwes)
            expected.append({
                "title": finding.get("title", ""),
                "severity": finding.get("severity", "unknown"),
                "location": finding.get("location", ""),
                "cwe": cwes,
            })
        for project_name, relative in projects.items():
            if len(cases) >= args.limit:
                break
            if not isinstance(project_name, str) or not isinstance(relative, str):
                continue
            # FORGE metadata is relative to its ``dataset/`` root and already
            # includes the ``contracts/`` segment.
            source_root = (dataset_root / relative).resolve()
            if source_root.is_dir() and expected:
                cases.append({
                    "id": f"forge-{report.stem}-{project_name}",
                    "source_root": source_root.relative_to(args.dataset.resolve()).as_posix(),
                    "compiler_versions": compiler_versions,
                    "expected_findings": expected,
                })
    manifest = {
        "dataset": "FORGE Artifacts",
        "source_repository": "https://github.com/shenyimings/FORGE-Artifacts",
        "selection": "projects with audit-derived findings and a declared Solidity 0.8 compiler",
        "case_count": len(cases),
        "cwe_counts": dict(sorted(categories.items())),
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} Solidity 0.8 benchmark cases to {args.output}")


if __name__ == "__main__":
    main()
