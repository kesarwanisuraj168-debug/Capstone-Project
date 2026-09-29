import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_predict_building():
    payload = {"building": "A", "date": "2026-09-15", "hour": 12, "model": "xgb"}
    resp = client.post("/api/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["building"] == "A"
    assert data["predicted_occupancy"] > 0
    assert "prediction_interval" in data or "rooms" in data

def test_predict_day_curve():
    resp = client.get("/api/predict/day?building=A&date=2026-09-15")
    assert resp.status_code == 200
    data = resp.json()
    assert "curve" in data
    assert len(data["curve"]) == 13

def test_model_compare():
    resp = client.get("/api/model/compare")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert len(data["models"]) >= 3
    # Check that R2 is provided for all
    for m in data["models"]:
        assert "R2" in m
        assert "MAE" in m
