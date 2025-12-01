import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import os
from PIL import Image
from plotly.subplots import make_subplots
from streamlit_elements import elements, mui, html
from pathlib import Path

# Project root (folder where Streamlit.py lives)
project_root = Path(__file__).resolve().parent

# Import choropleth builder
try:
    from graphs.choropleth_builder import prepare_geospatial_data, build_choropleth_figure
    CHOROPLETH_AVAILABLE = True
except ImportError:
    CHOROPLETH_AVAILABLE = False
    st.warning("⚠️ Choropleth visualization not available. Please ensure geopandas and fiona are installed.")

# If the module imported successfully, ensure required geospatial files exist in graphs/data.
if CHOROPLETH_AVAILABLE:
    # Look for geospatial files either under graphs/data/ OR project-level data/
    graphs_data_dir = project_root / "graphs" / "data"
    project_data_dir = project_root / "data"

    shapefile_candidates = [
        graphs_data_dir / "macao.shp",
        graphs_data_dir / "macao-shapefile" / "macao.shp",
        project_data_dir / "macao.shp",
        project_data_dir / "macao-shapefile" / "macao.shp",
    ]

    geojson_candidates = [
        graphs_data_dir / "macaushape.geojson",
        project_data_dir / "macaushape.geojson",
    ]

    shapefile_path = next((p for p in shapefile_candidates if p.exists()), None)
    geojson_path = next((p for p in geojson_candidates if p.exists()), None)

    if not (shapefile_path or geojson_path):
        CHOROPLETH_AVAILABLE = False
        CHOROPLETH_MISSING_REASON = (
            "Missing geospatial files. Expected a shapefile or macaushape.geojson in either 'graphs/data/' or 'data/'."
        )
        st.warning(
            "⚠️ Choropleth geospatial files missing — expected files in `graphs/data/` or `data/` (e.g. macao.shp or macaushape.geojson). The choropleth will be disabled until these files are present."
        )
    else:
        CHOROPLETH_MISSING_REASON = None

# Import refactored modules
from config import COLORS, FILE_NAMES, PAGE_CONFIG
from modules.data_loader import load_data, load_choropleth_data
from utils.calculations import format_yoy_label, get_yoy_style, compute_dependency_ratio, compute_median_age
from modules.ui_components import section_header, decorative_header
from sections.overview import show_overview
from sections.pyramid import show_pyramid
from sections.analysis import show_analysis

