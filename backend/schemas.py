"""Pydantic request/response schemas."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    full_name: str = ""
    password: str = Field(min_length=4, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    token: str
    user: UserOut


# ---------- Prediction ----------
class PredictRequest(BaseModel):
    building: str
    date: str
    hour: int = Field(ge=0, le=23)
    model: str = "xgb"


class OptimizeRequestItem(BaseModel):
    course: str
    students: int = Field(gt=0)
    equipment: list[str] = []
    preferred_building: Optional[str] = None
    current_room: Optional[str] = None


class OptimizeRequest(BaseModel):
    date: str
    hour: int = Field(ge=0, le=23)
    requests: list[OptimizeRequestItem]
    save: bool = True


class FeatureRow(BaseModel):
    building_num: int
    room_num: int
    capacity: int
    hour: int
    day_of_week: int
    month: int
    is_weekend: int
    semester: int
    event: int
    holiday: int
    weather_code: int
    temperature: float
    prev_hour_occ: float
    prev_day_occ: float


class ModelInfo(BaseModel):
    model: str
    metric: str
    value: Any


# ---------- Buildings & Rooms CRUD ----------
class BuildingCreate(BaseModel):
    code: str = Field(min_length=1, max_length=10)
    name: str = Field(min_length=1, max_length=100)
    x: int = Field(default=50, ge=0, le=100)
    y: int = Field(default=50, ge=0, le=100)


class BuildingUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    x: Optional[int] = Field(None, ge=0, le=100)
    y: Optional[int] = Field(None, ge=0, le=100)


class RoomCreate(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    building_code: str
    room_type: str = "classroom"
    capacity: int = Field(gt=0)
    floor: int = Field(default=1, ge=0, le=20)


class RoomUpdate(BaseModel):
    room_type: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0)
    floor: Optional[int] = Field(None, ge=0, le=20)