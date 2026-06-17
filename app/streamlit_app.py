"""
ARKANETRA — Physics-Informed Urban Heat Intelligence Platform
Streamlit frontend orchestrating geospatial intelligence, ML predictions, and cooling optimization.
"""
import sys
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# Path setup
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from analytics import (  # noqa: E402
    assign_priority_zones,
    compute_risk_scores,
    estimate_avg_cooling_potential,
    generate_driver_insights,
    generate_recommendation,
    run_optimizer,
)
from components import (  # noqa: E402
    HEAT_CLASS_COLORS,
    get_map_layout,
    ZONE_COLORS,
    insight_card,
    leaderboard_bar,
    mission_card,
    page_header,
    render_footer,
    render_hero,
    render_sidebar_brand,
    risk_gauge,
    section_header,
)
from styles import get_arkanetra_css  # noqa: E402

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ARKANETRA | Urban Heat Intelligence",
    page_icon="☀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = PROJECT_ROOT
HEAT_PRED_PATH = BASE_DIR / "data" / "raw" / "processed" / "heat_predictions.csv"
FEATURE_IMPORTANCE_PATH = BASE_DIR / "outputs" / "feature_importance.csv"
SHAP_IMAGE_PATH = BASE_DIR / "outputs" / "shap_summary.png"
MODEL_PATH = BASE_DIR / "models" / "urban_heat_rf.pkl"
OUT_INTERVENTION_CSV = BASE_DIR / "outputs" / "intervention_results.csv"

PAGES = [
    "🏠 Home",
    "🌍 Heat Monitor",
    "📊 Heat Drivers",
    "🌱 Cooling Simulator",
    "🎯 Optimizer",
    "📍 Priority Zones",
]

SPECTRAL_FEATURES = ["ALBEDO", "EVI", "NDVI", "NDBI", "MNDWI"]


# ── Theme State & Sidebar Brand ──────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

render_sidebar_brand()
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
st.session_state.dark_mode = dark_mode

# Apply dynamic CSS theme
st.markdown(get_arkanetra_css(dark_mode), unsafe_allow_html=True)

