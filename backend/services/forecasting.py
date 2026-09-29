"""
Spatiotemporal occupancy forecasting service.

Loads the trained model from ml/models and exposes:
  - predict_room   : single room / hour prediction
  - predict_building : whole-building prediction for one hour
  - predict_day    : 08:00-20:00 curve for a building
  - campus_forecast: every building for one hour (used by map / dashboard)
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session

from ..config import CALENDAR_JSON, MODELS_DIR, ROOMS_JSON
from ..models import Occupancy

# ---------------- static resources ----------------
with open(ROOMS_JSON, encoding="utf-8") as f:
    ROOMS_META = json.load(f)

ROOMS = {r["room"]: r for r in ROOMS_META["rooms"]}
BUILDING_NUM = ROOMS_META["building_num"]
ROOM_NUM = ROOMS_META["room_num"]

_calendar = {}
try:
    with open(CALENDAR_JSON, encoding="utf-8") as f:
        _raw_cal = json.load(f)
    _calendar = {row["date"]: row for row in _raw_cal}
except FileNotFoundError:
    _calendar = {}

_model = None
_named_models = {}
_meta = None

_lstm_model = None
_lstm_meta = None
_lstm_scaler = None


def load_model() -> tuple:
    global _model, _meta
    if _model is not None:
        return _model, _meta
    pkl = MODELS_DIR / "occupancy_model.pkl"
    if not pkl.exists():
        raise RuntimeError(f"Model not found at {pkl}. Run: py -3.11 ml/train_model.py")
    _model = joblib.load(pkl)
    with open(MODELS_DIR / "meta.json", encoding="utf-8") as f:
        _meta = json.load(f)
    return _model, _meta


def load_named_model(name: str):
    if name == "xgb":
        return load_model()[0]
    if name not in {"rf", "lgbm", "lr"}:
        raise RuntimeError(f"Unknown forecast model '{name}'.")
    if name not in _named_models:
        path = MODELS_DIR / f"occupancy_model_{name}.pkl"
        if not path.exists():
            raise RuntimeError(
                f"Model '{name}' is not trained yet. Run: python ml/train_model.py")
        _named_models[name] = joblib.load(path)
    return _named_models[name]


# ---------------- LSTM (optional, lazy loaded) ----------------
def load_lstm_model() -> tuple:
    global _lstm_model, _lstm_meta
    if _lstm_model is not None:
        return _lstm_model, _lstm_meta
    keras_path = MODELS_DIR / "occupancy_lstm.keras"
    meta_path = MODELS_DIR / "lstm_meta.json"
    if not keras_path.exists() or not meta_path.exists():
        raise RuntimeError(f"LSTM model not found. Run: py -3.11 ml/train_lstm.py")
    from tensorflow import keras  # heavy import, loaded on demand
    _lstm_model = keras.models.load_model(keras_path)
    with open(meta_path, encoding="utf-8") as f:
        _lstm_meta = json.load(f)
    return _lstm_model, _lstm_meta


def load_lstm_scaler():
    global _lstm_scaler
    if _lstm_scaler is not None:
        return _lstm_scaler
    _, meta = load_lstm_model()
    scaler_path = MODELS_DIR / meta.get("scaler", "lstm_scaler.pkl")
    if not scaler_path.exists():
        raise RuntimeError(f"LSTM scaler not found at {scaler_path}. "
                           f"Run: py -3.11 ml/train_lstm.py")
    _lstm_scaler = joblib.load(scaler_path)
    return _lstm_scaler


# ---------------- calendar / context helpers ----------------
def get_date_context(d: str) -> dict:
    if d in _calendar:
        row = _calendar[d]
        weather_code = {"Normal": 0, "Hot": 1, "Cold": 2, "Rainy": 3, "Stormy": 4}.get(
            row["weather"], 0)
        return {
            "date": d, "semester": int(row["semester"]),
            "event": 1 if row["event"] else 0,
            "holiday": int(row.get("holiday", 0)),
            "weather": row["weather"], "weather_code": weather_code,
            "temperature": float(row["temperature"]),
        }
    dt = date.fromisoformat(d)
    m = dt.month
    semester = 1 if m in (3, 4, 5, 8, 9, 10, 11, 12) else 0
    return {
        "date": d, "semester": semester, "event": 0, "holiday": 0,
        "weather": "Normal", "weather_code": 0, "temperature": 28.0,
    }


def _day_of_week(d: str) -> int:
    return date.fromisoformat(d).weekday()


def _prev_day(d: str) -> str:
    return (date.fromisoformat(d) - timedelta(days=1)).isoformat()


# ---------------- feature vector ----------------
def feature_row(d: str, hour: int, room: dict, prev_hour: float, prev_day: float) -> np.ndarray:
    ctx = get_date_context(d)
    dt = date.fromisoformat(d)
    values = {
        "hour": hour,
        "day_of_week": _day_of_week(d),
        "month": dt.month,
        "is_weekend": 1 if dt.weekday() >= 5 else 0,
        "semester": ctx["semester"],
        "event": ctx["event"],
        "holiday": ctx["holiday"],
        "weather_code": ctx["weather_code"],
        "temperature": ctx["temperature"],
        "building_num": BUILDING_NUM[room["building"]],
        "room_num": ROOM_NUM[room["room"]],
        "capacity": room["capacity"],
        "prev_hour_occ": float(prev_hour),
        "prev_day_occ": float(prev_day),
    }
    _, meta = load_model()
    fields = meta["feature_columns"]
    return np.array([values[c] for c in fields], dtype=float).reshape(1, -1)


def predict_row(d: str, hour: int, room: dict, prev_hour: float, prev_day: float,
                model_name: str = "xgb") -> int:
    model = load_named_model(model_name)
    x = feature_row(d, hour, room, prev_hour, prev_day)
    val = float(model.predict(x)[0])
    return int(round(max(0.0, val)))


# ---------------- history lookups ----------------
def _actual(db: Session, room_id: int, d: str, hour: int) -> float:
    q = db.query(Occupancy).filter(
        Occupancy.room_id == room_id,
        Occupancy.date == d,
        Occupancy.hour == hour).first()
    return float(q.occupancy_count) if q else 0.0


def _real_prev_hour(db: Session, room_id: int, d: str, hour: int) -> float:
    if hour <= 8:
        return 0.0
    q = db.query(Occupancy).filter(
        Occupancy.room_id == room_id,
        Occupancy.date == d,
        Occupancy.hour == hour - 1).first()
    return float(q.occupancy_count) if q else 0.0


def _real_prev_day(db: Session, room_id: int, d: str, hour: int) -> float:
    q = db.query(Occupancy).filter(
        Occupancy.room_id == room_id,
        Occupancy.date == _prev_day(d),
        Occupancy.hour == hour).first()
    return float(q.occupancy_count) if q else 0.0


# ---------------- public API ----------------
def predict_room(db: Session, room: dict, room_id: int, d: str, hour: int,
                 chain_prev_hour: float | None = None,
                 model_name: str = "xgb") -> int:
    prev_hour = chain_prev_hour if chain_prev_hour is not None else _real_prev_hour(db, room_id, d, hour)
    prev_day = _real_prev_day(db, room_id, d, hour)
    return predict_row(d, hour, room, prev_hour, prev_day, model_name)


# ---------------- LSTM prediction ----------------
def _actual_series(db: Session, room_id: int, upto_date: str, upto_hour: int,
                   n: int) -> list[tuple[str, int, float]]:
    """The last `n` recorded occupancy rows for a room strictly before (date, hour)."""
    from sqlalchemy import or_
    rows = (
        db.query(Occupancy.date, Occupancy.hour, Occupancy.occupancy_count)
        .filter(
            Occupancy.room_id == room_id,
            or_(Occupancy.date < upto_date,
                (Occupancy.date == upto_date) & (Occupancy.hour < upto_hour)),
        )
        .order_by(Occupancy.date.asc(), Occupancy.hour.asc())
        .all()
    )
    return [(d, int(h), float(v)) for d, h, v in rows[-n:]]


def _hour_before(d: str, hour: int) -> tuple[str, int]:
    if hour > 8:
        return d, hour - 1
    return (date.fromisoformat(d) - timedelta(days=1)).isoformat(), 20


def _lstm_feature(room: dict, d: str, hour: int, prev_hour: float,
                  prev_day: float) -> list[float]:
    """Feature vector in the exact column order used to train the LSTM."""
    ctx = get_date_context(d)
    dt = date.fromisoformat(d)
    values = {
        "hour": hour,
        "day_of_week": _day_of_week(d),
        "month": dt.month,
        "is_weekend": 1 if dt.weekday() >= 5 else 0,
        "semester": ctx["semester"],
        "event": ctx["event"],
        "holiday": ctx["holiday"],
        "weather_code": ctx["weather_code"],
        "temperature": ctx["temperature"],
        "building_num": BUILDING_NUM[room["building"]],
        "room_num": ROOM_NUM[room["room"]],
        "capacity": room["capacity"],
        "prev_hour_occ": float(prev_hour),
        "prev_day_occ": float(prev_day),
    }
    _, meta = load_lstm_model()
    return [values[c] for c in meta["feature_columns"]]


def predict_lstm_room(db: Session, room: dict, room_id: int, d: str, hour: int) -> int:
    model, meta = load_lstm_model()
    scaler = load_lstm_scaler()
    window = int(meta["window"])

    prev = _actual_series(db, room_id, d, hour, window + 1)
    while len(prev) < window + 1:
        nd, nh = _hour_before(*prev[0][:2])
        prev.insert(0, (nd, nh, 0.0))

    feats = []
    for i in range(1, len(prev)):
        dd, hh, _ = prev[i]
        prev_hour = prev[i - 1][2]
        prev_day = _actual(db, room_id, (date.fromisoformat(dd) - timedelta(days=1)).isoformat(), hh)
        feats.append(_lstm_feature(room, dd, hh, prev_hour, prev_day))

    arr = np.array(feats, dtype=float)
    x = scaler.transform(arr).reshape(1, window, -1)
    val = float(model.predict(x, verbose=0)[0, 0])
    return int(round(max(0.0, val)))


def predict_building(db: Session, building_code: str, d: str, hour: int,
                     with_rooms=False, model: str = "xgb"):
    from ..models import Building, Room
    b = db.query(Building).filter(Building.code == building_code).first()
    if not b:
        raise KeyError(f"Unknown building '{building_code}'")
    rooms = db.query(Room).filter(Room.building_id == b.id).all()

    total = 0
    details = []
    for r in sorted(rooms, key=lambda x: x.code):
        meta = ROOMS[r.code]
        if model == "lstm":
            pred = predict_lstm_room(db, meta, r.id, d, hour)
        else:
            pred = predict_room(db, meta, r.id, d, hour, model_name=model)
        total += pred
        details.append({
            "room": r.code,
            "type": r.room_type,
            "capacity": r.capacity,
            "predicted": pred,
            "utilization": round(pred / r.capacity * 100, 1) if r.capacity else 0,
        })

    capacity = sum(r.capacity for r in rooms)
    usable = total / capacity * 100 if capacity else 0
    status = "Overcrowded" if total > capacity else ("High" if usable >= 80 else
              ("Medium" if usable >= 50 else "Low"))
    result = {
        "building": building_code,
        "building_name": b.name,
        "date": d, "hour": hour,
        "predicted_occupancy": total,
        "capacity": capacity,
        "utilization": round(usable, 1),
        "status": status,
        "context": get_date_context(d),
    }
    if with_rooms:
        result["rooms"] = details
    return result


def predict_day(db: Session, building_code: str, d: str, with_rooms=False) -> dict:
    from ..models import Building, Room
    from ..config import HOURS

    b = db.query(Building).filter(Building.code == building_code).first()
    if not b:
        raise KeyError(f"Unknown building '{building_code}'")
    rooms = db.query(Room).filter(Room.building_id == b.id).order_by(Room.code).all()
    room_metas = {r.id: ROOMS[r.code] for r in rooms}

    curve, per_room = [], {}
    chain = {rid: None for rid in room_metas}
    for hour in HOURS:
        building_total = 0
        hour_details = []
        for r in rooms:
            h = chain[r.id]
            pred = predict_room(db, room_metas[r.id], r.id, d, hour, chain_prev_hour=h)
            chain[r.id] = float(pred)
            building_total += pred
            hour_details.append(pred)
        curve.append({"hour": hour, "predicted": building_total})
        per_room[hour] = hour_details

    result = {
        "building": building_code,
        "building_name": b.name,
        "date": d,
        "curve": curve,
        "context": get_date_context(d),
    }
    if with_rooms:
        rooms_out = []
        for i, r in enumerate(rooms):
            rooms_out.append({
                "room": r.code, "capacity": r.capacity,
                "curve": [per_room[h][i] for h in HOURS],
            })
        result["rooms"] = rooms_out
        result["hours"] = HOURS
    return result


def campus_forecast(db: Session, d: str, hour: int) -> dict:
    from ..models import Building
    buildings = db.query(Building).order_by(Building.code).all()
    items = [predict_building(db, b.code, d, hour, with_rooms=True) for b in buildings]
    total = sum(i["predicted_occupancy"] for i in items)
    capacity = sum(i["capacity"] for i in items)
    return {
        "date": d, "hour": hour,
        "total_predicted": total,
        "total_capacity": capacity,
        "utilization": round(total / capacity * 100, 1) if capacity else 0,
        "buildings": items,
    }


def model_metrics() -> dict:
    _, meta = load_model()
    return meta

