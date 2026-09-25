"""Create isolated Foundry wrappers for a reviewed SmartBugs Curated starter set."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StarterCase:
    identifier: str
    source: str
    vulnerability_class: str


STARTER_CASES = (
    StarterCase("smartbugs-reentrancy-bonus", "reentrancy/reentrancy_bonus.sol", "reentrancy"),
    StarterCase("smartbugs-access-control-phishable", "access_control/phishable.sol", "access_control"),
    StarterCase("smartbugs-arithmetic-overflow", "arithmetic/overflow_single_tx.sol", "arithmetic"),
    StarterCase("smartbugs-unchecked-call", "unchecked_low_level_calls/0xb11b2fed6c9354f7aa2f658d3b4d7b31d8a13b77.sol", "unchecked_low_level_call"),
)


def solidity_version(source: str) -> str:
    match = re.search(r"pragma\s+solidity\s+(?:\^|>=)?\s*(\d+\.\d+\.\d+)", source)
    if not match:
        raise ValueError("A fixed Solidity pragma is required for a prepared benchmark case")
    return match.group(1)


def prepare(source_root: Path, output_root: Path, manifest: Path) -> Path:
    cases = []
    for case in STARTER_CASES:
        source_path = source_root / case.source
        if not source_path.is_file():
            raise FileNotFoundError(f"SmartBugs source not found: {source_path}")
        target = output_root / case.identifier
        source_dir = target / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, source_dir / "Case.sol")
        version = solidity_version(source_path.read_text(encoding="utf-8"))
        (target / "foundry.toml").write_text(
            f'[profile.default]\nsrc = "src"\nsolc_version = "{version}"\n', encoding="utf-8"
        )
        cases.append({
            "id": case.identifier,
            "project_path": Path(os.path.relpath(output_root / case.identifier, manifest.parent)).as_posix(),
            "group": "held_out",
            "vulnerability_class": case.vulnerability_class,
            "ground_truth": "vulnerable",
        })
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "name": "smartbugs-curated-starter-detection-set",
        "cases": cases,
    }, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("datasets/smartbugs-curated/dataset"))
    parser.add_argument("--output", type=Path, default=Path("datasets/smartbugs-prepared"))
    parser.add_argument("--manifest", type=Path, default=Path("datasets/manifests/smartbugs-curated-starter.local.json"))
    args = parser.parse_args()
    manifest = prepare(args.source, args.output, args.manifest)
    print(f"Prepared {len(STARTER_CASES)} SmartBugs cases; manifest: {manifest}")


if __name__ == "__main__":
    main()
