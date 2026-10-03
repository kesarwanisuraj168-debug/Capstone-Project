"""
Spatiotemporal Analytics routes.

Provides real data-driven analytics:
- Day-of-week vs. Hour occupancy heatmaps
- Building vs. Time occupancy heatmaps
- Room-wise utilization comparisons
- Campus spatial coordinates and layout mapping
- Historical vs. Predicted comparison series
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import HOURS
from ..database import get_db
from ..models import Building, Occupancy, Room
from ..services import forecasting

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/heatmap/dow-hour")
def heatmap_dow_hour(
    building: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Day of Week (Monday=0 .. Sunday=6) vs Hour (8..20) matrix of average occupancy.
    Calculated directly from recorded historical occupancy.
    """
    q = (
        db.query(
            Occupancy.date,
            Occupancy.hour,
            func.sum(Occupancy.occupancy_count).label("total_occ"),
        )
        .join(Room, Occupancy.room_id == Room.id)
        .join(Building, Room.building_id == Building.id)
    )
    if building:
        q = q.filter(Building.code == building)

    rows = q.group_by(Occupancy.date, Occupancy.hour).all()

    # Aggregate by (weekday, hour)
    sums: dict[tuple[int, int], float] = {}
    counts: dict[tuple[int, int], int] = {}

    for d_str, hr, val in rows:
        try:
            wd = date.fromisoformat(d_str).weekday()
        except ValueError:
            continue
        key = (wd, hr)
        sums[key] = sums.get(key, 0.0) + float(val)
        counts[key] = counts.get(key, 0) + 1

    days_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours_labels = [f"{h:02d}:00" for h in HOURS]

    # Build z-matrix (7 days x 13 hours)
    matrix = []
    for wd in range(7):
        row = []
        for h in HOURS:
            c = counts.get((wd, h), 0)
            avg = round(sums.get((wd, h), 0.0) / c, 1) if c > 0 else 0.0
            row.append(avg)
        matrix.append(row)

    return {
        "days": days_labels,
        "hours": hours_labels,
        "matrix": matrix,
        "building": building or "Campus Total",
        "metric": "Average Occupancy",
    }


