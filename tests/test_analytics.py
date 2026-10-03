import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_heatmap_dow_hour():
    resp = client.get("/api/analytics/heatmap/dow-hour")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["days"]) == 7
    assert len(data["hours"]) == 13
    assert len(data["matrix"]) == 7

def test_heatmap_building_time():
    resp = client.get("/api/analytics/heatmap/building-time")
    assert resp.status_code == 200
    data = resp.json()
    assert "buildings" in data
    assert "matrix" in data

def test_spatial_campus():
    resp = client.get("/api/analytics/spatial?hour=12")
    assert resp.status_code == 200
    data = resp.json()
    assert "buildings" in data
    for b in data["buildings"]:
        assert "x" in b and "y" in b
        assert "capacity" in b
