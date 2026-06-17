"""
Feature engineering for tabular ML pipeline.
Includes stacking remote-sensing layers, neighborhood stats, temporal aggregations.
"""
import numpy as np
import pandas as pd
from typing import List

def create_feature_table(rasters: List[np.ndarray], meta: dict) -> pd.DataFrame:
    """
    Convert list of aligned raster arrays into a flat feature table per pixel or sample.
    - rasters: list of 2D numpy arrays (same shape)
    - meta: dict with coords or indices
    Returns DataFrame with features per sample.
    """
    # ...existing code...
    raise NotImplementedError("create_feature_table not implemented")

def add_physics_constraints(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply physics-informed derived features or constraints:
    e.g., enforce albedo range, ensure NDVI in [-1,1], create variables like fractional impervious surface.
    This function can add additional columns used by the model or for post-processing.
    """
    # ...existing code...
    # Placeholder: enforce sensible ranges
    df = df.copy()
    if "ndvi" in df.columns:
        df["ndvi"] = df["ndvi"].clip(-1.0, 1.0)
    if "albedo" in df.columns:
        df["albedo"] = df["albedo"].clip(0.0, 1.0)
    return df