# Urban Heat Mitigation and Cooling Strategies (MVP)-https://arkanetra-2026-unnathics--unnathics.replit.app/

watch the video : https://drive.google.com/file/d/1zpGkZM-Wa8YI8beFYLP6WpLdHkror07d/view?usp=sharing

Quickstart:
1. Copy `.env.example` -> `.env` and fill values (GEE credentials).
2. Create venv and install:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
3. Authenticate Earth Engine (or provide service account JSON).
4. Run Streamlit dashboard:
   streamlit run app/streamlit_app.py

Important folders:
- data/raw/: GeoTIFF exports from Earth Engine
- data/processed/: flattened dataset CSV
- models/: saved model artifacts
