"""
Central configuration for Urban Heat Mitigation project.
Reads environment variables and exposes constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
RAW_DIR = Path(os.getenv("RAW_DIR", DATA_DIR / "raw"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", DATA_DIR / "processed"))
MODEL_DIR = Path(os.getenv("MODEL_DIR", BASE_DIR / "models"))
LOG_DIR = Path(os.getenv("LOG_DIR", BASE_DIR / "logs"))

for d in (DATA_DIR, RAW_DIR, PROCESSED_DIR, MODEL_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

# GEE
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GEE_SERVICE_ACCOUNT = os.getenv("GEE_SERVICE_ACCOUNT")
GEE_PROJECT = os.getenv("GEE_PROJECT")

# Streamlit
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
SECRET_KEY = os.getenv("SECRET_KEY", "change_me_for_prod")

# Training defaults
XGB_PARAMS = {
    "nrounds": int(os.getenv("XGB_NUM_ROUNDS", "200")),
    "max_depth": int(os.getenv("XGB_MAX_DEPTH", "6")),
    "eta": float(os.getenv("XGB_LEARNING_RATE", "0.05")),
    "objective": "reg:squarederror",
}

# Optuna
OPTUNA_TRIALS = int(os.getenv("OPTUNA_TRIALS", "20"))
