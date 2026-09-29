"""
Capacity optimization service.

Solves a room-assignment problem for a set of class/event requests at a given
time slot. It uses the occupancy FORECAST to estimate each room's free seats
(usable capacity = capacity - predicted occupants) and finds an assignment that
minimises an objective combining:

    empty seats  +  overcrowding  +  room-switching cost
    + movement distance  +  equipment mismatch

The [MILP] is built with PuLP and solved with CBC. A per-request dummy room
guarantees feasibility; dummy assignments are reported as "no feasible room".
"""
from __future__ import annotations

import json
import math
import time
from datetime import date, timedelta

import pulp
from sqlalchemy.orm import Session

from ..models import Recommendation, Room, Timetable
from .forecasting import ROOMS as ROOM_META
from . import forecasting

# equipment -> room types that provide it
EQUIPMENT_GROUND_TRUTH = {
    "computers": {"lab", "library"},
    "workstations": {"lab", "library"},
    "projector": {"classroom", "meeting", "auditorium"},
    "sound_system": {"auditorium", "meeting"},
    "whiteboard": {"classroom", "lab", "meeting", "auditorium", "admin"},
    "lab_equipment": {"lab"},
}

W_EMPTY = 1.0
W_SWITCH = 0.35
W_DIST = 0.25
W_EQUIP = 5.0
W_PREF = 0.5
INFEASIBLE_PENALTY = 1e6


def building_xy(room_code: str) -> tuple[int, int]:
    meta = ROOM_META.get(room_code, {})
    building = meta.get("building")
    for b in forecasting.ROOMS_META["buildings"]:
        if b["code"] == building:
            return b["x"], b["y"]
    return meta.get("x", 0), meta.get("y", 0)


def equipment_ok(room_type: str, equipment: list[str]) -> bool:
    for eq in equipment:
        if eq not in EQUIPMENT_GROUND_TRUTH:
            continue
        if room_type not in EQUIPMENT_GROUND_TRUTH[eq]:
            return False
    return True


def candidate_rooms(db: Session) -> list[dict]:
    rows = (
        db.query(Room).join(Room.building).order_by(Room.code).all()
    )
    out = []
    for room in rows:
        out.append({
            "room_id": room.id,
            "code": room.code,
            "type": room.room_type,
            "capacity": room.capacity,
            "building": room.building.code,
            "building_name": room.building.name,
            "predicted": 0,
        })
    return out