@router.get("/heatmap/building-time")
def heatmap_building_time(
    dt: Optional[str] = Query(None, alias="date"),
    building: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Building or Room vs Hour matrix for a specific date.
    - If building is specified, returns room-level utilization matrix for that building.
    - If building is None, returns building-level utilization matrix for all campus buildings.
    - If no recorded occupancy exists for this date, uses the ML forecasting model.
    """
    latest = dt or db.query(func.max(Occupancy.date)).scalar()
    if not latest:
        return {"buildings": [], "hours": [], "matrix": []}

    hours_labels = [f"{h:02d}:00" for h in HOURS]

    # Mode 1: Specific building -> room-by-room utilization heatmap
    if building:
        b = db.query(Building).filter(Building.code == building).first()
        if not b:
            return {"buildings": [], "hours": [], "matrix": []}
        rooms = db.query(Room).filter(Room.building_id == b.id).order_by(Room.code).all()
        if not rooms:
            return {"buildings": [], "hours": [], "matrix": []}

        room_codes = [r.code for r in rooms]
        room_labels = [f"{r.code} ({r.room_type})" for r in rooms]

        # Check actual recorded records
        rows = (
            db.query(Room.code, Occupancy.hour, Occupancy.occupancy_count)
            .join(Room, Occupancy.room_id == Room.id)
            .join(Building, Room.building_id == Building.id)
            .filter(Building.code == building, Occupancy.date == latest)
            .all()
        )

        if rows:
            actual_map = {(code, hr): int(occ) for code, hr, occ in rows}
            matrix = []
            for r in rooms:
                row = []
                cap = r.capacity or 1
                for h in HOURS:
                    occ = actual_map.get((r.code, h), 0)
                    util = round(occ / cap * 100, 1)
                    row.append(util)
                matrix.append(row)
            is_predicted = False
        else:
            # Fallback to ML room-level prediction
            try:
                day_fc = forecasting.predict_day(db, building, latest, with_rooms=True)
                pred_rooms = day_fc.get("rooms", [])
                matrix = []
                for pr in pred_rooms:
                    cap = pr.get("capacity") or 1
                    curve = pr.get("curve", [])
                    matrix.append([round(v / cap * 100, 1) for v in curve])
            except Exception:
                matrix = [[0.0] * len(HOURS) for _ in rooms]
            is_predicted = True

        return {
            "date": latest,
            "buildings": room_labels,
            "hours": hours_labels,
            "matrix": matrix,
            "metric": "Utilization %",
            "is_predicted": is_predicted,
            "building": building,
            "level": "room",
        }

    # Mode 2: All campus buildings
    buildings = db.query(Building).order_by(Building.code).all()
    b_capacities = {}
    for b in buildings:
        cap = sum(r.capacity for r in b.rooms)
        b_capacities[b.code] = cap

    # Fetch actual records for this date
    rows = (
        db.query(
            Building.code,
            Occupancy.hour,
            func.sum(Occupancy.occupancy_count).label("occ"),
        )
        .join(Room, Occupancy.room_id == Room.id)
        .join(Building, Room.building_id == Building.id)
        .filter(Occupancy.date == latest)
        .group_by(Building.code, Occupancy.hour)
        .all()
    )

    if rows:
        actual_map = {(code, hr): int(occ) for code, hr, occ in rows}
        matrix = []
        for b in buildings:
            row = []
            cap = b_capacities.get(b.code, 1) or 1
            for h in HOURS:
                occ = actual_map.get((b.code, h), 0)
                util = round(occ / cap * 100, 1)
                row.append(util)
            matrix.append(row)
        is_predicted = False
    else:
        # Fallback to ML campus forecast across operating hours
        matrix = [[] for _ in buildings]
        try:
            for h in HOURS:
                fc = forecasting.campus_forecast(db, latest, h)
                pred_by_bldg = {item["building"]: item["utilization"] for item in fc["buildings"]}
                for idx, b in enumerate(buildings):
                    matrix[idx].append(pred_by_bldg.get(b.code, 0.0))
        except Exception:
            matrix = [[0.0] * len(HOURS) for _ in buildings]
        is_predicted = True

    return {
        "date": latest,
        "buildings": [f"{b.code} ({b.name})" for b in buildings],
        "hours": hours_labels,
        "matrix": matrix,
        "metric": "Utilization %",
        "is_predicted": is_predicted,
        "level": "building",
    }


@router.get("/room-comparison")
def room_comparison(
    building: Optional[str] = None,
    dt: Optional[str] = Query(None, alias="date"),
    db: Session = Depends(get_db),
):
    """Room-wise capacity and utilization metrics for a selected building/date."""
    latest = dt or db.query(func.max(Occupancy.date)).scalar()
    q = db.query(Room).join(Building).order_by(Building.code, Room.code)
    if building:
        q = q.filter(Building.code == building)
    rooms = q.all()

    out = []
    for r in rooms:
        # Compute avg, peak for this date
        stats = (
            db.query(
                func.avg(Occupancy.occupancy_count),
                func.max(Occupancy.occupancy_count),
            )
            .filter(Occupancy.room_id == r.id, Occupancy.date == latest)
            .first()
        )
        avg_occ = round(float(stats[0]), 1) if stats and stats[0] is not None else 0.0
        peak_occ = int(stats[1]) if stats and stats[1] is not None else 0
        util = round(avg_occ / r.capacity * 100, 1) if r.capacity else 0.0

        out.append({
            "room": r.code,
            "building": r.building.code,
            "building_name": r.building.name,
            "type": r.room_type,
            "floor": getattr(r, "floor", 1) or 1,
            "capacity": r.capacity,
            "avg_occupancy": avg_occ,
            "peak_occupancy": peak_occ,
            "utilization": util,
            "status": "Overcapacity" if peak_occ > r.capacity else ("High" if util >= 80 else ("Medium" if util >= 50 else "Low")),
        })

    return {"date": latest, "rooms": out}


@router.get("/spatial")
def spatial_campus(
    dt: Optional[str] = Query(None, alias="date"),
    hour: int = Query(12, ge=0, le=23),
    db: Session = Depends(get_db),
):
    """
    Returns campus map coordinates and status for 2D spatial visualization.
    Integrates building (x, y) coordinates with actual and predicted utilization.
    """
    latest = dt or db.query(func.max(Occupancy.date)).scalar()
    buildings = db.query(Building).order_by(Building.code).all()

    # Actual occupancy at this hour
    actual_rows = (
        db.query(Building.code, func.sum(Occupancy.occupancy_count))
        .join(Room, Occupancy.room_id == Room.id)
        .join(Building, Room.building_id == Building.id)
        .filter(Occupancy.date == latest, Occupancy.hour == hour)
        .group_by(Building.code)
        .all()
    )
    actual_map = {c: int(v) for c, v in actual_rows}

    # Predicted occupancy at this hour
    try:
        fc = forecasting.campus_forecast(db, latest, hour)
        pred_map = {b["building"]: b for b in fc["buildings"]}
    except Exception:
        pred_map = {}

    out = []
    for b in buildings:
        rooms = b.rooms
        cap = sum(r.capacity for r in rooms)
        act = actual_map.get(b.code, 0)
        fc_info = pred_map.get(b.code, {})
        pred = fc_info.get("predicted_occupancy", act)
        util = round(act / cap * 100, 1) if cap else 0.0

        status = "Overcrowded" if act > cap else ("High" if util >= 80 else ("Medium" if util >= 50 else "Low"))

        out.append({
            "code": b.code,
            "name": b.name,
            "x": b.x,
            "y": b.y,
            "capacity": cap,
            "room_count": len(rooms),
            "actual_occupancy": act,
            "predicted_occupancy": pred,
            "utilization": util,
            "status": status,
            "rooms": [
                {
                    "code": r.code,
                    "type": r.room_type,
                    "capacity": r.capacity,
                    "floor": getattr(r, "floor", 1) or 1,
                }
                for r in rooms
            ],
        })

    return {
        "date": latest,
        "hour": hour,
        "canvas_size": {"width": 100, "height": 100},
        "buildings": out,
    }


@router.get("/historical-vs-predicted")
def historical_vs_predicted(
    building: str = Query("A"),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Side-by-side daily historical vs. predicted occupancy for validation."""
    latest = db.query(func.max(Occupancy.date)).scalar()
    if not latest:
        return {"series": []}

    end_d = date.fromisoformat(latest)
    start_d = end_d - timedelta(days=days - 1)

    # Actual daily sums for this building
    actual_rows = (
        db.query(Occupancy.date, func.sum(Occupancy.occupancy_count))
        .join(Room, Occupancy.room_id == Room.id)
        .join(Building, Room.building_id == Building.id)
        .filter(Building.code == building, Occupancy.date >= start_d.isoformat(), Occupancy.date <= latest)
        .group_by(Occupancy.date)
        .order_by(Occupancy.date)
        .all()
    )
    actual_map = {d: int(v) for d, v in actual_rows}

    # Predicted daily sums for midday slot or day total
    series = []
    curr = start_d
    while curr <= end_d:
        d_str = curr.isoformat()
        act_val = actual_map.get(d_str, 0)
        try:
            day_fc = forecasting.predict_day(db, building, d_str)
            pred_val = sum(c["predicted"] for c in day_fc["curve"])
        except Exception:
            pred_val = act_val

        series.append({
            "date": d_str,
            "weekday": curr.strftime("%a"),
            "actual_person_hours": act_val,
            "predicted_person_hours": pred_val,
            "variance": pred_val - act_val,
        })
        curr += timedelta(days=1)

    return {
        "building": building,
        "days": days,
        "start_date": start_d.isoformat(),
        "end_date": latest,
        "series": series,
    }
