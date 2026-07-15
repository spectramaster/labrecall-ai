from fastapi.testclient import TestClient

from labrecall.app import app, get_agent


def test_health_and_memory_lifecycle() -> None:
    get_agent.cache_clear()
    client = TestClient(app)
    health = client.get("/health")
    assert health.json()["status"] == "ok"
    assert health.headers["x-request-id"]

    home = client.get("/")
    assert home.status_code == 200
    assert "Stop solving the same research failure twice" in home.text
    assert "frame-ancestors 'none'" in home.headers["content-security-policy"]
    assert client.get("/static/app.js").status_code == 200

    incident = client.post(
        "/api/incidents",
        json={
            "pipeline": "microscopy segmentation",
            "error": "Worker lost while writing checkpoint",
            "environment": "Python 3.12, distributed job",
            "attempted_actions": [],
            "constraints": ["preserve the last verified checkpoint"],
        },
    )
    assert incident.status_code == 200
    incident_id = incident.json()["incident_id"]

    outcome = client.post(
        f"/api/incidents/{incident_id}/outcome",
        json={
            "status": "worked",
            "action_taken": "Write checkpoints atomically through a temporary key.",
            "observation": "Three resumed runs completed without a partial checkpoint.",
            "side_effects": [],
        },
    )
    assert outcome.status_code == 200
    assert outcome.json()["learned"] is True

    conflicting = client.post(
        f"/api/incidents/{incident_id}/outcome",
        json={
            "status": "worked",
            "action_taken": "Write checkpoints atomically through a temporary key.",
            "observation": "Conflicting repeat evidence.",
            "side_effects": [],
        },
    )
    assert conflicting.status_code == 409
    assert conflicting.json()["request_id"] == conflicting.headers["x-request-id"]

    stats = client.get("/api/memory/stats").json()
    assert stats["incidents"] == 1
    assert stats["reusable_memories"] == 1
    assert stats["audit_events"] >= 5

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
