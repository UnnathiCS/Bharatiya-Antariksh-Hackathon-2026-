"""Physics-informed analytics: risk scoring, optimization, priority zoning."""

from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

RISK_WEIGHTS = {
    "NDBI": 0.40,
    "ALBEDO": 0.25,
    "NDVI": -0.20,
    "EVI": -0.10,
    "MNDWI": -0.05,
}

SCENARIOS = {
    "A: +10% NDVI": {"ndvi_pct": 10, "albedo_pct": 0},
    "B: +20% NDVI": {"ndvi_pct": 20, "albedo_pct": 0},
    "C: +10% ALBEDO": {"ndvi_pct": 0, "albedo_pct": 10},
    "D: +20% ALBEDO": {"ndvi_pct": 0, "albedo_pct": 20},
    "E: Combined": {"ndvi_pct": 10, "albedo_pct": 10},
}


def _minmax_normalize(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi - lo == 0:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def compute_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Physics-informed Urban Heat Risk Index normalized to 0–100."""
    out = df.copy()
    required = ["NDBI", "ALBEDO", "NDVI", "EVI", "MNDWI"]
    for col in required:
        if col not in out.columns:
            out[col] = 0.0

    normed = {col: _minmax_normalize(out[col].astype(float)) for col in required}
    raw = sum(RISK_WEIGHTS[col] * normed[col] for col in required)

    out["risk_score_raw"] = raw
    out["risk_score"] = (_minmax_normalize(raw) * 100).round(1)
    return out


def apply_scenario(
    row: pd.Series,
    ndvi_pct: float,
    albedo_pct: float,
) -> pd.Series:
    """Apply intervention deltas consistent with the cooling simulator."""
    updated = row.copy()
    delta_ndvi = (ndvi_pct / 100.0) * 0.2
    delta_evi = (ndvi_pct / 100.0) * 0.2
    delta_albedo = (albedo_pct / 100.0) * 0.1

    if "NDVI" in updated.index:
        updated["NDVI"] = np.clip(float(updated["NDVI"]) + delta_ndvi, -1.0, 1.0)
    if "EVI" in updated.index:
        updated["EVI"] = np.clip(float(updated["EVI"]) + delta_evi, -1.0, 1.0)
    if "ALBEDO" in updated.index:
        updated["ALBEDO"] = np.clip(float(updated["ALBEDO"]) + delta_albedo, 0.0, 1.0)
    return updated


def build_feature_matrix(
    df: pd.DataFrame,
    feature_cols: List[str],
    geo_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Build prediction matrix including spectral and geo features."""
    cols = list(feature_cols)
    if geo_cols:
        for g in geo_cols:
            if g in df.columns and g not in cols:
                cols.append(g)
    available = [c for c in cols if c in df.columns]
    return df[available].astype(float).copy()


def run_optimizer(
    df_hotspots: pd.DataFrame,
    predict_fn: Callable[[pd.DataFrame], np.ndarray],
    feature_cols: List[str],
) -> pd.DataFrame:
    """
    For each hotspot, test intervention scenarios and select best cooling strategy.
    Returns leaderboard table with priority rank.
    """
    results = []
    geo_cols = ["longitude", "latitude"]

    for i, (_, row) in enumerate(df_hotspots.iterrows()):
        base_X = build_feature_matrix(pd.DataFrame([row]), feature_cols, geo_cols)
        current_temp = float(predict_fn(base_X)[0])

        best_strategy = "None"
        best_cooling = 0.0
        best_temp = current_temp

        for scenario_name, params in SCENARIOS.items():
            modified = apply_scenario(row, params["ndvi_pct"], params["albedo_pct"])
            new_X = build_feature_matrix(pd.DataFrame([modified]), feature_cols, geo_cols)
            new_temp = float(predict_fn(new_X)[0])
            cooling = current_temp - new_temp

            if cooling > best_cooling:
                best_cooling = cooling
                best_strategy = scenario_name
                best_temp = new_temp

        results.append(
            {
                "Hotspot ID": i + 1,
                "Current Temperature": round(current_temp, 2),
                "Best Strategy": best_strategy,
                "Expected Cooling (°C)": round(best_cooling, 3),
                "Predicted After": round(best_temp, 2),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
            }
        )

    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values("Expected Cooling (°C)", ascending=False).reset_index(drop=True)
    result_df["Priority Rank"] = range(1, len(result_df) + 1)
    return result_df


def assign_priority_zones(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign Priority Zone 1/2/3 based on composite of predicted_lst + risk_score.
    Uses Extreme and High heat_class hotspots.
    """
    mask = df["heat_class"].isin(["Extreme", "High"])
    subset = df.loc[mask].copy()
    if subset.empty:
        return subset

    lst_norm = _minmax_normalize(subset["predicted_lst"].astype(float))
    risk_norm = _minmax_normalize(subset["risk_score"].astype(float))
    subset["priority_composite"] = (lst_norm + risk_norm) / 2.0

    subset = subset.sort_values("priority_composite", ascending=False).reset_index(drop=True)
    n = len(subset)
    zone_labels = []
    for idx in range(n):
        if idx < n / 3:
            zone_labels.append("Priority Zone 1")
        elif idx < 2 * n / 3:
            zone_labels.append("Priority Zone 2")
        else:
            zone_labels.append("Priority Zone 3")

    subset["priority_zone"] = zone_labels
    return subset


def generate_recommendation(row: pd.Series, medians: Dict[str, float]) -> str:
    """Rule-based intervention recommendation for a hotspot."""
    recs = []
    if "NDBI" in row.index and row["NDBI"] > medians.get("NDBI", 0):
        recs.append("Install Cool Roofs")
    if "NDVI" in row.index and row["NDVI"] < medians.get("NDVI", 0):
        recs.append("Increase Tree Cover")
    if "MNDWI" in row.index and row["MNDWI"] < medians.get("MNDWI", 0):
        recs.append("Water Sensitive Urban Design")
    if not recs:
        recs.append("Monitor & Maintain")
    return "; ".join(recs)


def generate_driver_insights(df_feat: pd.DataFrame) -> List[str]:
    """Auto-generate narrative insights from feature importance."""
    if df_feat.empty or "feature" not in df_feat.columns:
        return ["Feature importance data unavailable for narrative insights."]

    spectral = df_feat[~df_feat["feature"].isin(["latitude", "longitude"])].copy()
    if spectral.empty:
        return ["Spectral feature importance data unavailable."]

    spectral = spectral.sort_values("importance", ascending=False)
    top = spectral.iloc[0]
    insights = []

    driver_map = {
        "NDBI": "Built-up intensity (NDBI) is the strongest driver of urban heating.",
        "NDVI": "Vegetation cover (NDVI) exhibits a cooling influence on land surface temperature.",
        "EVI": "Enhanced vegetation index (EVI) contributes to localized cooling effects.",
        "ALBEDO": "Surface reflectance (Albedo) is a key physical driver — higher albedo reduces heat absorption.",
        "MNDWI": "Water presence (MNDWI) shows a measurable cooling influence in urban areas.",
    }

    feat_name = str(top["feature"]).upper()
    for key, msg in driver_map.items():
        if key in feat_name.upper():
            insights.append(msg)
            break
    else:
        insights.append(f"{top['feature']} is the most influential spectral feature in the model.")

    for _, row in spectral.iterrows():
        feat = str(row["feature"]).upper()
        if "NDBI" in feat:
            insights.append("Built-up intensity is the strongest driver of urban heating.")
        elif "NDVI" in feat:
            insights.append("Vegetation exhibits a cooling influence.")
        elif "ALBEDO" in feat:
            insights.append("Higher surface albedo reflects solar radiation, reducing heat accumulation.")

    seen = set()
    unique = []
    for ins in insights:
        if ins not in seen:
            seen.add(ins)
            unique.append(ins)
    return unique[:4]


def estimate_avg_cooling_potential(
    df: pd.DataFrame,
    predict_fn: Callable[[pd.DataFrame], np.ndarray],
    feature_cols: List[str],
    sample_n: int = 200,
) -> float:
    """Estimate average best-case cooling potential across a sample."""
    if df.empty:
        return 0.0
    sample = df.sample(n=min(sample_n, len(df)), random_state=42)
    opt = run_optimizer(sample, predict_fn, feature_cols)
    if opt.empty:
        return 0.0
    return float(opt["Expected Cooling (°C)"].mean())
