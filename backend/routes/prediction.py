"""Forecasting routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import optional_user, require_admin
from ..models import Building, Prediction, User
from ..schemas import PredictRequest
from ..services import forecasting

router = APIRouter(prefix="/api", tags=["prediction"])


def _store_prediction(db: Session, user: User | None, building_code: str,
                      date, hour, pred, model):
    b = db.query(Building).filter(Building.code == building_code).first()
    db.add(Prediction(
        user_id=user.id if user else None,
        building_id=b.id if b else None,
        date=date, hour=hour, predicted_occupancy=int(pred), model=model))
    db.commit()


@router.post("/predict")
def predict(body: PredictRequest, db: Session = Depends(get_db),
            user: User | None = Depends(optional_user)):
    date_s, hour = body.date, body.hour
    if hour < 8 or hour > 20:
        raise HTTPException(status_code=422, detail="Forecasts are valid for 08:00-20:00.")
    try:
        result = forecasting.predict_building(db, body.building, date_s, hour,
                                              with_rooms=True, model=body.model)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    _store_prediction(db, user, body.building, date_s, hour, result["predicted_occupancy"], body.model)
    return result


@router.get("/predict/day")
def predict_day(building: str, dt: str = Query(..., alias="date"),
                db: Session = Depends(get_db)):
    try:
        return forecasting.predict_day(db, building, dt, with_rooms=True)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/predict/campus")
def predict_campus(dt: str = Query(..., alias="date"),
                   hour: int = Query(..., ge=0, le=23), db: Session = Depends(get_db)):
    return forecasting.campus_forecast(db, dt, hour)


@router.get("/predict/overcapacity")
def overcapacity(dt: str = Query(..., alias="date"), hour: int = Query(8, ge=0, le=23),
                 threshold: int = Query(80, ge=1, le=100),
                 db: Session = Depends(get_db)):
    data = forecasting.campus_forecast(db, dt, hour)
    flagged = []
    for b in data["buildings"]:
        util = b["utilization"]
        if util >= threshold:
            flagged.append({
                "building": b["building"], "building_name": b["building_name"],
                "utilization": util, "predicted": b["predicted_occupancy"],
                "capacity": b["capacity"],
            })
    return {"date": dt, "hour": hour, "threshold": threshold,
            "count": len(flagged), "areas": flagged}


@router.get("/predict/peak")
def peak_hour(building: str, dt: str = Query(..., alias="date"),
              db: Session = Depends(get_db)):
    day = forecasting.predict_day(db, building, dt)
    peak = max(day["curve"], key=lambda c: c["predicted"])
    return {**day, "peak": peak}


@router.get("/model/metrics")
def model_metrics():
    try:
        return forecasting.model_metrics()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/model/compare")
def compare_models():
    """
    Compare forecasting models across MAE, RMSE, MAPE, R2, and training time.
    Calculated strictly on chronological hold-out data.
    """
    try:
        meta = forecasting.model_metrics()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    metrics_dict = meta.get("metrics", {})
    comparison_table = []
    for model_name, scores in metrics_dict.items():
        comparison_table.append({
            "model": model_name,
            "MAE": scores.get("MAE"),
            "RMSE": scores.get("RMSE"),
            "MAPE": f"{scores.get('MAPE')}%",
            "R2": scores.get("R2"),
            "training_time_s": scores.get("training_time_s", "-"),
            "status": "Ready",
        })

    # Sort descending by R2
    comparison_table.sort(key=lambda x: x["R2"] if isinstance(x["R2"], (int, float)) else -1, reverse=True)

    return {
        "active_model": meta.get("model", "XGBRegressor"),
        "trained_on": meta.get("trained_on"),
        "total_samples": meta.get("n_samples"),
        "train_samples": meta.get("split_point"),
        "test_samples": (meta.get("n_samples", 0) - meta.get("split_point", 0)) if meta.get("split_point") else None,
        "feature_columns": meta.get("feature_columns", []),
        "split_method": "Chronological hold-out (85% train, 15% test)",
        "models": comparison_table,
        "disclaimer": "Models are evaluated on synthetic demonstration data. Real-world accuracy requires calibration against physical campus sensor streams or attendance registers.",
    }


@router.post("/model/retrain")
def retrain_model(user: User = Depends(require_admin)):
    """
    Trigger retraining of baseline models on current features.
    Saves new weights and updates meta metrics.
    """
    import subprocess
    import sys
    from ..config import ML_DIR
    try:
        proc = subprocess.run(
            [sys.executable, str(ML_DIR / "train_model.py")],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        # Clear model cache in forecasting service
        forecasting._model = None
        forecasting._meta = None
        forecasting._named_models.clear()
        new_meta = forecasting.model_metrics()
        return {
            "status": "success",
            "message": "Models successfully retrained and reloaded.",
            "metrics": new_meta.get("metrics", {}),
            "output": proc.stdout[-500:],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")


@router.get("/predictions")
def history(limit: int = Query(30, ge=1, le=200), db: Session = Depends(get_db)):
    rows = (db.query(Prediction).order_by(Prediction.id.desc()).limit(limit).all())
    out = []
    for p in rows:
        building = db.query(Building).filter(Building.id == p.building_id).first() if p.building_id else None
        out.append({
            "id": p.id, "date": p.date, "hour": p.hour,
            "building": building.code if building else None,
            "predicted_occupancy": p.predicted_occupancy,
            "model": p.model, "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return out

