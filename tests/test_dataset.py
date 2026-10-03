import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dataset_summary():
    resp = client.get("/api/dataset/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_records" in data
    assert "origins" in data
    assert "synthetic" in data["origins"]

def test_dataset_template():
    resp = client.get("/api/dataset/template")
    assert resp.status_code == 200
    assert "room" in resp.text
    assert "occupancy" in resp.text

def test_dataset_empty_file_rejection():
    files = {"file": ("empty.csv", b"", "text/csv")}
    resp = client.post("/api/dataset/upload", files=files, data={"origin": "imported"})
    assert resp.status_code == 400

def test_dataset_valid_upload():
    csv_bytes = (
        b"date,hour,room,occupancy,capacity\n"
        b"2026-09-24,14,A-101,30,60\n"
        b"2026-09-24,15,A-101,35,60\n"
    )
    files = {"file": ("unit_test.csv", csv_bytes, "text/csv")}
    resp = client.post("/api/dataset/upload", files=files, data={"origin": "imported", "replace_duplicates": "true"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["total_rows"] == 2

def test_synthetic_generation_endpoint():
    resp = client.post("/api/dataset/generate-synthetic?start_date=2026-09-20&end_date=2026-09-22&scenario=exam&noise_level=0.05&seed_db=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["records_count"] > 0
    assert data["scenario"] == "exam"

def test_synthetic_download_endpoint():
    resp = client.get("/api/dataset/download-synthetic?start_date=2026-09-20&end_date=2026-09-21&scenario=normal")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "date,hour,room,occupancy" in resp.text

