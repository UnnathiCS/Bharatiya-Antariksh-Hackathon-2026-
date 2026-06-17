"""
Earth Engine authentication helper.
Supports service account (key file + service account email) or user auth.
"""
import os
import ee
from config import GOOGLE_APPLICATION_CREDENTIALS, GEE_SERVICE_ACCOUNT, GEE_PROJECT

def authenticate(service_account: str = None, key_file: str = None, project: str = None):
    """
    Initialize and return the ee module.
    If service_account and key_file are provided, use service account credentials.
    Otherwise attempt ee.Initialize() (assumes user has run `earthengine authenticate`).
    """
    project = project or GEE_PROJECT
    key_file = key_file or GOOGLE_APPLICATION_CREDENTIALS
    service_account = service_account or GEE_SERVICE_ACCOUNT

    # safe idempotent init
    try:
        if service_account and key_file:
            if not os.path.exists(key_file):
                raise FileNotFoundError(f"Service account key not found: {key_file}")
            credentials = ee.ServiceAccountCredentials(service_account, key_file)
            ee.Initialize(credentials, project=project)
        else:
            ee.Initialize()
    except Exception as exc:
        # Surface the error (caller should handle)
        raise RuntimeError(f"Failed to initialize Earth Engine: {exc}")
    return ee
