import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from labrecall.app import app, get_agent, handler


def test_health_and_memory_lifecycle() -> None:
    get_agent.cache_clear()
    client = TestClient(app)
    health = client.get("/health")
    assert health.json()["status"] == "ok"
    assert health.json()["architecture"]
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

    timeline = client.get("/api/memory/timeline?limit=5")
    assert timeline.status_code == 200
    assert timeline.json()[0]["event_type"] == "memory.promoted"
    assert timeline.json()[0]["evidence_ids"] == [incident_id]


def test_browser_sessions_are_isolated() -> None:
    get_agent.cache_clear()
    client = TestClient(app)
    headers_a = {"x-labrecall-session": "judge-a"}
    headers_b = {"x-labrecall-session": "judge-b"}

    incident = client.post(
        "/api/incidents",
        headers=headers_a,
        json={
            "pipeline": "spectral calibration",
            "error": "dark-reference drift after warm restart",
            "environment": "synthetic fixture",
        },
    )
    assert incident.status_code == 200
    assert client.get("/api/memory/stats", headers=headers_a).json()["incidents"] == 1
    assert client.get("/api/memory/stats", headers=headers_b).json()["incidents"] == 0


def test_power_tuning_payload_reaches_the_mangum_handler() -> None:
    template = json.loads(
        Path("evidence/lambda-power-tuning-input.template.json").read_text()
    )
    get_agent.cache_clear()
    context = SimpleNamespace(
        function_name="labrecall-fixture",
        function_version="$LATEST",
        invoked_function_arn="arn:aws:lambda:us-east-1:000000000000:function:labrecall-fixture",
        memory_limit_in_mb="1024",
        aws_request_id="power-tuning-test",
    )

    response = handler(template["payload"], context)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["mode"] == "fixture"
    assert body["requires_human_approval"] is True
