"""
Campus occupancy dataset generator (synthetic but structured and repeatable).

Produces:
  - dataset.csv        raw occupancy records  (one row per room per hour)
  - rooms.json         buildings / rooms / capacities / map coordinates
  - academic_calendar.json   dates + semester / event / holiday / weather

Run:  py -3.11 ml/generate_dataset.py
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ml"

random.seed(42)

HOURS = list(range(8, 21))  # 08:00 - 20:00 -> 13 slots

# --------------------------------------------------------------------------
# Campus physical layout
# --------------------------------------------------------------------------
BUILDINGS = [
    {
        "code": "A", "name": "Academic Block 1", "x": 16, "y": 22,
        "rooms": [
            ("A-101", "classroom", 60), ("A-102", "classroom", 60),
            ("A-103", "classroom", 45), ("A-104", "classroom", 45),
            ("A-105", "classroom", 60), ("A-Lab1", "lab", 30), ("A-Lab2", "lab", 30),
        ],
    },
    {
        "code": "B", "name": "Central Library", "x": 62, "y": 16,
        "rooms": [
            ("B-Ref", "library", 500), ("B-Reading", "library", 300),
            ("B-Digital", "library", 120), ("B-Silent", "library", 80),
        ],
    },
    {
        "code": "C", "name": "Cafeteria & Dining", "x": 34, "y": 56,
        "rooms": [
            ("C-FoodCourt", "cafeteria", 350), ("C-Canteen", "cafeteria", 250),
            ("C-Lounge", "cafeteria", 100), ("C-PR", "meeting", 50),
        ],
    },
    {
        "code": "D", "name": "Engineering Block", "x": 70, "y": 56,
        "rooms": [
            ("D-201", "classroom", 70), ("D-202", "classroom", 70),
            ("D-203", "classroom", 70), ("D-Lab301", "lab", 35),
            ("D-Lab302", "lab", 35), ("D-Lab303", "lab", 35),
            ("D-Seminar", "meeting", 120),
        ],
    },
    {
        "code": "E", "name": "Admin & Sports Complex", "x": 42, "y": 86,
        "rooms": [
            ("E-Admin", "admin", 40), ("E-Seminar", "meeting", 90),
            ("E-Gym", "gym", 80), ("E-Auditorium", "auditorium", 300),
        ],
    },
]

# --------------------------------------------------------------------------
# Academic calendar
# --------------------------------------------------------------------------
START = date(2026, 3, 1)
END = date(2026, 9, 21)  # historic data goes up to "today" (2026-09-22)

HOLIDAYS = {date(2026, 8, 15), date(2026, 8, 16), date(2026, 5, 22)}

# date -> event name
EVENTS = {
    date(2026, 4, 16): "TechFest Day 1",
    date(2026, 4, 17): "TechFest Day 2",
    date(2026, 5, 2): "Cultural Fest",
    date(2026, 8, 1): "Open Day",
    date(2026, 8, 29): "Hackathon",
    date(2026, 9, 5): "Foundation Day",
}

def in_semester(d: date) -> int:
    if HOLIDAYS and any(_ is None for _ in ()):  # no-op guard
        pass
    if d >= date(2026, 3, 1) and d <= date(2026, 5, 21):
        return 1
    if d >= date(2026, 5, 23) and d <= date(2026, 8, 9):
        return 0  # summer break
    if d >= date(2026, 8, 10):
        return 1
    return 1

def weather_for(d: date) -> tuple[str, float]:
    m = d.month
    if d >= date(2026, 6, 1) and d <= date(2026, 9, 15):
        roll = random.random()
        if roll < 0.25:
            return "Rainy", random.uniform(26, 32)
        if roll < 0.35:
            return "Stormy", random.uniform(25, 30)
        if roll < 0.7:
            return "Hot", random.uniform(33, 39)
        return "Normal", random.uniform(29, 33)
    if m in (3, 4, 5):
        roll = random.random()
        if roll < 0.12:
            return "Rainy", random.uniform(24, 30)
        if roll < 0.55:
            return "Hot", random.uniform(31, 37)
        return "Normal", random.uniform(27, 33)
    return "Normal", random.uniform(26, 31)

WEATHER_IMPACT = {"Normal": 1.0, "Hot": 0.92, "Cold": 0.96, "Rainy": 0.78, "Stormy": 0.62}

# --------------------------------------------------------------------------
# Occupancy behaviour model (room type -> hourly profile as % of capacity)
# --------------------------------------------------------------------------
PROFILES = {
    "classroom": {
        "weekday": [0.10, 0.75, 0.92, 0.98, 0.90, 0.85, 0.50, 0.55, 0.88, 0.95, 0.92, 0.55, 0.10],
        "weekend": [0.02, 0.05, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.05, 0.02, 0.01],
    },
    "lab": {
        "weekday": [0.05, 0.60, 0.90, 0.95, 0.60, 0.50, 0.30, 0.50, 0.85, 0.90, 0.60, 0.40, 0.08],
        "weekend": [0.02, 0.04, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.06, 0.05, 0.03, 0.01],
    },
    "library": {
        "weekday": [0.10, 0.25, 0.50, 0.65, 0.70, 0.72, 0.60, 0.55, 0.70, 0.75, 0.65, 0.50, 0.35],
        "weekend": [0.06, 0.15, 0.30, 0.45, 0.50, 0.52, 0.46, 0.40, 0.50, 0.55, 0.50, 0.40, 0.30],
    },
    "cafeteria": {
        "weekday": [0.65, 0.45, 0.35, 0.25, 0.15, 0.30, 0.80, 0.92, 0.55, 0.30, 0.35, 0.72, 0.40],
        "weekend": [0.30, 0.25, 0.22, 0.30, 0.35, 0.40, 0.55, 0.65, 0.40, 0.30, 0.35, 0.55, 0.32],
    },
    "meeting": {
        "weekday": [0.05, 0.30, 0.40, 0.50, 0.40, 0.35, 0.30, 0.20, 0.45, 0.50, 0.30, 0.15, 0.05],
        "weekend": [0.00, 0.05, 0.10, 0.12, 0.15, 0.15, 0.10, 0.05, 0.10, 0.15, 0.10, 0.05, 0.01],
    },
    "gym": {
        "weekday": [0.70, 0.35, 0.20, 0.15, 0.15, 0.20, 0.30, 0.45, 0.20, 0.25, 0.30, 0.55, 0.70],
        "weekend": [0.80, 0.60, 0.30, 0.30, 0.35, 0.40, 0.50, 0.50, 0.45, 0.40, 0.50, 0.60, 0.70],
    },
    "auditorium": {
        "weekday": [0.00, 0.00, 0.05, 0.10, 0.10, 0.15, 0.05, 0.05, 0.20, 0.30, 0.20, 0.05, 0.00],
        "weekend": [0.00, 0.00, 0.02, 0.02, 0.03, 0.03, 0.02, 0.02, 0.03, 0.03, 0.02, 0.00, 0.00],
    },
    "admin": {
        "weekday": [0.10, 0.30, 0.50, 0.60, 0.60, 0.55, 0.40, 0.30, 0.50, 0.55, 0.50, 0.30, 0.05],
        "weekend": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    },
}

SEM_FACTOR = {
    "classroom": (1.0, 0.35), "lab": (1.0, 0.30), "library": (1.0, 0.75),
    "cafeteria": (1.0, 0.70), "meeting": (1.0, 0.40), "gym": (1.0, 0.70),
    "auditorium": (1.0, 0.20), "admin": (1.0, 0.60),
}

EVENT_PROFILE = {  # used on event days for shared/cert venues
    "auditorium": [0.00, 0.00, 0.00, 0.00, 0.90, 0.95, 0.40, 0.25, 0.85, 0.90, 0.55, 0.15, 0.00],
    "meeting": [0.00, 0.05, 0.10, 0.15, 0.85, 0.90, 0.50, 0.30, 0.80, 0.85, 0.40, 0.10, 0.00],
    "cafeteria": [0.40, 0.35, 0.30, 0.30, 0.60, 0.80, 0.90, 0.95, 0.60, 0.45, 0.50, 0.85, 0.45],
}

DAY_WEIGHT = {0: 1.00, 1: 0.97, 2: 1.05, 3: 1.02, 4: 0.95, 5: 1.00, 6: 0.98}

# --------------------------------------------------------------------------
def main() -> None:
    ML_DIR.mkdir(parents=True, exist_ok=True)

    # numeric encodings used by BOTH generator and the backend predictor,
    # so training features and serving features stay in the same space.
    building_codes = sorted(b["code"] for b in BUILDINGS)
    all_rooms = [r[0] for b in BUILDINGS for r in b["rooms"]]
    room_names_sorted = sorted(all_rooms)
    building_num = {c: i for i, c in enumerate(building_codes)}
    room_num = {r: i for i, r in enumerate(room_names_sorted)}

    rooms_meta = []
    for b in BUILDINGS:
        for room, rtype, cap in b["rooms"]:
            rooms_meta.append({
                "building": b["code"], "building_name": b["name"],
                "room": room, "type": rtype, "capacity": cap,
                "x": b["x"], "y": b["y"],
            })
    with open(ML_DIR / "rooms.json", "w", encoding="utf-8") as f:
        json.dump({"buildings": BUILDINGS, "rooms": rooms_meta,
                   "building_num": building_num, "room_num": room_num}, f, indent=2)

    rows, calendar = [], []
    d = START
    while d <= END:
        is_holiday = d in HOLIDAYS
        event_name = EVENTS.get(d, "")
        sem = in_semester(d)
        weather, temp = weather_for(d)
        weather_code = {"Normal": 0, "Hot": 1, "Cold": 2, "Rainy": 3, "Stormy": 4}[weather]
        impact = WEATHER_IMPACT[weather]
        dow = d.weekday()
        weekend = 1 if dow >= 5 else 0
        day_w = DAY_WEIGHT[dow]

        for b in BUILDINGS:
            for room, rtype, cap in b["rooms"]:
                wk = "weekend" if weekend else "weekday"
                profile = PROFILES[rtype][wk]
                sem_on, sem_off = SEM_FACTOR[rtype]
                sem_factor = sem_on if sem else sem_off
                for idx, hour in enumerate(HOURS):
                    base = cap * profile[idx] * day_w * impact * sem_factor
                    if event_name and rtype in EVENT_PROFILE:
                        base = cap * EVENT_PROFILE[rtype][idx] * impact
                    noise = random.gauss(0, 0.06 * cap)
                    if is_holiday:
                        occ = random.uniform(0, 0.04 * cap)
                    else:
                        occ = max(0.0, min(cap, base + noise))
                    occ = int(round(occ))
                    rows.append({
                        "date": d.isoformat(),
                        "hour": hour,
                        "building": b["code"],
                        "room": room,
                        "type": rtype,
                        "occupancy": occ,
                        "capacity": cap,
                        "semester": sem,
                        "event": 1 if event_name else 0,
                        "holiday": 1 if is_holiday else 0,
                        "weather": weather,
                        "temperature": round(temp, 1),
                        "building_num": building_num[b["code"]],
                        "room_num": room_num[room],
                        "is_weekend": weekend,
                    })
        calendar.append({
            "date": d.isoformat(), "semester": sem, "event": event_name,
            "weather": weather, "temperature": round(temp, 1),
        })
        d += timedelta(days=1)

    with open(ML_DIR / "dataset.csv", "w", encoding="utf-8", newline="") as f:
        import csv
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(ML_DIR / "academic_calendar.json", "w", encoding="utf-8") as f:
        json.dump(calendar, f, indent=2)

    print(f"Generated {len(rows):,} occupancy records  "
          f"({START} -> {END})  rooms={len(rooms_meta)}")

if __name__ == "__main__":
    main()