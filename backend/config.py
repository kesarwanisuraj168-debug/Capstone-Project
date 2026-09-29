"""Central configuration for the Campus Occupancy system."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ml"
MODELS_DIR = ML_DIR / "models"
FRONTEND_DIR = ROOT / "frontend"
DATASET_CSV = ML_DIR / "dataset.csv"
ROOMS_JSON = ML_DIR / "rooms.json"
CALENDAR_JSON = ML_DIR / "academic_calendar.json"

# SQLite by default; point CAMPUS_DATABASE_URL at MySQL to switch, e.g.
#   mysql+pymysql://student:pass@localhost/campus
DATABASE_URL = os.getenv("CAMPUS_DATABASE_URL", f"sqlite:///{ROOT / 'campus.db'}")

SECRET_KEY = os.getenv("CAMPUS_SECRET", "campus-demo-secret-change-me-please-2026")
TOKEN_TTL_HOURS = int(os.getenv("CAMPUS_TOKEN_TTL_HOURS", "24"))
ALGORITHM = "HS256"

HOURS = list(range(8, 21))  # operating day 08:00-20:00