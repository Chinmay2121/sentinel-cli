from pathlib import Path

from fastapi.testclient import TestClient

from sentinel.api import app
from sentinel.schemas.state import RuntimeState
from sentinel.schemas.vulnerability import VulnerabilityFinding


def test_health_and_dashboard_are_available() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok", "scope": "local-only"}
    assert "Evidence before conclusions" in client.get("/").text


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
