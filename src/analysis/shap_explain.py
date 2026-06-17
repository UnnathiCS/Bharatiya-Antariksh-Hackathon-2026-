"""
SHAP explainability for XGBoost model artifacts saved by train_xgboost.
"""
import joblib
import pandas as pd
import shap
import numpy as np

def explain(model_artifact_path: str, X: pd.DataFrame, max_display: int = 10):
    art = joblib.load(model_artifact_path)
    model = art["model"]
    feature_names = art.get("feature_names", X.columns.tolist())

    def pred(data):
        dmat = model.DMatrix(data)
        return model.predict(dmat)

    explainer = shap.Explainer(pred, feature_names=feature_names, algorithm="tree")
    shap_values = explainer(X)
    # Return objects; caller can render summaries
    return {"explainer": explainer, "shap_values": shap_values}
