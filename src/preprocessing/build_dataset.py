"""
Preprocessing pipeline that:
 - reads rasters from data/raw/
 - aligns CRS and resolution to a reference raster
 - removes nodata
 - flattens and writes data/processed/urban_heat_dataset.csv
"""
from typing import Dict, Optional
import os
from pathlib import Path
import logging
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import xy as transform_xy
from config import RAW_DIR, PROCESSED_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_INPUTS = {
    "lst": RAW_DIR / "lst_bengaluru.tif",
    "ndvi": RAW_DIR / "ndvi_bengaluru.tif",
    "ndbi": RAW_DIR / "ndbi_bengaluru.tif",
    "albedo": RAW_DIR / "albedo_bengaluru.tif",
    "lulc": RAW_DIR / "lulc_bengaluru.tif",
}

def _open(path: Path):
    return rasterio.open(path)

def _reproject_array(src_ds, target_profile, resampling: Resampling):
    dst = np.full((target_profile["height"], target_profile["width"]), np.nan, dtype=np.float32)
    src_arr = src_ds.read(1).astype(np.float32)
    src_nodata = src_ds.nodata
    if src_nodata is not None:
        src_arr = np.where(src_arr == src_nodata, np.nan, src_arr)
    reproject(
        source=src_arr,
        destination=dst,
        src_transform=src_ds.transform,
        src_crs=src_ds.crs,
        dst_transform=target_profile["transform"],
        dst_crs=target_profile["crs"],
        resampling=resampling,
        dst_nodata=np.nan
    )
    return dst

def build_dataset(inputs: Optional[Dict[str, Path]] = None, max_rows: int = 250000) -> Path:
    inputs = inputs or DEFAULT_INPUTS
    # Validate
    for k, p in inputs.items():
        if not Path(p).exists():
            raise FileNotFoundError(f"Required raster {k} missing: {p}")

    ref_key = next(iter(inputs))
    logger.info(f"Using {ref_key} as reference grid.")
    with _open(inputs[ref_key]) as ref_ds:
        target_profile = {"crs": ref_ds.crs, "transform": ref_ds.transform, "width": ref_ds.width, "height": ref_ds.height}

    arrays = {}
    for k, p in inputs.items():
        logger.info(f"Reprojecting {k}")
        with _open(p) as ds:
            resampling = Resampling.nearest if "lulc" in k.lower() else Resampling.bilinear
            arr = _reproject_array(ds, target_profile, resampling)
            arrays[k] = arr

    # Build coordinate arrays
    h, w = target_profile["height"], target_profile["width"]
    rows = np.arange(h)
    cols = np.arange(w)
    cc, rr = np.meshgrid(cols, rows)
    xs, ys = transform_xy(target_profile["transform"], rr, cc)
    data = {"x": np.array(xs).ravel(), "y": np.array(ys).ravel()}
    for k, arr in arrays.items():
        data[k] = arr.ravel()

    df = pd.DataFrame(data)
    feature_cols = [c for c in df.columns if c not in ("x", "y")]
    logger.info("Dropping rows with nodata in any feature")
    df = df.dropna(subset=feature_cols, how="any").reset_index(drop=True)

    if len(df) > max_rows:
        frac = float(max_rows) / len(df)
        logger.info(f"Downsampling to {max_rows} rows (frac={frac:.4f})")
        df = df.sample(frac=frac, random_state=42).reset_index(drop=True)

    out_path = Path(PROCESSED_DIR) / "urban_heat_dataset.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Saved processed dataset to {out_path} rows={len(df)}")
    return out_path

if __name__ == "__main__":
    build_dataset()
