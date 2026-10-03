"""
Feature engineering for occupancy forecasting.

Adds temporal lags (previous hour, previous day) used by the model.

Input :  ml/dataset.csv
Output:  ml/dataset_features.csv

Run:  py -3.11 ml/preprocessing.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ml"

FEATURE_COLUMNS = [
    "hour", "day_of_week", "month", "is_weekend", "semester",
    "event", "holiday", "weather_code", "temperature",
    "building_num", "room_num", "capacity",
    "prev_hour_occ", "prev_day_occ",
]

TARGET_COLUMN = "occupancy"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["room", "date", "hour"]).reset_index(drop=True)

    df["day_of_week"] = df["date"].dt.weekday
    df["month"] = df["date"].dt.month
    df["weather_code"] = df["weather"].map(
        {"Normal": 0, "Hot": 1, "Cold": 2, "Rainy": 3, "Stormy": 4})

    per_room = df.groupby(["room"], group_keys=False)
    df["prev_hour_occ"] = per_room["occupancy"].shift(1)
    df["prev_day_occ"] = per_room["occupancy"].shift(len(pd.unique(df["hour"])))

    df["prev_hour_occ"] = df["prev_hour_occ"].fillna(0)
    df["prev_day_occ"] = df["prev_day_occ"].fillna(0)

    # A new day starts at 08:00 -> clear the prev_hour lag across midnight so
    # the model never "sees" yesterday evening. prev_hour is only within-day.
    first_hour_of_day = (
        df.sort_values(["room", "date", "hour"])
          .groupby(["room", "date"], as_index=False)["hour"].first()
    )
    first_keys = set(zip(first_hour_of_day["room"], first_hour_of_day["date"], first_hour_of_day["hour"]))
    df["_key"] = list(zip(df["room"], df["date"], df["hour"]))
    df.loc[df["_key"].isin(first_keys), "prev_hour_occ"] = 0.0
    df = df.drop(columns=["_key"])

    return df[["date"] + FEATURE_COLUMNS + [TARGET_COLUMN]]


def main() -> None:
    raw = pd.read_csv(ML_DIR / "dataset.csv")
    feat = build_features(raw)
    feat.to_csv(ML_DIR / "dataset_features.csv", index=False)
    print(f"Feature table: {feat.shape[0]:,} rows x {feat.shape[1]} cols")
    print("Columns:", list(feat.columns))


if __name__ == "__main__":
    main()