"""
Orchestration script to:
- Authenticate Earth Engine
- Build layers (LST, NDVI, NDBI, Albedo) for Bengaluru
- Export GeoTIFFs to data/raw/
- Sample composite and save CSV to data/raw/features.csv

Note: Exports use geemap.ee_export_image for local GeoTIFF writes.
"""
import os
import time
import ee
import geemap
import pandas as pd
from datetime import datetime
from gee_auth import authenticate
from feature_extraction import (
    sentinel2_median,
    compute_ndvi_s2,
    compute_ndbi_s2,
    compute_albedo_s2,
    get_landsat8_lst,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)

def _bengaluru_region(buffer_m=25000):
    """
    Approximate Bengaluru center and buffer (lon, lat)
    """
    lon, lat = 77.5946, 12.9716
    pt = ee.Geometry.Point([lon, lat])
    return pt.buffer(buffer_m).bounds()

def export_image_to_local(img: ee.Image, filename: str, region: ee.Geometry, scale: int = 30, crs: str = "EPSG:4326"):
    out_path = os.path.join(DATA_DIR, filename)
    # Use geemap to export to local GeoTIFF
    geemap.ee_export_image(
        img,
        filename=out_path,
        scale=scale,
        region=region,
        file_per_band=False,
        crs=crs
    )
    return out_path

def sample_image_to_csv(img: ee.Image, region: ee.Geometry, num_samples: int = 2000, scale: int = 30, out_csv: str = "features.csv"):
    """
    Sample the multi-band image randomly across the region and save to CSV.
    Uses ee.Image.sample with randomPoints; attempts to pull results client-side for moderate sizes.
    """
    sample_fc = img.sample(region=region, scale=scale, numPixels=num_samples, geometries=True)
    # getInfo can fail for big requests; keep it moderate
    info = sample_fc.getInfo()
    features = info.get("features", [])
    rows = []
    for f in features:
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = None
        if geom and geom.get("type") == "Point":
            coords = geom.get("coordinates")
            props["lon"] = coords[0]
            props["lat"] = coords[1]
        rows.append(props)
    df = pd.DataFrame(rows)
    out_path = os.path.join(DATA_DIR, out_csv)
    df.to_csv(out_path, index=False)
    return out_path

def run_pipeline(start_date="2020-01-01", end_date=None):
    """
    Main entry point for running the download pipeline.
    Returns list of log lines for UI display.
    """
    logs = []
    end_date = end_date or datetime.utcnow().strftime("%Y-%m-%d")
    logs.append(f"Pipeline started: {datetime.utcnow().isoformat()}")
    # Authenticate
    service_account = os.getenv("GEE_SERVICE_ACCOUNT")
    key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project = os.getenv("GEE_PROJECT")
    logs.append("Initializing Earth Engine...")
    try:
        ee = authenticate(service_account=service_account, key_file=key_file, project=project)
    except Exception as e:
        logs.append(f"Authentication failed: {e}")
        raise

    region = _bengaluru_region(buffer_m=25000)
    logs.append(f"Region defined (Bengaluru buffer).")

    # Sentinel-2 median composite
    logs.append("Building Sentinel-2 median composite...")
    s2 = sentinel2_median(region, start_date, end_date)
    logs.append("Computing NDVI, NDBI, Albedo...")
    ndvi = compute_ndvi_s2(s2)
    ndbi = compute_ndbi_s2(s2)
    albedo = compute_albedo_s2(s2)

    # Landsat LST (attempt L2 ST_B10 or fallback)
    logs.append("Retrieving Landsat-8 LST (approximation)...")
    lst = get_landsat8_lst("LANDSAT/LC08/C02/T1_L2", region, start_date, end_date)

    # Compose a multi-band image for sampling
    composite = ndvi.addBands(ndbi).addBands(albedo).addBands(lst).rename(["ndvi", "ndbi", "albedo", "lst"])
    # Export each single-band GeoTIFF
    exports = []
    try:
        logs.append("Exporting NDVI GeoTIFF...")
        p = export_image_to_local(ndvi, "ndvi_bengaluru.tif", region, scale=20)
        exports.append(p)
        logs.append(f"Saved {p}")

        logs.append("Exporting NDBI GeoTIFF...")
        p = export_image_to_local(ndbi, "ndbi_bengaluru.tif", region, scale=20)
        exports.append(p)
        logs.append(f"Saved {p}")

        logs.append("Exporting Albedo GeoTIFF...")
        p = export_image_to_local(albedo, "albedo_bengaluru.tif", region, scale=20)
        exports.append(p)
        logs.append(f"Saved {p}")

        logs.append("Exporting LST GeoTIFF...")
        p = export_image_to_local(lst, "lst_bengaluru.tif", region, scale=30)
        exports.append(p)
        logs.append(f"Saved {p}")
    except Exception as e:
        logs.append(f"Export failed: {e}")
        raise

    # Sample and export CSV
    logs.append("Sampling composite to CSV...")
    try:
        csv_path = sample_image_to_csv(composite, region, num_samples=2000, scale=30, out_csv="features_bengaluru.csv")
        logs.append(f"Saved CSV: {csv_path}")
    except Exception as e:
        logs.append(f"Sampling failed: {e}")
        raise

    logs.append("Pipeline finished.")
    return logs

# Convenience entry for import
def run_pipeline_entry():
    return run_pipeline()
    
# Allow running as script
if __name__ == "__main__":
    for line in run_pipeline():
        print(line)
