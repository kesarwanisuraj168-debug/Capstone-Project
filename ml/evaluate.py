"""
Evaluate a trained model against the hold-out set and print a score summary.

Run:  py -3.11 ml/evaluate.py [model.pkl]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocessing import FEATURE_COLUMNS as FE, TARGET_COLUMN

ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ml"
MODELS_DIR = ML_DIR / "models"


def main() -> None:
    model_path = Path(sys.argv[1]) if len(sys.argv) > 1 else MODELS_DIR / "occupancy_model.pkl"
    model = joblib.load(model_path)
    meta = json.loads((MODELS_DIR / "meta.json").read_text(encoding="utf-8"))

    df = pd.read_csv(ML_DIR / "dataset_features.csv")
    split = int(len(df) * 0.85)
    y_test = df[TARGET_COLUMN].values[split:]
    X_test = df[FE].values[split:]
    pred = np.clip(model.predict(X_test), 0, None)

    mape = float(np.mean(np.abs((y_test - pred) / np.maximum(y_test, 1))) * 100)
    print(f"Model      : {meta['model']}")
    print(f"Trained on : {meta.get('trained_on','?')}  samples={meta.get('n_samples', len(df)):,}")
    print(f"Test rows  : {len(y_test):,}")
    print("-" * 60)
    print(f"MAE   : {mean_absolute_error(y_test, pred):.3f}")
    print(f"RMSE  : {np.sqrt(mean_squared_error(y_test, pred)):.3f}")
    print(f"MAPE  : {mape:.2f}%")
    print(f"R2    : {r2_score(y_test, pred):.4f}")


if __name__ == "__main__":
    main()