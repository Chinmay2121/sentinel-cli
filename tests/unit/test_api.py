from pathlib import Path

from fastapi.testclient import TestClient

from sentinel.api import app
from sentinel.schemas.state import RuntimeState
from sentinel.schemas.vulnerability import VulnerabilityFinding


def test_health_and_dashboard_are_available() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok", "scope": "local-only"}
    assert "Evidence before conclusions" in client.get("/").text
    assert "Scan a project" in client.get("/").text


def test_environment_reports_tools_and_examples(monkeypatch) -> None:
    monkeypatch.setattr("sentinel.api.resolve_tool", lambda name: f"/tools/{name}" if name == "forge" else None)

    response = TestClient(app).get("/environment")

    assert response.status_code == 200
    assert response.json()["tools"]["forge"] == "/tools/forge"
    assert response.json()["tools"]["myth"] is None
    assert "vulnerable_reentrancy" in response.json()["examples"]


def test_monitor_plugin_configuration_never_connects() -> None:
    response = TestClient(app).post("/plugins/onchain-monitor", json={"target_chain": "ethereum", "rpc_endpoint": "http://localhost:8545", "contract_addresses": []})
    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_scan_request_validates_and_returns_workflow_result(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "foundry.toml").write_text("[profile.default]\n")
    captured = {}

    def fake_scan(path, **kwargs):
        captured.update(path=path, **kwargs)
        return RuntimeState(project_path=str(path), final_verification_state="no_candidates", final_report_path="reports/test.md")

    monkeypatch.setattr("sentinel.api.run_scan", fake_scan)
    response = TestClient(app).post("/scans", json={"project_path": str(project), "scout_only": True})
    assert response.status_code == 200
    assert response.json()["final_state"] == "no_candidates"
    assert captured["scout_only"] is True


def test_scan_request_rejects_non_foundry_project(tmp_path: Path) -> None:
    response = TestClient(app).post("/scans", json={"project_path": str(tmp_path)})
    assert response.status_code == 422
    assert "foundry.toml" in response.json()["detail"]


def test_report_path_endpoint_rejects_traversal() -> None:
    response = TestClient(app).get("/scans/../secret.json")
    assert response.status_code == 404


def test_report_artifact_can_be_opened_but_traversal_is_rejected(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "reports"
    output.mkdir()
    (output / "audit.md").write_text("# Audit", encoding="utf-8")
    monkeypatch.setattr("sentinel.api.settings.output_dir", output)

    response = TestClient(app).get("/reports/audit.md")

    assert response.status_code == 200
    assert response.text == "# Audit"
    assert TestClient(app).get("/reports/../secret.txt").status_code == 404


def test_scan_artifacts_lists_all_files_with_the_same_report_prefix(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "reports"
    output.mkdir()
    state = RuntimeState(project_path="/project")
    (output / "scan.json").write_text(state.model_dump_json(), encoding="utf-8")
    (output / "scan.md").write_text("# Report", encoding="utf-8")
    (output / "scan__summary.json").write_text("{}", encoding="utf-8")
    details = output / "scan__findings"
    details.mkdir()
    (details / "finding.md").write_text("# Finding", encoding="utf-8")
    monkeypatch.setattr("sentinel.api.settings.output_dir", output)

    response = TestClient(app).get("/scans/scan.json/artifacts")

    assert response.status_code == 200
    assert response.json() == [
        "scan.json", "scan.md", "scan__findings/finding.md", "scan__summary.json",
    ]


def test_live_run_exposes_a_status_endpoint(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "foundry.toml").write_text("[profile.default]\n")
    monkeypatch.setattr(
        "sentinel.api.run_scan",
        lambda *args, **kwargs: RuntimeState(project_path=str(project), final_verification_state="no_candidates"),
    )

    response = TestClient(app).post("/runs", json={"project_path": str(project)})

    assert response.status_code == 200
    assert TestClient(app).get(f"/runs/{response.json()['run_id']}").status_code == 200


def test_compare_endpoint_reports_introduced_findings(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "reports"
    output.mkdir()
    base = RuntimeState(project_path="/project")
    current = RuntimeState(project_path="/project", findings=[VulnerabilityFinding(
        id="new", source="test", detector="reentrancy", file="src/Vault.sol", line=12, description="new candidate",
    )])
    (output / "base.json").write_text(base.model_dump_json(), encoding="utf-8")
    (output / "current.json").write_text(current.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr("sentinel.api.settings.output_dir", output)

    response = TestClient(app).get("/scans/compare?base=base.json&current=current.json")

    assert response.status_code == 200
    assert response.json()["introduced"][0]["id"] == "new"


def test_buffered_live_events_are_sent_without_waiting(monkeypatch) -> None:
    from sentinel.api import RUNS
    from sentinel.telemetry import RunTelemetry

    telemetry = RunTelemetry()
    telemetry.emit("phase", "started", "scout")
    telemetry.finish("completed", "Scan complete")
    monkeypatch.setitem(RUNS, telemetry.run_id, telemetry)

    def unexpected_wait(*args, **kwargs):
        raise AssertionError("Buffered events should be delivered immediately")

    monkeypatch.setattr(telemetry.condition, "wait", unexpected_wait)
    response = TestClient(app).get(f"/runs/{telemetry.run_id}/events")
    assert response.status_code == 200
    assert '"summary": "scout"' in response.text
    assert '"summary": "Scan complete"' in response.text


def test_downloaded_ledger_retains_verbose_evidence(monkeypatch, tmp_path: Path) -> None:
    from sentinel.schemas.execution import ExecutionResult

    state = RuntimeState(
        project_path="/project",
        findings=[VulnerabilityFinding(
            id="candidate", source="slither", detector="reentrancy", file="src/Vault.sol",
            description="External call before state update", evidence=["full supporting evidence"],
            raw_output='{"detector": "reentrancy", "details": "original scanner output"}',
        )],
        original_source={"src/Vault.sol": "original source"},
        patched_source={"src/Vault.sol": "patched source"},
        exploit_result=ExecutionResult(command=["forge", "test"], cwd="/project", stdout="full execution trace"),
    )
    (tmp_path / "scan.json").write_text(state.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr("sentinel.api.settings.output_dir", tmp_path)
    response = TestClient(app).get("/reports/scan.json")
    assert response.status_code == 200
    assert response.json() == state.model_dump(mode="json")
