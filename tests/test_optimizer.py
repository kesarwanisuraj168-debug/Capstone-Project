import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_optimize_single_request():
    payload = {
        "date": "2026-09-15",
        "hour": 10,
        "requests": [
            {"course": "CS101", "students": 25, "equipment": ["computers"], "preferred_building": "A"}
        ],
        "save": False
    }
    resp = client.post("/api/optimize", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_requests"] == 1
    assert data["summary"]["accommodated"] == 1

def test_optimize_exceeding_rooms_robustness():
    # 25 requests against campus rooms (20-26 rooms)
    requests_list = [
        {"course": f"Course_{i}", "students": 20, "equipment": ["computers"]}
        for i in range(25)
    ]
    payload = {
        "date": "2026-09-15",
        "hour": 11,
        "requests": requests_list,
        "save": False
    }
    resp = client.post("/api/optimize", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_requests"] == 25
    assert data["summary"]["accommodated"] > 0
    assert data["summary"]["unmet"] > 0
