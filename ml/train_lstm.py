"""
(Optional) LSTM model for occupancy forecasting.

A simple 2-layer LSTM that consumes a per-room sequence of features and outputs
the next-hour occupancy. Kept separate from the main pipeline because TensorFlow
is heavy; the FastAPI backend loads this model lazily ONLY when the endpoint
/ predict with model="lstm" is requested and the file exists.

Run:  py -3.11 ml/train_lstm.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from preprocessing import FEATURE_COLUMNS as FE

ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ml"
MODELS_DIR = ML_DIR / "models"

WINDOW = 12  # past 12 hours


def main() -> None:
    import tensorflow as tf
    from tensorflow import keras

    df = pd.read_csv(ML_DIR / "dataset_features.csv")
    df = df.sort_values(["room_num", "date", "hour"]).reset_index(drop=True)
    n_features = len(FE)
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(df[FE].values)
    y_raw = df["occupancy"].values

    Xs, ys = [], []
    for room in df["room_num"].unique():
        idx = np.where(df["room_num"].values == room)[0]
        for i in range(WINDOW, len(idx)):
            Xs.append(X_scaled[idx[i - WINDOW: i]])
            ys.append(y_raw[idx[i]])
    Xs = np.asarray(Xs)
    ys = np.asarray(ys)
    split = int(len(Xs) * 0.85)

    model = keras.Sequential([
        keras.layers.LSTM(64, return_sequences=True, input_shape=(WINDOW, n_features)),
        keras.layers.LSTM(32),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    model.fit(Xs[:split], ys[:split], epochs=40, batch_size=256,
              validation_split=0.1, verbose=1)

    pred = np.clip(model.predict(Xs[split:]).ravel(), 0, None)
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    print("LSTM metrics:", {
        "MAE": float(mean_absolute_error(ys[split:], pred)),
        "RMSE": float(np.sqrt(mean_squared_error(ys[split:], pred))),
        "R2": float(r2_score(ys[split:], pred)),
    })

    model.save(MODELS_DIR / "occupancy_lstm.keras")
    import joblib
    joblib.dump(scaler, MODELS_DIR / "lstm_scaler.pkl")
    with open(MODELS_DIR / "lstm_meta.json", "w", encoding="utf-8") as f:
        json.dump({"window": WINDOW, "n_features": n_features,
                   "feature_columns": FE, "scaler": "lstm_scaler.pkl"}, f)


if __name__ == "__main__":
    main()