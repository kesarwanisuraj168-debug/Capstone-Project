"""
Database seeding: builds buildings/rooms from ml/rooms.json, loads historical
occupancy from ml/dataset.csv and creates the demo users.

Run standalone (from project root):
    py -3.11 -m backend.seed
"""
from __future__ import annotations

import csv
import json

from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from .config import DATASET_CSV, ROOMS_JSON, CALENDAR_JSON
from .database import Base, SessionLocal, engine
from .models import Building, CampusEvent, Occupancy, Room, Timetable, User
from .security import hash_password

CHUNK = 4000


def load_rooms_meta() -> dict:
    with open(ROOMS_JSON, encoding="utf-8") as f:
        return json.load(f)


def seed_structures(db: Session) -> None:
    meta = load_rooms_meta()
    if db.query(Building).count() == 0:
        for b in meta["buildings"]:
            db.add(Building(code=b["code"], name=b["name"], x=b["x"], y=b["y"]))
        db.commit()

    buildings = {b.code: b for b in db.query(Building).all()}
    known = {r.code for r in db.query(Room).all()}
    for r in meta["rooms"]:
        if r["room"] not in known:
            db.add(Room(code=r["room"], building_id=buildings[r["building"]].id,
                        room_type=r["type"], capacity=r["capacity"]))
    db.commit()


def seed_occupancy(db: Session) -> None:
    if db.query(func.count(Occupancy.id)).scalar() > 0:
        return
    rooms = {r.code: r.id for r in db.query(Room).all()}
    rows = []
    total = 0
    with open(DATASET_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for line in reader:
            room_id = rooms.get(line["room"])
            if room_id is None:
                continue
            rows.append({
                "room_id": room_id,
                "date": line["date"],
                "hour": int(line["hour"]),
                "occupancy_count": int(line["occupancy"]),
            })
            total += 1
            if len(rows) >= CHUNK:
                db.execute(insert(Occupancy), rows)
                rows.clear()
    if rows:
        db.execute(insert(Occupancy), rows)
    db.commit()
    print(f"Seeded {total:,} occupancy records")


def seed_events(db: Session) -> None:
    if db.query(func.count(CampusEvent.id)).scalar() > 0:
        return
    with open(CALENDAR_JSON, encoding="utf-8") as f:
        calendar = json.load(f)
    for row in calendar:
        if row.get("event"):
            db.add(CampusEvent(date=row["date"], name=row["event"]))
    db.commit()


def seed_timetable(db: Session) -> None:
    if db.query(func.count(Timetable.id)).scalar() > 0:
        return
    rooms = {r.code: r.id for r in db.query(Room).all()}
    # course, room, day(Monday=0), hour
    template = [
        ("CS301 - Data Structures", "A-101", 0, 9), ("CS301 - Data Structures", "A-101", 0, 10),
        ("CS305 - DBMS", "A-102", 0, 11), ("CS305 - DBMS", "A-102", 0, 12),
        ("ML Lab", "A-Lab1", 0, 14), ("ML Lab", "A-Lab1", 0, 15),
        ("CS301 - Data Structures", "A-101", 1, 9), ("ML Lab", "A-Lab1", 1, 11),
        ("EE201 - Circuits", "D-201", 1, 10), ("EE201 - Circuits", "D-201", 1, 11),
        ("Embedded Lab", "D-Lab301", 1, 14), ("Embedded Lab", "D-Lab301", 1, 15),
        ("CS305 - DBMS", "A-102", 2, 10), ("EE201 - Circuits", "D-201", 2, 9),
        ("AI & ML", "D-Seminar", 2, 14), ("AI & ML", "D-Seminar", 2, 15),
        ("CS301 - Data Structures", "A-101", 3, 11), ("Embedded Lab", "D-Lab301", 3, 9),
        ("AI & ML", "D-Seminar", 4, 9), ("CS305 - DBMS", "A-102", 4, 14),
    ]
    for course, room_code, dow, hour in template:
        rid = rooms.get(room_code)
        if rid:
            db.add(Timetable(course=course, room_id=rid, day_of_week=dow, hour=hour))
    db.commit()


def seed_users(db: Session) -> None:
    if db.query(func.count(User.id)).scalar() > 0:
        return
    db.add(User(username="admin", full_name="Campus Administrator",
                password_hash=hash_password("admin123"), role="admin"))
    db.add(User(username="user", full_name="Demo Student",
                password_hash=hash_password("user123"), role="user"))
    db.commit()
    print("Seeded users: admin/admin123, user/user123")


def seed_all() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_structures(db)
        seed_occupancy(db)
        seed_events(db)
        seed_timetable(db)
        seed_users(db)
    print("Database ready.")


if __name__ == "__main__":
    seed_all()