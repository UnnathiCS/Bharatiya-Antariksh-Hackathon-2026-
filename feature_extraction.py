"""
Feature extraction utilities using Google Earth Engine (ee).
Functions return ee.Image objects (single-band or multi-band) ready for export.
"""
from typing import Tuple
import ee

def compute_ndvi_s2(image: ee.Image, nir: str = "B8", red: str = "B4") -> ee.Image:
    """
    Compute NDVI for a Sentinel-2 image (SR collection).
    Returns single-band image named 'NDVI'.
    """
    ndvi = image.normalizedDifference([nir, red]).rename("ndvi")
    return ndvi

def compute_ndbi_s2(image: ee.Image, swir: str = "B11", nir: str = "B8") -> ee.Image:
    """
    Compute NDBI for Sentinel-2 image: (SWIR - NIR) / (SWIR + NIR)
    Returns single-band image named 'ndbi'.
    """
    ndbi = image.normalizedDifference([swir, nir]).rename("ndbi")
    return ndbi

def compute_albedo_s2(image: ee.Image) -> ee.Image:
    """
    Approximate broadband albedo from Sentinel-2 SR bands using a linear combination.
    Coefficients are an approximation; refine for production based on literature.
    Expects Sentinel-2 bands: B2,B3,B4,B8,B11 (blue, green, red, nir, swir1)
    """
    # Ensure we use surface reflectance (scale factor already applied in SR)
    # coefficients based on a rough broadband approximation (modify for your needs)
    coeffs = {
        "B2": 0.356,  # blue
        "B3": 0.130,  # green
        "B4": 0.373,  # red
        "B8": 0.085,  # nir
        "B11": 0.072, # swir1
    }
    bands = []
    weighted = None
    for b, c in coeffs.items():
        band = image.select(b).multiply(c)
        if weighted is None:
            weighted = band
        else:
            weighted = weighted.add(band)
    albedo = weighted.subtract(0.0018).rename("albedo")
    # Clip to sensible range
    albedo = albedo.max(0).min(1)
    return albedo

def get_landsat8_lst(collection_id: str, region: ee.Geometry, start: str, end: str) -> ee.Image:
    """
    Retrieve Landsat 8 LST approximation over region and time range.
    Uses L2 collection if available (prefer ST_B10 band), otherwise returns brightness temperature approximation.
    Returns a single-band image named 'lst' in Kelvin (where available) or relative brightness.
    """
    col = ee.ImageCollection(collection_id).filterBounds(region).filterDate(start, end)

    # Try surface temperature band (Landsat L2 has 'ST_B10')
    def use_st(img):
        return img.select(["ST_B10"]).multiply(0.00341802).rename("lst")  # scale example for L2

    # Map with a safe selector
    def safe_select(img):
        bands = img.bandNames()
        return ee.Algorithms.If(bands.contains("ST_B10"),
                                use_st(img),
                                # fallback: use brightness temperature from B10 using radiance->temp (simplified)
                                img.select(["B10"]).rename("lst"))
    mapped = col.map(lambda im: ee.Image(safe_select(im)))
    # Composite (median) to get a single image
    lst = mapped.median().rename("lst")
    return lst

def sentinel2_median(region: ee.Geometry, start: str, end: str, cloud_thresh: float = 0.2) -> ee.Image:
    """
    Return a median Sentinel-2 SR image clipped to region and filtered by cloud cover threshold.
    """
    s2 = ee.ImageCollection("COPERNICUS/S2_SR") \
            .filterBounds(region) \
            .filterDate(start, end) \
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_thresh * 100.0))
    median = s2.median().clip(region)
    return median
