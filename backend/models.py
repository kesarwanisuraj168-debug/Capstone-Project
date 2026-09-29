"""ORM models for the Campus Occupancy database."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), default="")
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="user")  # admin | user
    created_at = Column(DateTime, default=datetime.utcnow)


class Building(Base):
    __tablename__ = "buildings"
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)

    rooms = relationship("Room", back_populates="building", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    room_type = Column(String(30), default="classroom")
    capacity = Column(Integer, nullable=False)
    floor = Column(Integer, default=1)

    building = relationship("Building", back_populates="rooms")


class Occupancy(Base):
    __tablename__ = "occupancy"
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    hour = Column(Integer, nullable=False, index=True)
    occupancy_count = Column(Integer, nullable=False)
    data_origin = Column(String(20), default="synthetic", nullable=False)  # synthetic | imported | measured
    students_count = Column(Integer, nullable=True)
    staff_count = Column(Integer, nullable=True)
    is_exam = Column(Integer, default=0)
    scheduled_class = Column(String(100), nullable=True)

    room = relationship("Room")


class Timetable(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True)
    course = Column(String(80), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Mon .. 6=Sun
    hour = Column(Integer, nullable=False)
    semester = Column(Integer, default=1)

    room = relationship("Room")


class CampusEvent(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    date = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)
    date = Column(String(10), nullable=False)
    hour = Column(Integer, nullable=False)
    predicted_occupancy = Column(Integer, nullable=False)
    model = Column(String(30), default="xgb")
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    date = Column(String(10), nullable=False)
    hour = Column(Integer, nullable=False)
    payload = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)