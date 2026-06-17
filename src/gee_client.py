"""
Earth Engine ingestion and feature extraction.
Provides functions to produce NDVI, NDBI, ALBEDO and LST images for a study region.
"""
from typing import Tuple
import ee
from src.gee_auth import authenticate

# Note: callers should authenticate first; these functions assume ee is initialized
def sentinel2_median(region: ee.Geometry, start: str, end: str, cloud_thresh: float = 20.0) -> ee.Image:
    col = ee.ImageCollection("COPERNICUS/S2_SR") \
            .filterBounds(region) \
            .filterDate(start, end) \
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_thresh))
    median = col.median().clip(region)
    return median

def compute_ndvi(image: ee.Image, nir="B8", red="B4") -> ee.Image:
    return image.normalizedDifference([nir, red]).rename("ndvi")

def compute_ndbi(image: ee.Image, swir="B11", nir="B8") -> ee.Image:
    return image.normalizedDifference([swir, nir]).rename("ndbi")

def compute_albedo(image: ee.Image) -> ee.Image:
    # Coefficients from simple broadband approximation; refine for production
    coeffs = {"B2": 0.356, "B3": 0.130, "B4": 0.373, "B8": 0.085, "B11": 0.072}
    weighted = None
    for band, c in coeffs.items():
        b = image.select(band).multiply(c)
        weighted = b if weighted is None else weighted.add(b)
    albedo = weighted.subtract(0.0018).rename("albedo")
    return albedo.max(0).min(1)

def landsat8_lst(region: ee.Geometry, start: str, end: str) -> ee.Image:
    """
    Approximate LST from Landsat 8 L2 (ST_B10) when available. Returns Kelvin-ish values when using L2.
    """
    col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(region).filterDate(start, end)
    def pick(img):
        bands = img.bandNames()
        def has_st():
            return img.select("ST_B10").multiply(0.00341802).rename("lst")
        def fallback():
            return img.select("B10").rename("lst")
        return ee.Image(ee.Algorithms.If(bands.contains("ST_B10"), has_st(), fallback()))
    mapped = col.map(lambda i: ee.Image(pick(i)))
    lst = mapped.median().clip(region).rename("lst")
    return lst
