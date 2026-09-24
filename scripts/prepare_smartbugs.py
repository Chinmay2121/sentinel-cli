"""Create a readable Sentinel benchmark manifest from SmartBugs Curated sources.

SmartBugs contracts are individual annotated Solidity files, not Foundry projects.
This script records their expected category and labelled vulnerable lines so they
can be scanned in Scout-only evaluation mode after being wrapped as Foundry cases.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LINE_PATTERN = re.compile(r"@vulnerable_at_lines:\s*([^*\n]+)")
CATEGORY_PATTERN = re.compile(r"<yes>\s+<report>\s+([A-Z_]+)")


def annotated_lines(source: str) -> list[int]:
    match = LINE_PATTERN.search(source)
    if not match:
        return []
    return [int(value) for value in re.findall(r"\d+", match.group(1))]


def build_manifest(dataset_root: Path) -> list[dict[str, object]]:
    source_root = dataset_root / "dataset"
    if not source_root.is_dir():
        raise ValueError(f"SmartBugs dataset folder is missing: {source_root}")
    cases: list[dict[str, object]] = []
    for source_path in sorted(source_root.rglob("*.sol")):
        source = source_path.read_text(encoding="utf-8", errors="replace")
        categories = sorted(set(CATEGORY_PATTERN.findall(source)))
        cases.append({
            "id": source_path.relative_to(source_root).with_suffix("").as_posix().replace("/", "--"),
            "source_file": source_path.relative_to(dataset_root).as_posix(),
            "expected_categories": categories or [source_path.parent.name.upper()],
            "expected_vulnerable_lines": annotated_lines(source),
            "scan_mode": "scout-only",
            "note": "Dataset case: detection evidence only; no generic exploit or patch is claimed.",
        })
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Sentinel's SmartBugs benchmark manifest.")
    parser.add_argument("--dataset", type=Path, default=Path("datasets/smartbugs-curated"))
    parser.add_argument("--output", type=Path, default=Path("datasets/manifests/smartbugs-curated.json"))
    args = parser.parse_args()
    cases = build_manifest(args.dataset.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "dataset": "SmartBugs Curated",
        "case_count": len(cases),
        "cases": cases,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} annotated SmartBugs cases to {args.output}")


if __name__ == "__main__":
    main()
