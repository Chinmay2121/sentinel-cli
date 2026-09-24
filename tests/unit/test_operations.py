from sentinel.benchmark import summarize_benchmark
from sentinel.monitoring import evaluate_monitors
from sentinel.remediation_guard import requires_human_review
from sentinel.schemas.analysis import AnalyzerRun
from sentinel.schemas.state import RuntimeState
from sentinel.simulation import prepare_incident_replay


def test_local_operations_record_evidence_without_network_actions() -> None:
    state = RuntimeState(project_path="/project", analyzer_runs=[AnalyzerRun(tool="slither", target=".", status="unavailable")])
    assert evaluate_monitors(state)[0].rule_id == "coverage-incomplete"
    assert prepare_incident_replay("reentrancy drill").status == "queued"
    assert requires_human_review(state)


def test_benchmark_metrics_require_explicit_counts() -> None:
    summary = summarize_benchmark(3, 1, 2)
    assert summary.precision == 0.75
    assert summary.recall == 0.6
