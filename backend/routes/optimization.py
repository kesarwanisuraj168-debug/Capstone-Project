"""Capacity optimisation routes."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import optional_user
from ..models import Recommendation, Timetable, User
from ..schemas import OptimizeRequest
from ..services import optimizer

router = APIRouter(prefix="/api", tags=["optimization"])


@router.post("/optimize")
def optimize(body: OptimizeRequest, db: Session = Depends(get_db),
             user: User | None = Depends(optional_user)):
    if len(body.requests) > 40:
        raise HTTPException(status_code=422, detail="Too many requests (max 40).")
    requests = [r.model_dump() for r in body.requests]
    return optimizer.recommend(db, body.date, body.hour, requests,
                               user_id=user.id if user else None, save=body.save)


@router.get("/recommendations")
def recommendations(limit: int = Query(30, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.query(Recommendation).order_by(Recommendation.id.desc()).limit(limit).all()
    out = []
    for r in rows:
        try:
            payload = json.loads(r.payload)
        except json.JSONDecodeError:
            payload = {}
        out.append({
            "id": r.id, "date": r.date, "hour": r.hour,
            "summary": payload.get("summary", {}),
            "results": payload.get("results", []),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return out

@router.get("/optimize/courses")
def courses(db: Session = Depends(get_db)):
    return [row[0] for row in db.query(Timetable.course).distinct()
            .order_by(Timetable.course).all()]


@router.get("/optimize/options")
def options(students: int = Query(20, gt=0),
            equipment: str = Query("", description="comma separated"),
            db: Session = Depends(get_db)):
    equip = [e.strip() for e in equipment.split(",") if e.strip()] if equipment else []
    rooms = optimizer.candidate_rooms(db)
    out = []
    for r in rooms:
        if students <= r["capacity"] and optimizer.equipment_ok(r["type"], equip):
            out.append({
                "room": r["code"], "type": r["type"], "capacity": r["capacity"],
                "building": r["building"], "building_name": r["building_name"],
            })
    return out

