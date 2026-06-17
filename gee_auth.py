"""
Helpers to authenticate and initialize Google Earth Engine (EE).
Supports:
- Application default credentials (gcloud auth application-default login)
- Service account JSON key + service account email
"""
import os
import ee

def authenticate(service_account: str = None, key_file: str = None, project: str = None):
    """
    Initialize Earth Engine.
    - service_account: optional service account email (e.g. 'sa@project.iam.gserviceaccount.com')
    - key_file: path to service account JSON key file
    - project: optional GCP project id (used for ee.Initialize)
    Returns initialized ee module.
    """
    # allow idempotent calls
    if ee.data._initialized:
        return ee

    if service_account and key_file:
        if not os.path.exists(key_file):
            raise FileNotFoundError(f"Service account key not found: {key_file}")
        credentials = ee.ServiceAccountCredentials(service_account, key_file)
        ee.Initialize(credentials, project=project)
    else:
        # Try default auth flow / local user auth
        try:
            ee.Initialize()
        except Exception as e:
            # if not authenticated, provide a helpful message
            raise RuntimeError(
                "Could not initialize Earth Engine. Ensure you ran `earthengine authenticate` "
                "or provided a service account and key file. Original error: " + str(e)
            )
    return ee
