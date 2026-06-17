"""
Earth Engine ingestion helpers: Landsat LST, Sentinel-2 NDVI, NDBI, albedo, LULC.
Provide small, testable functions that return ee.Image or exported arrays.
"""
from typing import Tuple, Dict, Any
import ee
from config import gee_init

# Initialize EE (call gee_init after importing; tests can mock ee)
try:
    gee_init(ee)
except Exception:
    # In CI or when credentials are not set we allow import to continue.
    pass

def get_landsat_lst(collection_id: str, region: ee.Geometry, start: str, end: str) -> ee.Image:
    """
    Extract Landsat 8 Land Surface Temperature (LST) composite for the given period & region.
    Returns an ee.Image with LST band in Kelvin (or specified unit).
    """
    # ...existing code...
    # TODO: implement retrieval, cloud masking, emissivity correction.
    raise NotImplementedError("get_landsat_lst not implemented yet")

def get_sentinel_ndvi(collection_id: str, region: ee.Geometry, start: str, end: str) -> ee.Image:
    """
    Compute NDVI composite from Sentinel-2 for given period & region.
    """
    # ...existing code...
    raise NotImplementedError("get_sentinel_ndvi not implemented yet")

def compute_ndbi(image: ee.Image, nir_band: str = "B5", swir_band: str = "B6") -> ee.Image:
    """
    Compute Normalized Difference Built-up Index (NDBI).
    """
    # ...existing code...
    raise NotImplementedError("compute_ndbi not implemented yet")

def compute_albedo(image: ee.Image) -> ee.Image:
    """
    Compute broadband albedo from appropriate bands.
    """
    # ...existing code...
    raise NotImplementedError("compute_albedo not implemented yet")

def get_lulc(region: ee.Geometry, year: int = 2020) -> ee.Image:
    """
    Retrieve Land Use/Land Cover image for a region/year (e.g., ESA WorldCover or CCI).
    """
    # ...existing code...
    raise NotImplementedError("get_lulc not implemented yet")