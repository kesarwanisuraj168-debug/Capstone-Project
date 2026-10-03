"""Occupancy & campus data routes (read & admin CRUD)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Building, Occupancy, Room
from ..schemas import BuildingCreate, BuildingUpdate, RoomCreate, RoomUpdate

router = APIRouter(prefix="/api", tags=["occupancy"])


@router.get("/buildings")
def list_buildings(db: Session = Depends(get_db)):
    out = []
    for b in db.query(Building).order_by(Building.code).all():
        rooms = db.query(Room).filter(Room.building_id == b.id).all()
        out.append({
            "id": b.id, "code": b.code, "name": b.name, "x": b.x, "y": b.y,
            "room_count": len(rooms),
            "capacity": sum(r.capacity for r in rooms),
        })
    return out


@router.post("/buildings")
def create_building(
    payload: BuildingCreate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    code = payload.code.strip().upper()
    existing = db.query(Building).filter(Building.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Building with code '{code}' already exists.")

    bldg = Building(code=code, name=payload.name.strip(), x=payload.x, y=payload.y)
    db.add(bldg)
    db.commit()
    db.refresh(bldg)
    return {"status": "success", "message": f"Building '{bldg.code}' created successfully.", "building": {"id": bldg.id, "code": bldg.code, "name": bldg.name, "x": bldg.x, "y": bldg.y}}


@router.put("/buildings/{building_id}")
def update_building(
    building_id: int,
    payload: BuildingUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    bldg = db.query(Building).filter(Building.id == building_id).first()
    if not bldg:
        raise HTTPException(status_code=404, detail="Building not found.")

    if payload.name is not None:
        bldg.name = payload.name.strip()
    if payload.x is not None:
        bldg.x = payload.x
    if payload.y is not None:
        bldg.y = payload.y

    db.commit()
    db.refresh(bldg)
    return {"status": "success", "message": f"Building '{bldg.code}' updated.", "building": {"id": bldg.id, "code": bldg.code, "name": bldg.name, "x": bldg.x, "y": bldg.y}}


@router.delete("/buildings/{building_id}")
def delete_building(
    building_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    bldg = db.query(Building).filter(Building.id == building_id).first()
    if not bldg:
        raise HTTPException(status_code=404, detail="Building not found.")

    # Delete rooms & associated occupancies
    room_ids = [r.id for r in bldg.rooms]
    if room_ids:
        db.query(Occupancy).filter(Occupancy.room_id.in_(room_ids)).delete(synchronize_session=False)

    code = bldg.code
    db.delete(bldg)
    db.commit()
    return {"status": "success", "message": f"Building '{code}' and associated rooms deleted."}


@router.get("/rooms")
def list_rooms(building: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Room).join(Building).order_by(Building.code, Room.code)
    if building:
        q = q.filter(Building.code == building)
    return [
        {
            "id": r.id,
            "code": r.code,
            "type": r.room_type,
            "capacity": r.capacity,
            "floor": r.floor or 1,
            "building": r.building.code,
            "building_id": r.building.id,
            "building_name": r.building.name,
        }
        for r in q.all()
    ]


@router.post("/rooms")
def create_room(
    payload: RoomCreate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    bldg_code = payload.building_code.strip().upper()
    bldg = db.query(Building).filter(Building.code == bldg_code).first()
    if not bldg:
        raise HTTPException(status_code=404, detail=f"Building '{bldg_code}' does not exist.")

    room_code = payload.code.strip()
    existing = db.query(Room).filter(Room.code == room_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Room with code '{room_code}' already exists.")

    new_room = Room(
        code=room_code,
        building_id=bldg.id,
        room_type=payload.room_type.strip().lower(),
        capacity=payload.capacity,
        floor=payload.floor,
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return {
        "status": "success",
        "message": f"Room '{new_room.code}' created in Building {bldg.code}.",
        "room": {
            "id": new_room.id,
            "code": new_room.code,
            "type": new_room.room_type,
            "capacity": new_room.capacity,
            "floor": new_room.floor,
            "building": bldg.code,
        },
    }


@router.put("/rooms/{room_id}")
def update_room(
    room_id: int,
    payload: RoomUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")

    if payload.room_type is not None:
        room.room_type = payload.room_type.strip().lower()
    if payload.capacity is not None:
        room.capacity = payload.capacity
    if payload.floor is not None:
        room.floor = payload.floor

    db.commit()
    db.refresh(room)
    return {
        "status": "success",
        "message": f"Room '{room.code}' updated.",
        "room": {
            "id": room.id,
            "code": room.code,
            "type": room.room_type,
            "capacity": room.capacity,
            "floor": room.floor,
        },
    }


@router.delete("/rooms/{room_id}")
def delete_room(
    room_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")

    code = room.code
    db.query(Occupancy).filter(Occupancy.room_id == room.id).delete(synchronize_session=False)
    db.delete(room)
    db.commit()
    return {"status": "success", "message": f"Room '{code}' deleted."}


@router.get("/occupancy/current")
def current_occupancy(db: Session = Depends(get_db)):
    """Latest recorded snapshot per building (most recent date+hour in data)."""
    latest = db.query(func.max(Occupancy.date)).scalar()
    if not latest:
        return {"date": None, "hour": None, "buildings": [], "total": 0}
    hour = db.query(func.max(Occupancy.hour)).filter(Occupancy.date == latest).scalar()
    rows = (
        db.query(Building.code, func.sum(Occupancy.occupancy_count))
        .join(Room, Room.building_id == Building.id)
        .join(Occupancy, Occupancy.room_id == Room.id)
        .filter(Occupancy.date == latest, Occupancy.hour == hour)
        .group_by(Building.code)
        .order_by(Building.code)
        .all()
    )
    buildings = [{"code": c, "occupancy": int(v)} for c, v in rows]
    return {"date": latest, "hour": hour, "buildings": buildings,
            "total": sum(int(v) for _, v in rows)}


@router.get("/occupancy/history")
def occupancy_history(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    latest = db.query(func.max(Occupancy.date)).scalar()
    if not latest:
        return {"series": []}
    start = (date.fromisoformat(latest) - timedelta(days=days - 1)).isoformat()
    rows = (
        db.query(Occupancy.date, func.sum(Occupancy.occupancy_count))
        .filter(Occupancy.date >= start)
        .group_by(Occupancy.date)
        .order_by(Occupancy.date)
        .all()
    )
    return {"series": [{"date": d, "total": int(v)} for d, v in rows]}


@router.get("/occupancy/date")
def occupancy_for_slot(dt: str = Query(..., alias="date"), hour: int = Query(..., ge=0, le=23),
                       db: Session = Depends(get_db)):
    rows = (
        db.query(Building.code, func.sum(Occupancy.occupancy_count))
        .join(Room, Room.building_id == Building.id)
        .join(Occupancy, Occupancy.room_id == Room.id)
        .filter(Occupancy.date == dt, Occupancy.hour == hour)
        .group_by(Building.code).order_by(Building.code).all()
    )
    return {"date": dt, "hour": hour,
            "buildings": [{"code": c, "occupancy": int(v)} for c, v in rows],
            "total": int(sum(v for _, v in rows))}


@router.get("/occupancy/detail")
def occupancy_detail(building: str, dt: str = Query(..., alias="date"),
                     db: Session = Depends(get_db)):
    rooms = (
        db.query(Room).join(Building).filter(Building.code == building)
        .order_by(Room.code).all()
    )
    if not rooms:
        return {"building": building, "rooms": []}
    rows = (
        db.query(Occupancy.room_id, Occupancy.hour, Occupancy.occupancy_count)
        .filter(Occupancy.date == dt, Occupancy.room_id.in_([r.id for r in rooms]))
        .all()
    )
    grid = {(rid, hr): val for rid, hr, val in rows}
    out = []
    for r in rooms:
        out.append({
            "room": r.code, "type": r.room_type, "capacity": r.capacity,
            "hours": [grid.get((r.id, h), None) for h in range(8, 21)],
        })
    return {"building": building, "date": dt, "hours": list(range(8, 21)), "rooms": out}