def next_24_hours(db: Session, start_date: str, start_hour: int) -> list[dict]:
    """Return the rolling 24-hour campus forecast, including closed hours."""
    start = date.fromisoformat(start_date)
    analysis = []
    for offset in range(24):
        point = start + timedelta(days=(start_hour + offset) // 24)
        hour = (start_hour + offset) % 24
        date_s = point.isoformat()
        if 8 <= hour <= 20:
            forecast = forecasting.campus_forecast(db, date_s, hour)
            analysis.append({
                "date": date_s, "hour": hour, "status": "operating",
                "predicted_occupancy": forecast["total_predicted"],
                "capacity": forecast["total_capacity"],
                "utilization": forecast["utilization"],
            })
        else:
            analysis.append({
                "date": date_s, "hour": hour, "status": "closed",
                "predicted_occupancy": 0, "capacity": 0, "utilization": 0,
            })
    return analysis


def recommend(db: Session, date: str, hour: int, requests: list[dict],
              user_id: int | None = None, save: bool = True) -> dict:
    """Solve the assignment MILP and return per-request recommendations."""
    t0 = time.time()
    hourly_analysis = next_24_hours(db, date, hour)
    rooms = candidate_rooms(db)
    if not rooms:
        return {"status": "error", "message": "No rooms defined in the database."}
    if not requests:
        return {"status": "error", "message": "At least one request is required."}
    if hour < 8 or hour > 20:
        return {
            "status": "closed",
            "summary": {
                "date": date, "hour": hour,
                "total_requests": len(requests), "accommodated": 0,
                "moved": 0, "kept": 0, "new": 0, "unmet": len(requests),
                "solver": "not run (campus closed)",
                "solve_time_s": round(time.time() - t0, 3), "objective": 0,
            },
            "results": [{
                "course": req.get("course", "Request"),
                "students": int(req["students"]),
                "status": "campus closed",
                "recommended_room": None,
                "recommended_building": None,
                "reason": "No classes are scheduled from 21:00 through 07:00.",
            } for req in requests],
            "hourly_analysis": hourly_analysis,
        }

    # Check existing timetable bookings for this weekday and hour
    try:
        dow = date.fromisoformat(date).weekday()
        booked_rooms = {
            t.room_id: t.course
            for t in db.query(Timetable).filter(Timetable.day_of_week == dow, Timetable.hour == hour).all()
        }
    except Exception:
        booked_rooms = {}

    # ---- usable capacity per candidate room using the forecast ----
    for r in rooms:
        meta = ROOM_META.get(r["code"])
        r["predicted"] = (
            forecasting.predict_room(db, meta, r["room_id"], date, hour)
            if meta else 0
        )
        r["usable"] = max(0, r["capacity"] - r["predicted"])
        r["booked_course"] = booked_rooms.get(r["room_id"])

    room_by_code = {r["code"]: r for r in rooms}

    # ---- build the model ----
    prob = pulp.LpProblem("campus_capacity", pulp.LpMinimize)
    x: dict[tuple[int, str], pulp.LpVariable] = {}
    dummy_x: dict[int, pulp.LpVariable] = {}
    cost_map: dict[tuple[int, str], float] = {}
    feasible_map: dict[tuple[int, str], bool] = {}
    request_labels: dict[int, str] = {}

    for i, req in enumerate(requests):
        students = int(req["students"])
        equip = req.get("equipment") or []
        preferred = req.get("preferred_building")
        current = req.get("current_room")
        request_labels[i] = req.get("course", f"Request {i + 1}")
        dummy_x[i] = pulp.LpVariable(f"dummy_{i}", cat="Binary")

        cbx, cby = building_xy(current) if current else (35, 50)
        for rc, r in room_by_code.items():
            tt_conflict = bool(r.get("booked_course") and r.get("booked_course") != req.get("course"))
            feasible = (students <= r["usable"] and equipment_ok(r["type"], equip) and not tt_conflict)
            feasible_map[(i, rc)] = feasible

            empty_ratio = max(0.0, (r["capacity"] - students) / r["capacity"]) if r["capacity"] else 0.0
            dx = building_xy(rc)[0] - cbx
            dy = building_xy(rc)[1] - cby
            dnorm = min(math.hypot(dx, dy) / 100.0, 1.0)
            switch = 0.0 if (current and current == rc) else 1.0
            equip_miss = 0.0 if equipment_ok(r["type"], equip) else W_EQUIP
            pref_miss = W_PREF if (preferred and r["building"] != preferred) else 0.0

            base = (W_EMPTY * empty_ratio + W_SWITCH * switch
                    + W_DIST * dnorm + equip_miss + pref_miss)
            cost_map[(i, rc)] = base if feasible else INFEASIBLE_PENALTY
            var = pulp.LpVariable(f"x_{i}_{rc}", cat="Binary", upBound=1 if feasible else 0)
            x[(i, rc)] = var

    # each request is assigned to either one feasible room or its dummy variable
    for i in range(len(requests)):
        prob += pulp.lpSum(x[(i, rc)] for rc in room_by_code) + dummy_x[i] == 1, f"assign_{i}"

    # each real room hosts at most one request
    for rc in room_by_code:
        prob += pulp.lpSum(x[(i, rc)] for i in range(len(requests))) <= 1, f"cap_{rc}"

    prob += (
        pulp.lpSum(cost_map[(i, rc)] * x[(i, rc)] for i in range(len(requests)) for rc in room_by_code)
        + pulp.lpSum(INFEASIBLE_PENALTY * dummy_x[i] for i in range(len(requests))),
        "objective",
    )

    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=30))

    # ---- post-process ----
    results = []
    for i in range(len(requests)):
        chosen = [rc for rc in room_by_code
                  if x[(i, rc)].value() is not None and x[(i, rc)].value() > 0.5]
        rc = chosen[0] if chosen else None
        req = requests[i]
        students = int(req["students"])
        if rc is None or (dummy_x[i].value() is not None and dummy_x[i].value() > 0.5) or cost_map.get((i, rc), 0) >= INFEASIBLE_PENALTY:
            results.append({
                "course": request_labels[i],
                "students": students,
                "status": "no feasible room",
                "recommended_room": None,
                "recommended_building": None,
                "current_room": req.get("current_room"),
                "reason": "No room on campus has enough free capacity and "
                          "required equipment at the selected time.",
})
            continue
        r = room_by_code[rc]
        current = req.get("current_room")
        status = "new"
        if current:
            status = "moved" if current != rc else "kept"
        results.append({
            "course": request_labels[i],
            "students": students,
            "status": status,
            "recommended_room": rc,
            "recommended_building": r["building"],
            "building_name": r["building_name"],
            "capacity": r["capacity"],
            "predicted_occupancy": r["predicted"],
            "free_seats": r["usable"],
            "current_room": current,
            "empty_after": r["capacity"] - students,
            "utilization": round(students / r["capacity"] * 100, 1) if r["capacity"] else 0.0,
            "equipment_ok": equipment_ok(r["type"], req.get("equipment") or []),
            "reason": (_fits_reason(req, r)),
})

    summary = {
        "date": date, "hour": hour,
        "total_requests": len(requests),
        "accommodated": sum(1 for _ in results if _["status"] != "no feasible room"),
        "moved": sum(1 for _ in results if _["status"] == "moved"),
        "kept": sum(1 for _ in results if _["status"] == "kept"),
        "new": sum(1 for _ in results if _["status"] == "new"),
        "unmet": sum(1 for _ in results if _["status"] == "no feasible room"),
        "solver": "PuLP / CBC (MILP)",
        "solve_time_s": round(time.time() - t0, 3),
        "objective": pulp.value(prob.objective),
    }

    payload = {
        "status": "ok",
        "summary": summary,
        "results": results,
        "assumptions": {
            "usable_capacity": "capacity - predicted occupancy (forecast-driven)",
            "objective": "min(empty seats, switching, distance, equipment mismatch)",
        },
        "hourly_analysis": hourly_analysis,
    }
    if save and user_id is not None:
        db.add(Recommendation(
            user_id=user_id, date=date, hour=hour,
            payload=json.dumps(payload)))
        db.commit()
    return payload


def _fits_reason(req: dict, room: dict) -> str:
    students = int(req["students"])
    if room["usable"] >= students:
        return (f"Free seats ({room['usable']}) cover predicted class of "
                f"{students}; no overcrowding at capacity {room['capacity']}.")
    return (f"Room capacity {room['capacity']} fits {students} students "
            f"but forecast leaves only {room['usable']} free seats.")