# New: hide the tour container box from the UI (and its arrow-left variation)
st.markdown(
    """
    <style>
    /* Remove the .tour-container box from UI */
    .tour-container, .tour-container.arrow-left {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Data loaders ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_heat_predictions(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


@st.cache_data(ttl=3600)
def load_feature_importance(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    cols = [c.lower() for c in df.columns]
    if "feature" not in cols and len(df.columns) >= 2:
        df.columns = ["feature", "importance"] + list(df.columns[2:])
    return df


@st.cache_resource
def load_model(path: Path):
    if not path.exists():
        return None, None
    try:
        artifact = joblib.load(path)
    except Exception:
        return None, None

    if isinstance(artifact, dict):
        model = artifact.get("model") or artifact.get("estimator") or artifact.get("pipe")
        feature_names = artifact.get("feature_names") or artifact.get("features")
        if model is None:
            model = artifact
    else:
        model = artifact
        feature_names = None

    if feature_names is None and model is not None:
        try:
            feature_names = list(getattr(model, "feature_names_in_", None))
        except Exception:
            feature_names = None

    if feature_names is not None and not isinstance(feature_names, (list, tuple)):
        try:
            feature_names = list(feature_names)
        except Exception:
            feature_names = None

    return model, feature_names


@st.cache_resource
def load_shap_image(path: Path):
    if not path.exists():
        return None
    try:
        return Image.open(path)
    except Exception:
        return None


# ── Prediction helpers ─────────────────────────────────────────────────────────
def align_features(df: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
    if feature_names is None:
        return df.copy()

    df_cols_lower = {c.lower(): c for c in df.columns}
    aligned, missing = [], []
    for fname in feature_names:
        if fname in df.columns:
            aligned.append(df[fname].astype(float))
        elif fname.lower() in df_cols_lower:
            aligned.append(df[df_cols_lower[fname.lower()]].astype(float))
        else:
            fname_norm = fname.lower().replace("_", "").replace(" ", "")
            matched = None
            for c in df.columns:
                if c.lower().replace("_", "").replace(" ", "") == fname_norm:
                    matched = c
                    break
            if matched:
                aligned.append(df[matched].astype(float))
            else:
                missing.append(fname)
                aligned.append(pd.Series(np.zeros(len(df)), dtype=float))

    if missing:
        st.warning(
            f"Model expects features not present in input; filling with zeros: {missing}"
        )

    aligned_df = pd.concat(aligned, axis=1)
    aligned_df.columns = feature_names
    return aligned_df


def predict_with_model(model, feature_names, X_df: pd.DataFrame) -> np.ndarray:
    if model is None:
        raise RuntimeError("Model not loaded.")
    X_in = align_features(X_df.copy(), feature_names) if feature_names else X_df.copy()
    try:
        preds = model.predict(X_in)
    except Exception:
        preds = model.predict(X_in.values)
    return np.array(preds, dtype=float)


def safe_warn_missing(path: Path, name: str):
    st.warning(f"{name} missing at: {path}")


def build_map(
    df_map: pd.DataFrame,
    color_col: str,
    color_map: Optional[dict] = None,
    continuous: bool = False,
    hover_cols: Optional[List[str]] = None,
    title: str = "",
):
    hover = hover_cols or ["predicted_lst", "heat_class", "risk_score", "latitude", "longitude"]
    hover = {c: True for c in hover if c in df_map.columns}

    if continuous:
        fig = px.scatter_mapbox(
            df_map,
            lat="latitude",
            lon="longitude",
            color=color_col,
            color_continuous_scale=[
                [0, "#4db8c4"],
                [0.33, "#eab308"],
                [0.66, "#f97316"],
                [1, "#dc2626"],
            ],
            hover_data=hover,
            zoom=10,
            height=620,
            title=title,
        )
    else:
        fig = px.scatter_mapbox(
            df_map,
            lat="latitude",
            lon="longitude",
            color=color_col,
            color_discrete_map=color_map or HEAT_CLASS_COLORS,
            hover_data=hover,
            zoom=10,
            height=620,
            title=title,
        )

    fig.update_traces(marker=dict(size=9, opacity=0.85))
    fig.update_layout(**get_map_layout())
    return fig


# ── Load resources ───────────────────────────────────────────────────────────
df_heat_raw = load_heat_predictions(HEAT_PRED_PATH)
df_feat = load_feature_importance(FEATURE_IMPORTANCE_PATH)
shap_img = load_shap_image(SHAP_IMAGE_PATH)
model, model_feature_names = load_model(MODEL_PATH)

if not df_heat_raw.empty:
    df_heat = compute_risk_scores(df_heat_raw)
else:
    df_heat = df_heat_raw

predict_fn = (
    lambda X: predict_with_model(model, model_feature_names, X) if model else None
)

# Initialize session state for current page and onboarding tour
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Home"
if "show_tour" not in st.session_state:
    st.session_state.show_tour = True
if "tour_step" not in st.session_state:
    st.session_state.tour_step = 0

# ── Sidebar Navigation ───────────────────────────────────────────────────────
page = st.sidebar.radio(
    "Mission Navigation",
    PAGES,
    key="current_page",
    label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.caption("Bengaluru Urban Heat Observatory")
st.sidebar.caption("Landsat 8 · Sentinel-2 · RF Model")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME (Welcome / Tour Guide)
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    render_hero()

    if st.session_state.show_tour:
        step = st.session_state.tour_step
        progress_pct = int((step + 1) * 20)

        # Inject CSS to locate elements and apply pulsing glow animations
        if step == 0:
            st.markdown(
                """
                <style>
                .sidebar-brand {
                    border: 3px solid #22d3ee !important;
                    box-shadow: 0 0 15px #22d3ee, 0 0 25px rgba(34, 211, 238, 0.4) !important;
                    border-radius: 12px;
                    animation: tourPulse 1.5s infinite alternate !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            container_class = 'tour-container arrow-left'
        elif step == 1:
            st.markdown(
                """
                <style>
                section[data-testid="stSidebar"] [data-testid="stRadio"] {
                    border: 3px solid #22d3ee !important;
                    box-shadow: 0 0 15px #22d3ee, 0 0 25px rgba(34, 211, 238, 0.4) !important;
                    border-radius: 10px;
                    padding: 10px !important;
                    animation: tourPulse 1.5s infinite alternate !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            container_class = 'tour-container arrow-left'
        elif step == 2:
            st.markdown(
                """
                <style>
                section[data-testid="stSidebar"] .stCheckbox {
                    border: 3px solid #fb923c !important;
                    box-shadow: 0 0 15px #fb923c, 0 0 25px rgba(251, 146, 60, 0.4) !important;
                    border-radius: 10px;
                    padding: 10px !important;
                    animation: tourPulse 1.5s infinite alternate !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            container_class = 'tour-container arrow-left'
        elif step == 3:
            st.markdown(
                """
                <style>
                .hero-section {
                    border: 3px solid #22d3ee !important;
                    box-shadow: 0 0 20px #22d3ee, 0 0 30px rgba(34, 211, 238, 0.3) !important;
                    animation: tourPulse 1.5s infinite alternate !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            container_class = 'tour-container'
        else:
            container_class = 'tour-container'

        st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)

        if step == 0:
            st.markdown(
                """
                <h3>🛰 Step 1: Welcome to ARKANETRA</h3>
                <p>Welcome to <b>ARKANETRA (अर्कनेत्र)</b>, the Physics-Informed Urban Heat Intelligence Platform.</p>
                <p>Look at the <b>pulsing cyan highlight</b> at the top of the sidebar. The ARKANETRA brand logo features active rotating and color-shifting animations representing solar observatory inputs!</p>
                """,
                unsafe_allow_html=True
            )
        elif step == 1:
            st.markdown(
                """
                <h3>🧭 Step 2: Mission Navigation</h3>
                <p>Look at the <b>pulsing cyan highlight</b> in the sidebar.</p>
                <p>This radio selection control serves as the navigation hub, allowing you to switch between all platform modules: Heat Monitor, Heat Drivers, Simulator, Optimizer, and Priority Zones.</p>
                """,
                unsafe_allow_html=True
            )
        elif step == 2:
            st.markdown(
                """
                <h3>🌙 Step 3: Theme Switcher</h3>
                <p>Look at the <b>pulsing orange highlight</b> in the sidebar.</p>
                <p>This is the <b>Dark Mode Toggle</b> widget. Flip it to instantly switch the user interface between Dark theme (ideal for cartography and heat maps) and Light theme.</p>
                """,
                unsafe_allow_html=True
            )
        elif step == 3:
            st.markdown(
                """
                <h3>🔥 Step 4: Mission Briefing</h3>
                <p>Look at the <b>pulsing cyan highlight</b> in the main dashboard area.</p>
                <p>This is the Welcome Hero banner. It displays key operational statistics, sensors utilized (Landsat 8, Sentinel-2), and the Explainable Random Forest model in use.</p>
                """,
                unsafe_allow_html=True
            )
        elif step == 4:
            st.markdown(
                """
                <h3>📍 Step 5: Tour Finished!</h3>
                <p>You have finished the briefing tour. You can restart the tour at any time from the Home dashboard panel.</p>
                <p>Click <b>Finish</b> to explore the platform modules!</p>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            f"""
            <div class="tour-progress-bar">
                <div class="tour-progress-fill" style="width: {progress_pct}%"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        b_col1, b_col2, b_col3 = st.columns([1, 2, 1])
        with b_col1:
            if step > 0:
                if st.button("⬅ Back", use_container_width=True):
                    st.session_state.tour_step -= 1
                    st.rerun()
        with b_col3:
            if step < 4:
                if st.button("Next ➡", use_container_width=True):
                    st.session_state.tour_step += 1
                    st.rerun()
            else:
                if st.button("Finish 🎉", use_container_width=True):
                    st.session_state.show_tour = False
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Skip tour & explore platform ➔"):
            st.session_state.show_tour = False
            st.rerun()
    else:
        st.markdown(
            """
            <div class="section-header"><span>Mission Control</span> Modules</div>
            <div class="home-grid">
                <div class="home-card">
                    <h4>🌍 Heat Monitor</h4>
                    <p>Observe real-time hotspot distributions, observe key metrics, and review physics-informed risk models across Bengaluru.</p>
                </div>
                <div class="home-card">
                    <h4>📊 Heat Drivers</h4>
                    <p>Understand the physical drivers of urban heating using explainable AI feature importances and SHAP impact analyses.</p>
                </div>
                <div class="home-card">
                    <h4>🌱 Cooling Simulator</h4>
                    <p>Simulate urban canopy and albedo expansion and instantly calculate average and peak cooling potential.</p>
                </div>
                <div class="home-card">
                    <h4>🎯 Optimizer</h4>
                    <p>Pinpoint the most cost-effective and highest-performing cooling strategies tailored to each specific hotspot.</p>
                </div>
                <div class="home-card">
                    <h4>📍 Priority Zones</h4>
                    <p>Discover high-priority zones ranked by risk scores to design immediate cooling interventions.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("---")
        if st.button("Launch Platform Mission Control 🚀", use_container_width=True):
            st.session_state.current_page = "🌍 Heat Monitor"
            st.rerun()
            
        if st.button("Restart onboarding tour 🔁"):
            st.session_state.show_tour = True
            st.session_state.tour_step = 0
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HEAT MONITOR (Mission Control)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌍 Heat Monitor":
    render_hero()

    if df_heat.empty:
        safe_warn_missing(HEAT_PRED_PATH, "Heat predictions file")
    else:
        avg_temp = float(df_heat["predicted_lst"].mean())
        max_temp = float(df_heat["predicted_lst"].max())
        extreme_count = int((df_heat["heat_class"] == "Extreme").sum())
        avg_risk = float(df_heat["risk_score"].mean())
        max_risk = float(df_heat["risk_score"].max())

        cooling_potential = 0.0
        if model is not None:
            extreme_df = df_heat[df_heat["heat_class"] == "Extreme"]
            if not extreme_df.empty:
                avail = [f for f in SPECTRAL_FEATURES if f in extreme_df.columns]
                cooling_potential = estimate_avg_cooling_potential(
                    extreme_df, predict_fn, avail, sample_n=min(100, len(extreme_df))
                )

        section_header("Overview", "Mission")
        k1, k2, k3, k4 = st.columns(4)
        mission_card(k1, "🛰", "Mission Status", "ACTIVE", "cyan", "All systems nominal")
        mission_card(k2, "🔥", "Hotspot Count", f"{extreme_count}", "red", "Extreme class")
        mission_card(
            k3, "❄", "Avg Cooling Potential",
            f"{cooling_potential:.2f}°C", "cyan", "Best-case intervention"
        )
        mission_card(k4, "⚠", "Risk Index", f"{avg_risk:.1f}", "orange", f"Peak: {max_risk:.1f}")

        section_header("Intelligence", "Geospatial")
        df_map = df_heat.dropna(subset=["latitude", "longitude"]).copy()
        df_map["latitude"] = pd.to_numeric(df_map["latitude"], errors="coerce")
        df_map["longitude"] = pd.to_numeric(df_map["longitude"], errors="coerce")
        df_map = df_map.dropna(subset=["latitude", "longitude"])

        if df_map.empty:
            st.info("No geolocated points available to render map.")
        else:
            fig_map = build_map(
                df_map, "heat_class",
                color_map=HEAT_CLASS_COLORS,
                title="Urban Heat Hotspot Map — Bengaluru",
            )
            st.plotly_chart(fig_map, use_container_width=True)

        section_header("Risk", "Physics-Informed")
        st.caption(
            "Combines AI predictions with physically meaningful heat drivers. "
            "Risk Score = 0.40×NDBI + 0.25×ALBEDO − 0.20×NDVI − 0.10×EVI − 0.05×MNDWI (normalized 0–100)."
        )

        g1, g2, g3, g4 = st.columns([2, 1, 1, 1])
        with g1:
            st.plotly_chart(risk_gauge(avg_risk), use_container_width=True)
        mission_card(g2, "📊", "Average Risk Score", f"{avg_risk:.1f}", "orange")
        mission_card(g3, "🔺", "Highest Risk Score", f"{max_risk:.1f}", "red")
        mission_card(g4, "🌡", "Max Temperature", f"{max_temp:.1f}°C", "navy")

        if not df_map.empty:
            fig_risk_map = build_map(
                df_map, "risk_score", continuous=True,
                title="Urban Heat Risk Score Map",
            )
            st.plotly_chart(fig_risk_map, use_container_width=True)

        section_header("Summary", "Mission KPIs")
        k5, k6, k7 = st.columns(3)
        mission_card(k5, "🌡", "Average Temperature", f"{avg_temp:.2f}°C", "navy")
        mission_card(k6, "📍", "Total Observation Points", f"{len(df_heat)}", "cyan")
        mission_card(k7, "🔴", "Extreme Hotspots", f"{extreme_count}", "red")

        section_header("Statistics", "Hotspot")
        stats = (
            df_heat.groupby("heat_class")
            .agg(count=("predicted_lst", "count"), mean_pred=("predicted_lst", "mean"),
                 max_pred=("predicted_lst", "max"), mean_risk=("risk_score", "mean"))
            .reset_index()
        )
        st.dataframe(
            stats.style.format({
                "mean_pred": "{:.2f}", "max_pred": "{:.2f}", "mean_risk": "{:.1f}",
            }),
            use_container_width=True,
        )

        section_header("Locations", "Top 10 Hottest")
        top10 = df_heat.sort_values("predicted_lst", ascending=False).head(10)
        display_cols = [c for c in [
            "predicted_lst", "heat_class", "risk_score", "latitude", "longitude",
            "NDVI", "NDBI", "ALBEDO",
        ] if c in top10.columns]
        st.dataframe(
            top10[display_cols].reset_index(drop=True).style.format({
                "predicted_lst": "{:.2f}", "risk_score": "{:.1f}",
                "latitude": "{:.4f}", "longitude": "{:.4f}",
            }),
            use_container_width=True,
        )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HEAT DRIVERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Heat Drivers":
    page_header("Heat Drivers", "Explainable AI analysis of urban heating factors")

    col1, col2 = st.columns([1, 1])
    with col1:
        section_header("Importance", "Feature")
        if df_feat.empty:
            safe_warn_missing(FEATURE_IMPORTANCE_PATH, "Feature importance CSV")
        else:
            if "importance" in df_feat.columns and "feature" in df_feat.columns:
                df_plot = df_feat.sort_values("importance", ascending=True).tail(50)
                scale = [[0, "#22d3ee"], [0.5, "#3b82f6"], [1, "#fb923c"]] if dark_mode else [[0, "#4db8c4"], [0.5, "#1a3a5c"], [1, "#e85d04"]]
                fig = px.bar(
                    df_plot, x="importance", y="feature", orientation="h",
                    color="importance",
                    color_continuous_scale=scale,
                    title="Model Feature Importance",
                )
                fig.update_layout(
                    height=500, margin=dict(l=160),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False,
                    font=dict(family="Inter, sans-serif", color="#f8fafc" if dark_mode else "#0a1628"),
                )
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Feature importance file missing expected columns.")

    with col2:
        section_header("Summary", "SHAP")
        if shap_img is None:
            safe_warn_missing(SHAP_IMAGE_PATH, "SHAP summary image")
        else:
            st.image(shap_img, caption="SHAP Feature Impact Summary", use_container_width=True)

    section_header("Insights", "Automated")
    for insight in generate_driver_insights(df_feat):
        insight_card(insight)

    with st.expander("Methodology & Physics Interpretation"):
        st.markdown(
            """
            **Feature importance** is derived from Random Forest explainability (SHAP values).

            | Index | Physical Meaning | Heat Effect |
            |-------|-----------------|-------------|
            | **NDBI** | Built-up area intensity | Increases urban heat |
            | **NDVI** | Vegetation cover | Cooling influence |
            | **EVI** | Enhanced vegetation | Cooling influence |
            | **ALBEDO** | Surface reflectance | Higher albedo reduces absorption |
            | **MNDWI** | Water/moisture presence | Cooling influence |

            Interpretations combine AI model outputs with physically meaningful remote sensing indices
            derived from Landsat 8 and Sentinel-2 via Google Earth Engine.
            """
        )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: COOLING SIMULATOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌱 Cooling Simulator":
    page_header("Cooling Simulator", "Test urban cooling intervention scenarios with the trained ML model")

    if df_heat.empty:
        safe_warn_missing(HEAT_PRED_PATH, "Heat predictions file")
        st.stop()

    if model is None:
        safe_warn_missing(MODEL_PATH, "Trained model")
        st.stop()

    available_features = [f for f in SPECTRAL_FEATURES if f in df_heat.columns]
    if not available_features:
        st.error("Model features not present in dataset. Cannot run simulation.")
        st.stop()

    st.markdown("Adjust intervention sliders and run simulation on a sample of the dataset.")
    col_sl1, col_sl2, col_sl3 = st.columns(3)
    with col_sl1:
        tree_cover = st.slider("Tree Cover Increase (%)", 0, 50, 10)
    with col_sl2:
        cool_roof = st.slider("Cool Roof Adoption (%)", 0, 50, 10)
    with col_sl3:
        sample_size = st.slider(
            "Sample size", 100, min(5000, len(df_heat)),
            min(1000, len(df_heat)),
        )

    df_sim = df_heat.sample(n=sample_size, random_state=42).reset_index(drop=True)

    geo_cols = [c for c in ["longitude", "latitude"] if c in df_sim.columns]
    feature_cols = available_features + geo_cols
    X_base = df_sim[feature_cols].astype(float).copy()

    delta_ndvi = (tree_cover / 100.0) * 0.2
    delta_evi = (tree_cover / 100.0) * 0.2
    delta_albedo = (cool_roof / 100.0) * 0.1

    X_new = X_base.copy()
    if "NDVI" in X_new.columns:
        X_new["NDVI"] = np.clip(X_new["NDVI"] + delta_ndvi, -1.0, 1.0)
    if "EVI" in X_new.columns:
        X_new["EVI"] = np.clip(X_new["EVI"] + delta_evi, -1.0, 1.0)
    if "ALBEDO" in X_new.columns:
        X_new["ALBEDO"] = np.clip(X_new["ALBEDO"] + delta_albedo, 0.0, 1.0)

    try:
        pred_base = predict_with_model(model, model_feature_names, X_base)
        pred_new = predict_with_model(model, model_feature_names, X_new)
    except Exception as exc:
        st.error(f"Prediction failed: {exc}")
        pred_base = np.zeros(len(X_base))
        pred_new = np.zeros(len(X_new))

    delta = pred_base - pred_new
    avg_cooling = float(np.mean(delta))
    max_cooling = float(np.max(delta))
    percent_improved = float(100.0 * np.sum(delta > 0) / len(delta))

    section_header("Results", "Simulation")
    c1, c2, c3 = st.columns(3)
    mission_card(c1, "❄", "Average Cooling", f"{avg_cooling:.3f}°C", "cyan")
    mission_card(c2, "🏆", "Maximum Cooling", f"{max_cooling:.3f}°C", "orange")
    mission_card(c3, "📈", "Points Improved", f"{percent_improved:.1f}%", "navy")

    section_header("Distribution", "Temperature")
    df_plot = pd.DataFrame({"before": pred_base, "after": pred_new})
    fig_box = go.Figure()
    fig_box.add_trace(go.Box(y=df_plot["before"], name="Baseline", marker_color="#ef4444" if dark_mode else "#dc2626",
                             fillcolor="rgba(239,68,68,0.15)" if dark_mode else "rgba(220,38,38,0.15)"))
    fig_box.add_trace(go.Box(y=df_plot["after"], name="Intervention", marker_color="#22d3ee" if dark_mode else "#4db8c4",
                             fillcolor="rgba(34,211,238,0.15)" if dark_mode else "rgba(77,184,196,0.15)"))
    fig_box.update_layout(
        height=420, yaxis_title="Predicted LST (°C)",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#f8fafc" if dark_mode else "#0a1628"),
    )
    st.plotly_chart(fig_box, use_container_width=True)

    section_header("Distribution", "Spatial Cooling")
    df_map_sim = df_sim.copy()
    df_map_sim["delta"] = delta
    df_map_sim = df_map_sim.dropna(subset=["latitude", "longitude"])
    if not df_map_sim.empty:
        fig_map2 = px.scatter_mapbox(
            df_map_sim, lat="latitude", lon="longitude", color="delta",
            color_continuous_scale=[[0, "#dc2626"], [0.5, "#eab308"], [1, "#4db8c4"]],
            hover_data={c: True for c in ["predicted_lst", "delta", "risk_score", "latitude", "longitude"]
                        if c in df_map_sim.columns},
            zoom=10, height=620, title="Cooling Effect Spatial Distribution",
        )
        fig_map2.update_traces(marker=dict(size=9, opacity=0.85))
        fig_map2.update_layout(**get_map_layout())
        st.plotly_chart(fig_map2, use_container_width=True)
    else:
        st.info("Insufficient geolocation data to display cooling distribution.")

    if st.button("Save intervention results to outputs/intervention_results.csv"):
        out_df = df_sim.copy()
        out_df["pred_base"] = pred_base
        out_df["pred_intervention"] = pred_new
        out_df["delta_pred"] = delta
        OUT_INTERVENTION_CSV.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(OUT_INTERVENTION_CSV, index=False)
        st.success(f"Saved to {OUT_INTERVENTION_CSV}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OPTIMIZER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Optimizer":
    page_header(
        "Cooling Strategy Optimizer",
        "Test intervention scenarios per hotspot and select maximum cooling strategy",
    )

    if df_heat.empty:
        safe_warn_missing(HEAT_PRED_PATH, "Heat predictions file")
        st.stop()
    if model is None:
        safe_warn_missing(MODEL_PATH, "Trained model")
        st.stop()

    available_features = [f for f in SPECTRAL_FEATURES if f in df_heat.columns]
    heat_filter = st.selectbox(
        "Hotspot population",
        ["Extreme hotspots", "High + Extreme hotspots", "All hotspots"],
        index=0,
    )
    if heat_filter == "Extreme hotspots":
        df_target = df_heat[df_heat["heat_class"] == "Extreme"].copy()
    elif heat_filter == "High + Extreme hotspots":
        df_target = df_heat[df_heat["heat_class"].isin(["Extreme", "High"])].copy()
    else:
        df_target = df_heat.copy()

    max_hotspots = st.slider("Number of hotspots to optimize", 10, min(200, len(df_target)), 50)
    df_target = df_target.head(max_hotspots)

    if df_target.empty:
        st.info("No hotspots available for the selected filter.")
        st.stop()

    st.markdown(
        """
        **Intervention Scenarios Tested:**
        - **A:** +10% NDVI (tree cover)
        - **B:** +20% NDVI
        - **C:** +10% ALBEDO (cool roofs)
        - **D:** +20% ALBEDO
        - **E:** Combined (+10% NDVI + +10% ALBEDO)
        """
    )

    with st.spinner("Running optimization across intervention scenarios…"):
        opt_results = run_optimizer(df_target, predict_fn, available_features)

    section_header("Board", "Optimization Results")
    display_df = opt_results[[
        "Hotspot ID", "Current Temperature", "Best Strategy",
        "Expected Cooling (°C)", "Priority Rank",
    ]]
    st.dataframe(
        display_df.style.format({
            "Current Temperature": "{:.2f}",
            "Expected Cooling (°C)": "{:.3f}",
        }).background_gradient(subset=["Expected Cooling (°C)"], cmap="YlGn"),
        use_container_width=True,
        height=400,
    )

    section_header("", "Cooling Leaderboard")
    top_n = min(10, len(opt_results))
    max_cool = float(opt_results["Expected Cooling (°C)"].max()) if not opt_results.empty else 1.0
    for _, row in opt_results.head(top_n).iterrows():
        leaderboard_bar(
            int(row["Priority Rank"]),
            f"Hotspot #{int(row['Hotspot ID'])} — {row['Best Strategy']}",
            float(row["Expected Cooling (°C)"]),
            max_cool,
        )

    section_header("Map", "Optimized Cooling Potential")
    opt_map = opt_results.dropna(subset=["latitude", "longitude"]).copy()
    if not opt_map.empty:
        fig_opt = px.scatter_mapbox(
            opt_map, lat="latitude", lon="longitude",
            color="Expected Cooling (°C)",
            size="Expected Cooling (°C)",
            size_max=18,
            color_continuous_scale=[[0, "#eab308"], [0.5, "#4db8c4"], [1, "#0f2744"]],
            hover_data={c: True for c in [
                "Hotspot ID", "Current Temperature", "Best Strategy",
                "Expected Cooling (°C)", "Priority Rank",
            ]},
            zoom=10, height=620, title="Best Strategy Cooling Potential",
        )
        fig_opt.update_traces(marker=dict(opacity=0.85))
        fig_opt.update_layout(**get_map_layout())
        st.plotly_chart(fig_opt, use_container_width=True)

    csv_bytes = opt_results.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download optimization results CSV",
        data=csv_bytes,
        file_name="cooling_optimization_results.csv",
        mime="text/csv",
    )

    section_header("Recommendations", "Legacy Intervention")
    with st.expander("View rule-based recommendations for Extreme hotspots"):
        df_extreme = df_heat[df_heat["heat_class"] == "Extreme"].copy()
        if not df_extreme.empty:
            medians = {
                "NDBI": float(df_extreme["NDBI"].median()) if "NDBI" in df_extreme.columns else 0,
                "NDVI": float(df_extreme["NDVI"].median()) if "NDVI" in df_extreme.columns else 0,
                "MNDWI": float(df_extreme["MNDWI"].median()) if "MNDWI" in df_extreme.columns else 0,
            }
            recs = [generate_recommendation(row, medians) for _, row in df_extreme.iterrows()]
            df_extreme = df_extreme.reset_index(drop=True)
            df_extreme["recommendations"] = recs
            df_extreme["hotspot_id"] = df_extreme.index + 1
            preds = df_extreme["predicted_lst"].astype(float)
            min_p, max_p = preds.min(), preds.max()
            if max_p - min_p == 0:
                df_extreme["priority_score"] = 50
            else:
                df_extreme["priority_score"] = (
                    (preds - min_p) / (max_p - min_p) * 99 + 1
                ).round(0).astype(int)
            rec_cols = ["hotspot_id", "predicted_lst", "latitude", "longitude",
                        "recommendations", "priority_score", "risk_score"]
            rec_cols = [c for c in rec_cols if c in df_extreme.columns]
            st.dataframe(
                df_extreme[rec_cols].sort_values("priority_score", ascending=False),
                use_container_width=True,
            )
            rec_csv = df_extreme[rec_cols].to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download recommendations CSV",
                data=rec_csv,
                file_name="intervention_recommendations.csv",
                mime="text/csv",
            )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PRIORITY ZONES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📍 Priority Zones":
    page_header(
        "Spatial Priority Zones",
        "Ranked intervention zones based on predicted temperature and physics-informed risk score",
    )

    if df_heat.empty:
        safe_warn_missing(HEAT_PRED_PATH, "Heat predictions file")
        st.stop()

    zones_df = assign_priority_zones(df_heat)
    if zones_df.empty:
        st.info("No Extreme or High hotspots available for priority zoning.")
        st.stop()

    medians = {
        "NDBI": float(zones_df["NDBI"].median()) if "NDBI" in zones_df.columns else 0,
        "NDVI": float(zones_df["NDVI"].median()) if "NDVI" in zones_df.columns else 0,
        "MNDWI": float(zones_df["MNDWI"].median()) if "MNDWI" in zones_df.columns else 0,
    }
    zones_df["Recommended Intervention"] = [
        generate_recommendation(row, medians) for _, row in zones_df.iterrows()
    ]

    z1 = int((zones_df["priority_zone"] == "Priority Zone 1").sum())
    z2 = int((zones_df["priority_zone"] == "Priority Zone 2").sum())
    z3 = int((zones_df["priority_zone"] == "Priority Zone 3").sum())

    section_header("Overview", "Zone")
    c1, c2, c3 = st.columns(3)
    mission_card(c1, "🔴", "Priority Zone 1", f"{z1} locations", "red", "Immediate action")
    mission_card(c2, "🟠", "Priority Zone 2", f"{z2} locations", "orange", "High priority")
    mission_card(c3, "🟡", "Priority Zone 3", f"{z3} locations", "orange", "Moderate priority")

    section_header("Map", "Priority Zone")
    zones_map = zones_df.dropna(subset=["latitude", "longitude"]).copy()
    if not zones_map.empty:
        fig_zones = px.scatter_mapbox(
            zones_map, lat="latitude", lon="longitude",
            color="priority_zone",
            color_discrete_map=ZONE_COLORS,
            hover_data={c: True for c in [
                "predicted_lst", "risk_score", "heat_class",
                "Recommended Intervention", "latitude", "longitude",
            ] if c in zones_map.columns},
            zoom=10, height=650, title="Spatial Priority Zones — Intervention Targeting",
        )
        fig_zones.update_traces(marker=dict(size=11, opacity=0.9))
        fig_zones.update_layout(**get_map_layout())
        st.plotly_chart(fig_zones, use_container_width=True)

    for zone_name, badge_class, color in [
        ("Priority Zone 1", "zone-badge-1", "#dc2626"),
        ("Priority Zone 2", "zone-badge-2", "#ea580c"),
        ("Priority Zone 3", "zone-badge-3", "#ca8a04"),
    ]:
        zone_subset = zones_df[zones_df["priority_zone"] == zone_name]
        if zone_subset.empty:
            continue
        st.markdown(
            f'<div class="section-header"><span class="{badge_class}">{zone_name}</span> '
            f'— {len(zone_subset)} locations</div>',
            unsafe_allow_html=True,
        )
        show_cols = [c for c in [
            "latitude", "longitude", "predicted_lst", "risk_score",
            "heat_class", "Recommended Intervention",
        ] if c in zone_subset.columns]
        st.dataframe(
            zone_subset[show_cols].head(15).style.format({
                "predicted_lst": "{:.2f}", "risk_score": "{:.1f}",
                "latitude": "{:.4f}", "longitude": "{:.4f}",
            }),
            use_container_width=True,
        )

    csv_bytes = zones_df[[c for c in [
        "priority_zone", "latitude", "longitude", "predicted_lst",
        "risk_score", "heat_class", "Recommended Intervention",
    ] if c in zones_df.columns]].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download priority zones CSV",
        data=csv_bytes,
        file_name="priority_zones.csv",
        mime="text/csv",
    )

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
render_footer()