# Page configuration
st.set_page_config(
    page_title="Macao Demographics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

# Global styles with enhanced decoration
st.markdown("""
    <style>
    * {
        box-sizing: border-box;
    }
    
    /* Reduce overall padding and margins */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 100% !important;
    }
    
    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
    }
    
    body {
        background: white;
    }
    .stApp {
        background: white;
    }
    
    /* Enhanced sidebar with decorative pattern */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2c5aa0 50%, #1e3a5f 100%);
        width: 280px !important;
        position: relative;
    }
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(255,255,255,0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(255,255,255,0.03) 0%, transparent 50%);
        pointer-events: none;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: white;
        font-weight: 500;
    }
    button[kind="header"] {
        color: white;
    }
    [data-testid="stSidebar"] button {
        color: white !important;
    }
    [data-testid="stSidebar"] .stSelectSlider > div > div {
        color: white !important;
    }
    [data-testid="stSidebar"] .stSelectSlider div div {
        color: white;
    }
    [data-testid="stSidebar"] .stSlider span {
        color: white;
    }
    [data-testid="stSidebar"] span[data-testid="stMarkdownContainer"] {
        color: white;
    }
    [data-testid="stSidebar"] * {
        color: white;
    }
    [data-testid="stSidebar"] input {
        color: white;
    }
    
    /* Enhanced metric cards with icon decorations */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);
        margin-bottom: 8px;
        border: 1px solid rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 150px;
        height: 150px;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .metric-card:hover {
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.25);
        transform: translateY(-2px);
        border-left-color: #764ba2;
    }
    
    /* Enhanced chart containers with reduced margins */
    .chart-container {
        background: white;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
        margin-bottom: 12px;
        border: 1px solid rgba(102, 126, 234, 0.08);
        position: relative;
    }
    .chart-container::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.03), transparent);
        border-radius: 0 16px 0 100%;
        pointer-events: none;
    }
    
    /* Enhanced chart titles with decorative underline */
    .chart-title {
        font-size: 1.2em;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        padding-bottom: 8px;
        border-bottom: 3px solid transparent;
        background: linear-gradient(white, white) padding-box,
                    linear-gradient(90deg, #667eea 0%, #764ba2 50%, transparent 100%) border-box;
        border-bottom: 3px solid transparent;
        background-clip: padding-box, border-box;
        background-origin: padding-box, border-box;
    }
    
    /* Decorative sections with glow effect */
    .section-divider {
        height: 3px;
        background: linear-gradient(90deg, transparent, #667eea 20%, #764ba2 50%, #667eea 80%, transparent);
        margin: 20px 0;
        border-radius: 2px;
        box-shadow: 0 2px 12px rgba(102, 126, 234, 0.3);
        position: relative;
    }
    .section-divider::after {
        content: '';
        position: absolute;
        top: -2px;
        left: 50%;
        transform: translateX(-50%);
        width: 40%;
        height: 7px;
        background: linear-gradient(90deg, transparent, rgba(118, 75, 162, 0.2), transparent);
        filter: blur(4px);
    }
    
    /* Enhanced statistics boxes */
    .stat-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
        border-left: 5px solid #667eea;
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        position: relative;
    }
    .stat-box::before {
        content: '▸';
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: #667eea;
        font-size: 1.2em;
        opacity: 0;
        transition: all 0.3s ease;
    }
    .stat-box:hover {
        border-left-color: #764ba2;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        padding-left: 30px;
    }
    .stat-box:hover::before {
        opacity: 1;
        left: 16px;
    }
    
    /* Enhanced badge styling with icons */
    .badge {
        display: inline-block;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        margin: 4px 4px 4px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    .badge:hover {
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
    }
    .badge-primary {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(102, 126, 234, 0.25));
        color: #667eea;
        border: 1px solid #667eea;
    }
    .badge-success {
        background: linear-gradient(135deg, rgba(39, 174, 96, 0.15), rgba(39, 174, 96, 0.25));
        color: #27ae60;
        border: 1px solid #27ae60;
    }
    .badge-warning {
        background: linear-gradient(135deg, rgba(243, 156, 18, 0.15), rgba(243, 156, 18, 0.25));
        color: #f39c12;
        border: 1px solid #f39c12;
    }
    .badge-danger {
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.15), rgba(231, 76, 60, 0.25));
        color: #e74c3c;
        border: 1px solid #e74c3c;
    }
    
    /* Info boxes with decorative corners */
    .info-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        border: 2px solid rgba(102, 126, 234, 0.2);
        position: relative;
    }
    .info-box::before,
    .info-box::after {
        content: '';
        position: absolute;
        width: 20px;
        height: 20px;
        border: 3px solid #667eea;
    }
    .info-box::before {
        top: -2px;
        left: -2px;
        border-right: none;
        border-bottom: none;
        border-radius: 12px 0 0 0;
    }
    .info-box::after {
        bottom: -2px;
        right: -2px;
        border-left: none;
        border-top: none;
        border-radius: 0 0 12px 0;
    }
    
    /* Enhanced section headers */
    h2, h3 {
        color: #1e3a5f !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Section header styling */
    .section-header {
        color: #1e3a5f;
        font-weight: 800;
        font-size: 1.4em;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .section-underline {
        height: 3px;
        width: 55px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 2px;
        box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
    }
    
    /* Plotly chart containers - reduce margins */
    .js-plotly-plot {
        margin-bottom: 0 !important;
    }
    
    /* Streamlit columns - reduce gaps */
    [data-testid="column"] {
        padding: 0 0.5rem !important;
    }
    
    /* Smooth transitions */
    * {
        transition: background-color 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease, transform 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

demographics, pyramid, pyramid_percent = load_data()
regions_gdf, geojson = load_choropleth_data()

# Add derived metrics to dataframe
if demographics is not None:
    # compute dependency ratio and median age per row
    demographics['Dependency ratio'] = demographics.apply(compute_dependency_ratio, axis=1)
    demographics['Median age'] = demographics.apply(compute_median_age, axis=1)

if demographics is None:
    st.stop()

# Sidebar - styled
st.sidebar.title("📊 Dashboard Controls")
st.sidebar.markdown("---")

years = demographics['Year'].dropna().astype(int).tolist()
st.sidebar.markdown('<p style="font-size:18px; font-weight:800; color:#e0f0ff; margin-top: -10px; margin-bottom: 0px;">Select Year</p>', unsafe_allow_html=True)
selected_year = st.sidebar.select_slider(
    "Select Year",
    options=years,
    value=2024,
    label_visibility='collapsed'
)

# Initialize session state for visualization type
if 'viz_type' not in st.session_state:
    st.session_state.viz_type = "Overview"

# Navigation buttons with dynamic highlighting
st.sidebar.markdown('<p style="margin-bottom: 0px;"><strong>Click a button below to switch views:</strong></p>', unsafe_allow_html=True)

# Button styling
button_style = """
    <style>
    [data-testid="stSidebar"] [data-testid="stButton"] {
        margin: 1px 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        width: 100%;
        padding: 10px 12px;
        border: 2px solid transparent;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: left;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #5f3d8e 100%);
        color: white !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:active {
        transform: scale(0.98);
    }
    /* Highlight active button */
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
        border-color: rgba(255,255,255,0.8) !important;
        box-shadow: 0 0 15px rgba(255,255,255, 0.4) !important;
        transform: scale(1.02) !important;
        font-weight: 700 !important;
    }
    </style>
"""

st.sidebar.markdown(button_style, unsafe_allow_html=True)

# Three functional buttons
if st.sidebar.button("Overview", key="nav_overview", width='stretch', type="primary" if st.session_state.viz_type == "Overview" else "secondary"):
    st.session_state.viz_type = "Overview"
    st.rerun()

if st.sidebar.button("Population Pyramid", key="nav_pyramid", width='stretch', type="primary" if st.session_state.viz_type == "Population Pyramid" else "secondary"):
    st.session_state.viz_type = "Population Pyramid"
    st.rerun()

if st.sidebar.button("Demographic Analysis", key="nav_trends", width='stretch', type="primary" if st.session_state.viz_type == "Demographic Analysis" else "secondary"):
    st.session_state.viz_type = "Demographic Analysis"
    st.rerun()

viz_type = st.session_state.viz_type

# Reduce gap before About section
st.sidebar.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("<span style='font-size: 22px; font-weight: bold;'>About</span>", unsafe_allow_html=True)
st.sidebar.markdown(
    """
    <span style='font-size: 16px; font-weight: bold;'>Macao Demographics Dashboard</span>
    
    Demographic analysis of Macao SAR from 1999-2024

    <span style='font-size: 16px; font-weight: bold;'>Key Features:</span>
    - Interactive temporal analysis (1999-2024)
    - Age-gender population pyramids  
    - Multi-dimensional trend visualization
    - Regional demographic mapping

    <span style='font-size: 16px; font-weight: bold;'>Data Sources:</span>
    
    Macao Statistics and Census Service
    """,
    unsafe_allow_html=True
)

# Get current year data
current_data = demographics[demographics['Year'] == selected_year].iloc[0]

# =======================
# OVERVIEW SECTION
# =======================
if "Overview" in viz_type:
    show_overview(selected_year, demographics, pyramid, pyramid_percent, regions_gdf, geojson, project_root, CHOROPLETH_AVAILABLE)
elif "Population Pyramid" in viz_type:
    show_pyramid(selected_year, project_root)
elif "Demographic Analysis" in viz_type:
    show_analysis(selected_year, project_root)
# Footer
st.markdown("---")
with elements("footer"):
    mui.Box(
        mui.Typography(
            "Macao Demographics Dashboard | Data: 1999-2024",
            variant="body2",
            style={"textAlign": "center", "color": "#7f8c8d"}
        ),
        mui.Typography(
            "Source: Macao Statistics and Census Service",
            variant="caption",
            style={"textAlign": "center", "color": "#95a5a6", "display": "block", "marginTop": "8px"}
        ),
        style={"padding": "15px", "textAlign": "center"}
    )
