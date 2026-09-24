from pathlib import Path

import pytest

from sentinel.patching.applier import apply_replacement, apply_unified_diff
from sentinel.reporting.markdown import render_report, write_report
from sentinel.runner import ControlledRunner
from sentinel.schemas.state import RuntimeState


def test_state_ledger_is_json_serializable() -> None:
    state = RuntimeState(project_path="/tmp/project")
    assert '"project_path": "/tmp/project"' in state.json_ledger()


def test_runner_rejects_untrusted_commands(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ControlledRunner().run(["sh", "-c", "echo unsafe"], tmp_path)


def test_runner_rejects_noncompiler_environment_override(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="compiler environment"):
        ControlledRunner().run(["forge", "build"], tmp_path, env={"PATH": "/tmp"})


def test_runner_records_missing_allowlisted_tool(tmp_path: Path, monkeypatch) -> None:
    def missing(*args, **kwargs):
        raise FileNotFoundError("forge unavailable")
    monkeypatch.setattr("sentinel.runner.subprocess.run", missing)
    result = ControlledRunner().run(["forge", "build"], tmp_path)
    assert not result.success
    assert result.exit_code == -1


def test_patch_replacement_is_scoped(tmp_path: Path) -> None:
    source = tmp_path / "Contract.sol"
    source.write_text("contract C { uint256 x; }", encoding="utf-8")
    apply_replacement(tmp_path, "Contract.sol", "uint256 x", "uint256 y", {"Contract.sol"})
    assert "uint256 y" in source.read_text(encoding="utf-8")


def test_unified_patch_applies_only_matching_existing_file(tmp_path: Path) -> None:
    source = tmp_path / "Contract.sol"
    source.write_text("contract C {\n    uint256 x;\n}\n", encoding="utf-8")
    patch = "--- a/Contract.sol\n+++ b/Contract.sol\n@@ -1,3 +1,3 @@\n contract C {\n-    uint256 x;\n+    uint256 y;\n }\n"
    assert apply_unified_diff(tmp_path, patch, {"Contract.sol"}) == ["Contract.sol"]
    assert "uint256 y" in source.read_text(encoding="utf-8")


def test_unified_patch_rejects_stale_context_and_new_files(tmp_path: Path) -> None:
    source = tmp_path / "Contract.sol"
    source.write_text("contract C {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="context"):
        apply_unified_diff(tmp_path, "+++ b/Contract.sol\n@@ -1 +1 @@\n-old\n+new\n", {"Contract.sol"})
    with pytest.raises(ValueError, match="unauthorized"):
        apply_unified_diff(tmp_path, "+++ b/New.sol\n@@ -0,0 +1 @@\n+new\n", {"Contract.sol"})


def test_report_never_invents_confirmation() -> None:
    state = RuntimeState(project_path="/tmp/project", final_verification_state="candidate_only")
    report = render_report(state)
    assert "candidate_only" in report
    assert "verified" not in report.split("## Final Outcome", 1)[1]


def test_report_writes_readable_solidity_artifacts(tmp_path: Path) -> None:
    state = RuntimeState(
        project_path="/tmp/project", candidate_id="demo", exploit_source="contract Exploit {}",
        patched_source={"src/Contract.sol": "contract Contract {}"},
    )
    report_path = write_report(state, tmp_path)
    artifact_names = {Path(path).name for path in state.report_artifacts}
    assert report_path.is_file()
    assert any(name.endswith("__Contract.patch.sol") for name in artifact_names)
    assert any(name.endswith("__demo.exploit.t.sol") for name in artifact_names)
    assert "Saved patched Solidity file" in report_path.read_text(encoding="utf-8")
    assert (tmp_path / f"{report_path.stem}__summary.json").is_file()
