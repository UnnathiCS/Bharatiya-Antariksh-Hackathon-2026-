"""
Utilities to export ee.Image to local GeoTIFF using geemap.
"""
import os
import geemap
from typing import Optional
import ee
from config import RAW_DIR

def export_image_local(img: ee.Image, filename: str, region: ee.Geometry, scale: int = 30, crs: str = "EPSG:4326") -> str:
    out_path = os.path.join(RAW_DIR, filename)
    # geemap handles download; wrap exceptions for clearer messaging
    try:
        geemap.ee_export_image(img, filename=out_path, scale=scale, region=region, file_per_band=False, crs=crs)
    except Exception as exc:
        raise RuntimeError(f"Failed to export {filename}: {exc}")
    return out_path
