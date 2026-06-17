"""Reusable ARKANETRA UI components."""

import streamlit as st
import plotly.graph_objects as go


def render_sidebar_brand():
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="logo-mark">☀</div>
            <div class="brand-name">ARKANETRA</div>
            <div class="brand-sub">अर्कनेत्र · The Eye of the Sun</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
        <div class="hero-section">
            <div class="hero-content">
                <h1 class="hero-title">ARKANETRA</h1>
                <div class="hero-devanagari">अर्कनेत्र</div>
                <p class="hero-tagline">Physics-Informed Urban Heat Intelligence Platform</p>
                <div class="hero-badge">
                    Powered by Landsat, Sentinel-2, Earth Engine and Explainable AI
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mission_card(col, icon: str, label: str, value: str, accent: str = "cyan", delta: str = ""):
    delta_html = f'<div class="card-delta">{delta}</div>' if delta else ""
    with col:
        st.markdown(
            f"""
            <div class="mission-card {accent}-accent">
                <div class="card-icon">{icon}</div>
                <div class="card-label">{label}</div>
                <div class="card-value">{value}</div>
                {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def section_header(title: str, highlight: str = ""):
    if highlight:
        st.markdown(
            f'<div class="section-header"><span>{highlight}</span> {title}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def insight_card(text: str, label: str = "Observation"):
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-label">{label}</div>
            <p>{text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
        <div class="arkanetra-footer">
            <div class="footer-brand">ARKANETRA</div>
            <div class="footer-sub">Bharatiya Antariksh Hackathon 2026 -Built by Unnathi_CS</div>
            <div class="footer-tag">Urban Heat Intelligence &amp; Cooling Optimization Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_gauge(score: float, title: str = "Urban Heat Risk Index"):
    dark_mode = st.session_state.get("dark_mode", True)
    text_color = "#f8fafc" if dark_mode else "#0a1628"
    title_color = "#94a3b8" if dark_mode else "#5a6f82"
    bg_color = "#1e293b" if dark_mode else "#f1f5f9"
    
    # threshold bar and other steps styled per theme
    step1_color = "rgba(34, 211, 238, 0.2)" if dark_mode else "rgba(77,184,196,0.25)"  # cyan
    step2_color = "rgba(251, 146, 60, 0.2)" if dark_mode else "rgba(244,140,6,0.25)"   # orange
    step3_color = "rgba(239, 68, 68, 0.2)" if dark_mode else "rgba(220,38,38,0.25)"    # red
    bar_color = "#fb923c" if dark_mode else "#e85d04"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "", "font": {"size": 36, "color": text_color}},
            title={"text": title, "font": {"size": 14, "color": title_color}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#94a3b8", "tickwidth": 1},
                "bar": {"color": bar_color, "thickness": 0.25},
                "bgcolor": bg_color,
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 33], "color": step1_color},
                    {"range": [33, 66], "color": step2_color},
                    {"range": [66, 100], "color": step3_color},
                ],
                "threshold": {
                    "line": {"color": "#dc2626" if not dark_mode else "#ef4444", "width": 3},
                    "thickness": 0.8,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=30, r=30, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def leaderboard_bar(rank: int, label: str, value: float, max_value: float):
    pct = (value / max_value * 100) if max_value > 0 else 0
    dark_mode = st.session_state.get("dark_mode", True)
    label_color = "#cbd5e1" if dark_mode else "#334155"
    val_color = "#f8fafc" if dark_mode else "#0a1628"
    st.markdown(
        f"""
        <div class="leaderboard-row">
            <div class="leaderboard-rank">#{rank}</div>
            <div style="flex:0 0 120px; font-size:0.85rem; color:{label_color} !important;">{label}</div>
            <div class="leaderboard-bar">
                <div class="leaderboard-bar-fill" style="width:{pct:.0f}%"></div>
            </div>
            <div style="font-weight:600; color:{val_color} !important; min-width:60px; text-align:right;">
                {value:.2f}°C
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


HEAT_CLASS_COLORS = {
    "Very Low": "#3b82f6",
    "Low": "#22c55e",
    "Medium": "#eab308",
    "High": "#f97316",
    "Extreme": "#dc2626",
}

ZONE_COLORS = {
    "Priority Zone 1": "#dc2626",
    "Priority Zone 2": "#ea580c",
    "Priority Zone 3": "#ca8a04",
}

# Static fallback layout dictionary
MAP_LAYOUT = dict(
    mapbox_style="carto-positron",
    margin=dict(r=0, t=30, l=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#0a1628"),
)


def get_map_layout() -> dict:
    try:
        dark_mode = st.session_state.get("dark_mode", True)
    except Exception:
        dark_mode = True
    
    style = "carto-darkmatter" if dark_mode else "carto-positron"
    text_color = "#f8fafc" if dark_mode else "#0a1628"
    
    return dict(
        mapbox_style=style,
        margin=dict(r=0, t=30, l=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=text_color),
    )
