"""
Train an XGBoost model to predict LST from features.
Implements simple physics-informed monotonic constraints and model persistence.
"""
import os
from pathlib import Path
import joblib
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from config import MODEL_DIR, XGB_PARAMS

MODEL_DIR.mkdir(parents=True, exist_ok=True)

def _build_monotone_list(feature_names):
    """
    Map monotonic constraints:
    - NDVI should decrease LST => negative monotonic constraint (-1)
    - Albedo should decrease LST => negative constraint (-1)
    - NDBI (built-up) should increase LST => positive constraint (+1)
    Order must correspond to feature_names list for xgb parameter 'monotone_constraints'.
    """
    monotone_map = {"ndvi": -1, "albedo": -1, "ndbi": 1}
    return [monotone_map.get(f.lower(), 0) for f in feature_names]

def train_from_csv(csv_path: str, target_col: str = "lst", test_size: float = 0.2, random_state: int = 42):
    df = pd.read_csv(csv_path)
    # Ensure required columns
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in {csv_path}")
    X = df.drop(columns=[target_col, "x", "y"], errors="ignore")
    y = df[target_col]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=test_size, random_state=random_state)

    feature_names = list(X.columns)
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_names)
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=feature_names)

    params = {
        "max_depth": XGB_PARAMS.get("max_depth", 6),
        "eta": XGB_PARAMS.get("eta", 0.05),
        "objective": XGB_PARAMS.get("objective", "reg:squarederror"),
        "tree_method": "hist",
        "verbosity": 1,
    }
    # Attach monotone constraints as list string expected by xgboost
    monotone_list = _build_monotone_list(feature_names)
    if any(m != 0 for m in monotone_list):
        params["monotone_constraints"] = f"({','.join([str(int(m)) for m in monotone_list])})"

    num_round = XGB_PARAMS.get("nrounds", 200)
    model = xgb.train(params, dtrain, num_boost_round=num_round, evals=[(dval, "validation")])

    preds = model.predict(dval)
    rmse = mean_squared_error(y_val, preds, squared=False)

    out_path = Path(MODEL_DIR) / "xgb_model.joblib"
    joblib.dump({"model": model, "feature_names": feature_names}, out_path)

    return {"model_path": str(out_path), "rmse": float(rmse)}
