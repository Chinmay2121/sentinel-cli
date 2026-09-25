import json
from pathlib import Path

from scripts.prepare_smartbugs_cases import STARTER_CASES, prepare


def test_prepare_creates_isolated_foundry_cases_and_manifest(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    for case in STARTER_CASES:
        path = source_root / case.source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("pragma solidity ^0.4.24; contract Case {}", encoding="utf-8")
    output = tmp_path / "prepared"
    manifest = tmp_path / "manifest.json"

    written = prepare(source_root, output, manifest)

    assert written == manifest
    document = json.loads(manifest.read_text())
    assert len(document["cases"]) == len(STARTER_CASES)
    for case in STARTER_CASES:
        assert (output / case.identifier / "foundry.toml").is_file()
        assert (output / case.identifier / "src" / "Case.sol").is_file()
    assert (manifest.parent / document["cases"][0]["project_path"]).resolve() == (output / STARTER_CASES[0].identifier).resolve()
