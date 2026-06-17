"""ARKANETRA mission-control theme — ISRO-inspired geospatial UI."""

def get_arkanetra_css(dark_mode: bool = True) -> str:
    if dark_mode:
        # Dark Theme variables
        deep = "#f8fafc"  # Off-white / light text in dark mode
        navy = "#0a121e"  # Deep space slate-navy background element
        blue = "#1e293b"  # Border and panel colors
        cyan = "#22d3ee"  # Glowing cyan accent
        cyan_muted = "#94a3b8"  # Slate-muted text
        orange = "#fb923c"  # Vivid orange accent
        orange_light = "#fdba74"  # Lighter orange for gradients
        white = "#f8fafc"  # Pure light text
        surface = "#1f2937"  # Slate-800 surfaces
        border = "rgba(77, 184, 196, 0.28)"  # More visible borders for dark mode
        shadow = "0 4px 30px rgba(0, 0, 0, 0.6)"
        glass = "rgba(17, 24, 39, 0.85)"  # Semitransparent panels
        app_bg = "linear-gradient(165deg, #090f1d 0%, #0d1726 45%, #050912 100%)"
        sidebar_bg = "linear-gradient(180deg, #050a12 0%, #0c1420 100%)"
        sidebar_text = "#ecf0f4"
        sidebar_hover = "rgba(77, 184, 196, 0.15)"
        sidebar_active = "rgba(77, 184, 196, 0.25)"
        card_label = "#94a3b8"
        insight_p = "#cbd5e1"
        logo_gradient = "linear-gradient(90deg, #fb923c, #ffffff, #22d3ee)"
        logo_sub = "#22d3ee"
    else:
        # Light Theme variables
        deep = "#0a1628"  # Dark navy text in light mode
        navy = "#0f2744"
        blue = "#1a3a5c"
        cyan = "#4db8c4"
        cyan_muted = "#7ec8d4"
        orange = "#e85d04"
        orange_light = "#f48c06"
        white = "#ffffff"
        surface = "#ffffff"  # White surfaces
        border = "rgba(77, 184, 196, 0.18)"
        shadow = "0 4px 24px rgba(10, 22, 40, 0.08)"
        glass = "rgba(255, 255, 255, 0.82)"
        app_bg = "linear-gradient(165deg, #eef4f8 0%, #f8fafc 45%, #e8f0f6 100%)"
        # KEEP SIDEBAR DARK NAVY in light mode for professional contrast and visibility!
        sidebar_bg = "linear-gradient(180deg, #0a1628 0%, #0f2744 100%)"
        sidebar_text = "#ecf0f4"
        sidebar_hover = "rgba(255, 255, 255, 0.06)"
        sidebar_active = "rgba(77, 184, 196, 0.18)"
        card_label = "#5a6f82"
        insight_p = "#334155"
        logo_gradient = "linear-gradient(90deg, #e85d04, #ffffff, #4db8c4)"
        logo_sub = "#4db8c4"

    return f"""
<link href="https://fonts.googleapis.com/css2?family=Yatra+One&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {{
    --arkanetra-deep: {deep};
    --arkanetra-navy: {navy};
    --arkanetra-blue: {blue};
    --arkanetra-cyan: {cyan};
    --arkanetra-cyan-muted: {cyan_muted};
    --arkanetra-orange: {orange};
    --arkanetra-orange-light: {orange_light};
    --arkanetra-white: {white};
    --arkanetra-surface: {surface};
    --arkanetra-border: {border};
    --arkanetra-shadow: {shadow};
    --arkanetra-glass: {glass};
}}

/* Hide default Streamlit chrome */
#MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; }}
.block-container {{ padding-top: 1.5rem; max-width: 1400px; }}

.stApp {{
    background: {app_bg};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--arkanetra-deep);
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {sidebar_bg};
    border-right: 1px solid var(--arkanetra-border);
}}
section[data-testid="stSidebar"] * {{
    color: {sidebar_text} !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
    background: {sidebar_hover};
    border-radius: 10px;
    padding: 10px 14px;
    margin: 4px 0;
    border: 1px solid transparent;
    transition: all 0.2s ease;
    font-size: 0.92rem;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    background: {sidebar_active};
    border-color: var(--arkanetra-border);
}}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-baseweb="radio"] {{
    padding: 0;
}}

/* Explicit sidebar text override for headers, markdown, labels, and text to be styled as #ecf0f4 */
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3, 
section[data-testid="stSidebar"] h4, 
section[data-testid="stSidebar"] h5, 
section[data-testid="stSidebar"] h6, 
section[data-testid="stSidebar"] p, 
section[data-testid="stSidebar"] span, 
section[data-testid="stSidebar"] label, 
section[data-testid="stSidebar"] .stMarkdown {{
    color: #ecf0f4 !important;
}}

/* Onboarding Tour Card and Home Grid */
.tour-container {{
    background: var(--arkanetra-glass);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 2px solid var(--arkanetra-orange);
    border-radius: 20px;
    padding: 2.2rem;
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.4);
    z-index: 999999;
    max-width: 500px;
    width: 90%;
    animation: tourPop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}}
.tour-container.centered-modal {{
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}}
.tour-container.sidebar-modal {{
    position: fixed;
    top: 220px;
    left: 360px;
}}
.tour-container.sidebar-modal::after {{
    content: '';
    position: absolute;
    top: 50%;
    left: -20px;
    transform: translateY(-50%);
    border-width: 10px;
    border-style: solid;
    border-color: transparent var(--arkanetra-orange) transparent transparent;
}}
.tour-container h3 {{
    margin-top: 0;
    color: var(--arkanetra-orange) !important;
    font-family: 'Yatra One', cursive;
}}
.tour-progress-bar {{
    height: 6px;
    background: rgba(77, 184, 196, 0.2);
    border-radius: 3px;
    margin: 1.2rem 0;
    overflow: hidden;
}}
.tour-progress-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--arkanetra-orange), var(--arkanetra-cyan));
    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}}
.home-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-top: 1.5rem;
}}
.home-card {{
    background: var(--arkanetra-glass);
    border: 1px solid var(--arkanetra-border);
    border-radius: 16px;
    padding: 1.8rem;
    box-shadow: var(--arkanetra-shadow);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}}
.home-card h4 {{
    margin-top: 0;
    font-family: 'Yatra One', cursive;
    color: var(--arkanetra-deep) !important;
}}
.home-card p {{
    font-size: 0.9rem;
    color: var(--arkanetra-cyan-muted) !important;
    line-height: 1.5;
    margin-bottom: 0;
}}
.home-card:hover {{
    transform: translateY(-5px);
    border-color: var(--arkanetra-orange);
    box-shadow: 0 12px 30px rgba(232, 93, 4, 0.15);
}}
.home-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 4px;
    background: linear-gradient(90deg, var(--arkanetra-cyan), var(--arkanetra-orange));
    opacity: 0;
    transition: opacity 0.3s ease;
}}
.home-card:hover::before {{
    opacity: 1;
}}

/* Logo animations and styling */
@keyframes logo-spin-pulse {{
    0% {{
        transform: rotate(0deg) scale(1);
        box-shadow: 0 0 15px rgba(232, 93, 4, 0.4);
    }}
    50% {{
        transform: rotate(180deg) scale(1.08);
        box-shadow: 0 0 25px rgba(77, 184, 196, 0.8);
    }}
    100% {{
        transform: rotate(360deg) scale(1);
        box-shadow: 0 0 15px rgba(232, 93, 4, 0.4);
    }}
}}
@keyframes gradient-shift {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}
@keyframes glow-pulse {{
    0% {{ text-shadow: 0 0 5px rgba(77, 184, 196, 0.2); }}
    50% {{ text-shadow: 0 0 15px var(--arkanetra-cyan); }}
    100% {{ text-shadow: 0 0 5px rgba(77, 184, 196, 0.2); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}
@keyframes tourPop {{
    from {{ transform: translate(-50%, -50%) scale(0.85); opacity: 0; }}
    to {{ transform: translate(-50%, -50%) scale(1); opacity: 1; }}
}}
@keyframes tourPulse {{
    0% {{ transform: scale(1); box-shadow: 0 0 8px currentColor; }}
    100% {{ transform: scale(1.01); box-shadow: 0 0 20px currentColor; }}
}}

.sidebar-brand {{
    text-align: center;
    padding: 1.2rem 0.5rem 1.5rem;
    border-bottom: 1px solid var(--arkanetra-border);
    margin-bottom: 1rem;
}}
.sidebar-brand .logo-mark {{
    width: 48px; height: 48px;
    margin: 0 auto 0.6rem;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--arkanetra-orange), var(--arkanetra-cyan));
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    color: #ffffff !important;
    animation: logo-spin-pulse 10s infinite linear;
}}
.sidebar-brand .brand-name {{
    font-family: 'Yatra One', cursive;
    font-size: 1.45rem;
    letter-spacing: 0.05em;
    font-weight: 700;
    background: {logo_gradient};
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-shift 6s ease infinite, glow-pulse 4s ease-in-out infinite;
}}
.sidebar-brand .brand-sub {{
    font-size: 0.78rem;
    font-weight: 500;
    margin-top: 6px;
    color: {logo_sub} !important;
}}

/* Hero */
.hero-section {{
    background: linear-gradient(135deg, var(--arkanetra-navy) 0%, var(--arkanetra-blue) 55%, #1a3a5c 100%);
    border-radius: 20px;
    padding: 2.5rem 2.8rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--arkanetra-shadow);
}}
.hero-section::before {{
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(77,184,196,0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.hero-section::after {{
    content: '';
    position: absolute;
    bottom: -30%; left: 10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(232,93,4,0.1) 0%, transparent 70%);
    border-radius: 50%;
}}
.hero-content {{ position: relative; z-index: 1; }}
.hero-title {{
    font-family: 'Yatra One', cursive;
    font-size: 3.2rem;
    color: #ffffff !important;
    margin: 0;
    line-height: 1.1;
    letter-spacing: 0.06em;
}}
.hero-devanagari {{
    font-family: 'Yatra One', cursive;
    font-size: 1.6rem;
    color: var(--arkanetra-cyan-muted) !important;
    margin: 0.3rem 0 0.8rem;
    opacity: 0.9;
}}
.hero-tagline {{
    font-size: 1.05rem;
    color: rgba(255,255,255,0.85) !important;
    font-weight: 400;
    margin: 0;
}}
.hero-badge {{
    display: inline-block;
    margin-top: 1.2rem;
    padding: 6px 16px;
    background: rgba(77,184,196,0.15);
    border: 1px solid rgba(77,184,196,0.3);
    border-radius: 20px;
    font-size: 0.78rem;
    color: var(--arkanetra-cyan-muted) !important;
    letter-spacing: 0.03em;
}}

/* Cards */
.mission-card {{
    background: var(--arkanetra-glass);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--arkanetra-border);
    border-radius: 16px;
    padding: 1.25rem 1.4rem;
    box-shadow: var(--arkanetra-shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}}
.mission-card:hover {{
    transform: translateY(-2px);
    box-shadow: var(--arkanetra-shadow);
}}
.mission-card .card-icon {{
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}}
.mission-card .card-label {{
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {card_label} !important;
    font-weight: 600;
    margin-bottom: 0.3rem;
}}
.mission-card .card-value {{
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--arkanetra-deep) !important;
    line-height: 1.2;
}}
.mission-card .card-delta {{
    font-size: 0.82rem;
    color: var(--arkanetra-cyan) !important;
    margin-top: 0.25rem;
}}
.mission-card.orange-accent {{ border-left: 4px solid var(--arkanetra-orange); }}
.mission-card.cyan-accent {{ border-left: 4px solid var(--arkanetra-cyan); }}
.mission-card.navy-accent {{ border-left: 4px solid var(--arkanetra-navy); }}
.mission-card.red-accent {{ border-left: 4px solid #dc2626; }}

/* Section headers */
.section-header {{
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--arkanetra-deep) !important;
    margin: 1.8rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--arkanetra-border);
}}
.section-header span {{
    color: var(--arkanetra-orange) !important;
}}

/* Insight cards */
.insight-card {{
    background: var(--arkanetra-surface);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    border-left: 4px solid var(--arkanetra-cyan);
    box-shadow: var(--arkanetra-shadow);
    margin-bottom: 0.8rem;
}}
.insight-card p {{
    margin: 0;
    color: {insight_p} !important;
    font-size: 0.95rem;
    line-height: 1.55;
}}
.insight-card .insight-label {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--arkanetra-cyan) !important;
    font-weight: 600;
    margin-bottom: 0.4rem;
}}

/* Gauge container */
.gauge-container {{
    background: var(--arkanetra-surface);
    border-radius: 16px;
    padding: 1rem;
    border: 1px solid var(--arkanetra-border);
    box-shadow: var(--arkanetra-shadow);
    text-align: center;
}}

/* Page title */
.page-title {{
    font-family: 'Yatra One', cursive;
    font-size: 1.8rem;
    color: var(--arkanetra-deep) !important;
    margin-bottom: 0.3rem;
}}
.page-subtitle {{
    color: var(--arkanetra-cyan-muted) !important;
    font-size: 0.92rem;
    margin-bottom: 1.2rem;
}}

/* Footer */
.arkanetra-footer {{
    text-align: center;
    padding: 2rem 1rem 1rem;
    margin-top: 2rem;
    border-top: 1px solid var(--arkanetra-border);
}}
.arkanetra-footer .footer-brand {{
    font-family: 'Yatra One', cursive;
    font-size: 1.3rem;
    color: var(--arkanetra-deep) !important;
}}
.arkanetra-footer .footer-sub {{
    font-size: 0.82rem;
    color: var(--arkanetra-cyan-muted) !important;
    margin-top: 0.3rem;
}}
.arkanetra-footer .footer-tag {{
    font-size: 0.75rem;
    color: var(--arkanetra-cyan) !important;
    margin-top: 0.5rem;
}}

/* Leaderboard */
.leaderboard-row {{
    display: flex;
    align-items: center;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
    background: var(--arkanetra-surface);
    border-radius: 10px;
    border: 1px solid var(--arkanetra-border);
}}
.leaderboard-rank {{
    font-weight: 700;
    font-size: 1.1rem;
    color: var(--arkanetra-orange) !important;
    width: 36px;
}}
.leaderboard-bar {{
    flex: 1;
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    margin: 0 1rem;
    overflow: hidden;
}}
.leaderboard-bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--arkanetra-cyan), var(--arkanetra-orange));
    border-radius: 4px;
}}

/* Zone badges */
.zone-badge-1 {{ background: #dc2626; color: white !important; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; }}
.zone-badge-2 {{ background: #ea580c; color: white !important; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; }}
.zone-badge-3 {{ background: #ca8a04; color: white !important; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; }}

/* Streamlit overrides */
h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {{
    color: var(--arkanetra-deep);
}}
.stMetricValue {{ color: var(--arkanetra-deep) !important; }}
.stButton > button {{
    background: linear-gradient(135deg, var(--arkanetra-navy), var(--arkanetra-blue)) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}
.stDownloadButton > button {{
    background: linear-gradient(135deg, var(--arkanetra-orange), var(--arkanetra-orange-light)) !important;
    color: white !important;
    border-radius: 10px !important;
}}

@media (max-width: 768px) {{
    .hero-title {{ font-size: 2.2rem; }}
    .hero-section {{ padding: 1.8rem 1.5rem; }}
    .mission-card .card-value {{ font-size: 1.4rem; }}
    .tour-container.sidebar-modal {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }}
    .tour-container.sidebar-modal::after {{
        display: none;
    }}
}}
</style>
"""

ARKANETRA_CSS = get_arkanetra_css(True)
