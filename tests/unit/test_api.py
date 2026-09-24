from pathlib import Path

from fastapi.testclient import TestClient

from sentinel.api import app
from sentinel.schemas.state import RuntimeState


def test_health_and_dashboard_are_available() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok", "scope": "local-only"}
    assert "Sentinel local review" in client.get("/").text


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
