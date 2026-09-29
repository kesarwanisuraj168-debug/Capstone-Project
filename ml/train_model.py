"""
Model evaluation & comparison for occupancy forecasting.

Trains several baselines (Linear / RandomForest / LightGBM / XGBoost) on the
engineered features and reports MAE, RMSE, MAPE and R2 on a time-based hold-out.

Run:  py -3.11 ml/train_model.py
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import FEATURE_COLUMNS, TARGET_COLUMN

ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ml"
MODELS_DIR = ML_DIR / "models"

FE = FEATURE_COLUMNS


def metrics(y_true, y_pred) -> dict:
    mape = float(np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100)
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAPE": round(mape, 2),
        "R2": round(float(r2_score(y_true, y_pred)), 4),
    }


def evaluate_model(name, model, X_train, y_train, X_test, y_test, results):
    model.fit(X_train, y_train)
    pred = np.clip(model.predict(X_test), 0, None)
    results[name] = metrics(y_test, pred)
    filename = {"LinearRegression": "occupancy_model_lr.pkl",
                "RandomForest": "occupancy_model_rf.pkl",
                "LightGBM": "occupancy_model_lgbm.pkl",
                "XGBoost": "occupancy_model_eval_xgb.pkl"}.get(name)
    if filename:
        joblib.dump(model, MODELS_DIR / filename)
    print(f"{name:>14}  " + "  ".join(f"{k}={v}" for k, v in results[name].items()))
    return model


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ML_DIR / "dataset_features.csv")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "room_num", "hour"]).reset_index(drop=True)

    # time-based split: last 15% is the hold-out
    split = int(len(df) * 0.85)
    y = df[TARGET_COLUMN].values
    X = df[FE].values
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print(f"Train rows {len(X_train):,} | Test rows {len(X_test):,}")
    results: dict = {}

    _ = evaluate_model("LinearRegression", LinearRegression(),
                       X_train, y_train, X_test, y_test, results)

    _ = evaluate_model("RandomForest", RandomForestRegressor(
        n_estimators=35, max_depth=18, n_jobs=-1, random_state=42),
        X_train, y_train, X_test, y_test, results)

    try:
        import lightgbm as lgb
        _ = evaluate_model("LightGBM", lgb.LGBMRegressor(
            n_estimators=600, learning_rate=0.05, num_leaves=63,
            colsample_bytree=0.8, subsample=0.8, n_jobs=-1, random_state=42),
            X_train, y_train, X_test, y_test, results)
    except Exception as e:  # noqa: BLE001
        print("LightGBM unavailable:", e)

    try:
        import xgboost as xgb
        best = evaluate_model("XGBoost", xgb.XGBRegressor(
            n_estimators=700, learning_rate=0.04, max_depth=7,
            subsample=0.8, colsample_bytree=0.8,
            n_jobs=-1, random_state=42, verbosity=0),
            X_train, y_train, X_test, y_test, results)
    except Exception as e:  # noqa: BLE001
        print("XGBoost unavailable, falling back to RandomForest as final model", e)
        best = RandomForestRegressor(n_estimators=35, max_depth=18,
                                     n_jobs=-1, random_state=42)
        best.fit(X_train, y_train)

    # final fit on ALL data for maximum prediction quality
    final = type(best)(**best.get_params())
    final.fit(np.vstack([X_train, X_test]), np.concatenate([y_train, y_test]))

    model_path = MODELS_DIR / "occupancy_model.pkl"
    joblib.dump(final, model_path)

    meta = {
        "model": type(final).__name__,
        "feature_columns": FE,
        "target": TARGET_COLUMN,
        "metrics": results,
        "trained_on": df["date"].max().strftime("%Y-%m-%d"),
        "n_samples": int(len(df)),
        "split_point": split,
    }
    with open(MODELS_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("\nSaved ->", model_path)


if __name__ == "__main__":
    main()