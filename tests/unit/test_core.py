from pathlib import Path

import pytest

from sentinel.patching.applier import apply_replacement
from sentinel.reporting.markdown import render_report
from sentinel.runner import ControlledRunner
from sentinel.schemas.state import RuntimeState


def test_state_ledger_is_json_serializable() -> None:
    state = RuntimeState(project_path="/tmp/project")
    assert '"project_path": "/tmp/project"' in state.json_ledger()


def test_runner_rejects_untrusted_commands(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ControlledRunner().run(["sh", "-c", "echo unsafe"], tmp_path)


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


def test_report_never_invents_confirmation() -> None:
    state = RuntimeState(project_path="/tmp/project", final_verification_state="candidate_only")
    report = render_report(state)
    assert "candidate_only" in report
    assert "verified" not in report.split("## Final Outcome", 1)[1]
