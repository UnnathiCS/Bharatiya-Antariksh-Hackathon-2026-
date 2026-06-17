"""
Simulate cooling interventions by perturbing features and using the trained model to predict LST changes.
Supports interventions on 'albedo' and 'ndvi' (increase).
"""
import joblib
import pandas as pd
import numpy as np
from typing import Dict
from pathlib import Path
from config import MODEL_DIR

def load_model():
    art = joblib.load(Path(MODEL_DIR) / "xgb_model.joblib")
    return art["model"], art["feature_names"]

def simulate(feature_df: pd.DataFrame, interventions: Dict[str, float]):
    """
    interventions: dict feature -> delta (absolute add to feature, e.g. {'albedo': 0.05, 'ndvi': 0.1})
    Returns DataFrame with baseline prediction and intervention prediction + delta.
    """
    model, feature_names = load_model()
    X = feature_df.copy()
    # Ensure columns present
    X_feat = X[feature_names].copy()

    dmat_base = model.DMatrix(X_feat)
    base_preds = model.predict(dmat_base)

    X_new = X_feat.copy()
    for k, v in interventions.items():
        if k in X_new.columns:
            X_new[k] = X_new[k] + v
    dmat_new = model.DMatrix(X_new)
    new_preds = model.predict(dmat_new)

    out = X.copy()
    out["pred_base"] = base_preds
    out["pred_intervention"] = new_preds
    out["delta_pred"] = out["pred_base"] - out["pred_intervention"]
    return out
