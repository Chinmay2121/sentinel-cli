from sentinel.graph.workflow import build_workflow
from sentinel.schemas.state import RuntimeState


def test_workflow_reaches_a_terminal_recorded_state() -> None:
    result = build_workflow().invoke(RuntimeState(project_path="examples/vulnerable_reentrancy", mock_mode=True))
    assert result["final_verification_state"] in {"finding_discarded", "verified", "human_review_required"}
