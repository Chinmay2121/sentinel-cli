import shutil
from pathlib import Path

from sentinel.graph.workflow import build_workflow
from sentinel.schemas.state import RuntimeState


def test_workflow_reaches_a_terminal_recorded_state(tmp_path, monkeypatch) -> None:
    project = tmp_path / "project"
    shutil.copytree(Path(__file__).parents[2] / "examples/vulnerable_reentrancy", project)
    def missing(*args, **kwargs):
        raise FileNotFoundError("tools unavailable")
    monkeypatch.setattr("sentinel.runner.subprocess.run", missing)
    result = build_workflow().invoke(RuntimeState(project_path=str(project), mock_mode=True))
    assert result["final_verification_state"] == "execution_unavailable"
    assert not result["exploit_confirmed"]
