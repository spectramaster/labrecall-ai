from fastapi.testclient import TestClient

from labrecall.app import app, get_agent


def test_health_and_memory_lifecycle() -> None:
    get_agent.cache_clear()
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"

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

    stats = client.get("/api/memory/stats").json()
    assert stats["incidents"] == 1
    assert stats["reusable_memories"] == 1
