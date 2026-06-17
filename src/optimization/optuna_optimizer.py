"""
Optuna tuner for XGBoost hyperparameters (simple regression objective).
"""
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from pathlib import Path
from config import OPTUNA_TRIALS

def tune(csv_path: str, target_col: str = "lst"):
    df = pd.read_csv(csv_path)
    X = df.drop(columns=[target_col, "x", "y"], errors="ignore")
    y = df[target_col]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)

    def objective(trial):
        params = {
            "tree_method": "hist",
            "objective": "reg:squarederror",
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "eta": trial.suggest_loguniform("eta", 0.01, 0.3),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        }
        num_round = trial.suggest_int("num_round", 50, 300)
        model = xgb.train(params, dtrain, num_boost_round=num_round)
        preds = model.predict(dval)
        return mean_squared_error(y_val, preds, squared=False)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=OPTUNA_TRIALS)
    return study.best_params, study.best_value
