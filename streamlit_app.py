"""Macao Demographics Dashboard - Main Application.

An interactive Streamlit dashboard for analyzing demographic data
of Macao SAR from 1999-2024.
"""

# Standard library imports
from pathlib import Path
import logging

# Third-party imports
import streamlit as st
import pandas as pd
from streamlit_elements import elements, mui

# Local imports
from utils.calculations import (
    compute_dependency_ratio_vectorized,
    compute_median_age_vectorized
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root directory
project_root = Path(__file__).resolve().parent

# Import choropleth builder (optional geospatial dependency)
try:
    from graphs.choropleth_builder import (
        GEO_DEPS_AVAILABLE,
        prepare_geospatial_data,
        build_choropleth_figure,
    )
    CHOROPLETH_AVAILABLE = bool(GEO_DEPS_AVAILABLE)
except ImportError:
    CHOROPLETH_AVAILABLE = False
    st.warning("⚠️ Choropleth visualization not available. Please ensure geopandas and fiona are installed.")

if CHOROPLETH_AVAILABLE:
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

# Local package imports
from config import COLORS, FILE_NAMES, PAGE_CONFIG
from modules.data_loader import load_data, load_choropleth_data
from modules.ui_components import section_header, decorative_header
from sections.analysis import show_analysis
from sections.overview import show_overview
from sections.pyramid import show_pyramid
from utils.calculations import (
    compute_dependency_ratio,
    compute_median_age,
    format_yoy_label,
    get_yoy_style,
)

# Page configuration
st.set_page_config(
    page_title="Macao Demographics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

css_file = Path(__file__).parent / "static" / "styles.css"
if css_file.exists():
    with open(css_file, 'r', encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
else:
    # Fallback to inline CSS if file not found
    st.warning("CSS file not found. Using default styles.")

@st.cache_data(ttl=3600, show_spinner="Loading demographic data...")
def load_and_enrich_data():
    """Load and enrich demographics data with computed metrics.
    
    Cached for 1 hour to avoid redundant computations.
    Uses vectorized operations for optimal performance.
    
    Returns:
        tuple: (demographics, pyramid, pyramid_percent) DataFrames
    """
    try:
        demographics, pyramid, pyramid_percent = load_data()
        
        if demographics is not None:
            # Use vectorized computations for better performance
            demographics['Dependency ratio'] = compute_dependency_ratio_vectorized(demographics)
            demographics['Median age'] = compute_median_age_vectorized(demographics)
            logger.info(f"Successfully loaded data for {len(demographics)} years")
        else:
            logger.error("Failed to load demographic data")
        
        return demographics, pyramid, pyramid_percent
    except Exception as e:
        logger.error(f"Error loading and enriching data: {e}")
        st.error(f"Failed to load data: {str(e)}")
        return None, None, None

# Load enriched data (cached)
demographics, pyramid, pyramid_percent = load_and_enrich_data()
regions_gdf, geojson = load_choropleth_data()

if demographics is None:
    st.error("Failed to load demographic data. Please check data files.")
    st.stop()

# Sidebar - styled
st.sidebar.title("📊 Dashboard Controls")
st.sidebar.markdown("---")

years = demographics['Year'].dropna().astype(int).tolist()
st.sidebar.markdown('<p style="font-size:18px; font-weight:800; color:#e0f0ff; margin-top: -10px; margin-bottom: 0px;">Select Year</p>', unsafe_allow_html=True)

# Get the last year from the data or default to 2024
default_year = years[-1] if years else 2024

selected_year = st.sidebar.select_slider(
    "Select Year",
    options=years,
    value=default_year if default_year in years else years[-1],
    label_visibility='collapsed'
)

# Validate that selected year exists in data
if selected_year not in demographics['Year'].values:
    st.error(f"⚠️ No data available for year {selected_year}. Please select a different year.")
    st.stop()

# Initialize session state
if 'viz_type' not in st.session_state:
    st.session_state.viz_type = "Overview"
if 'last_year' not in st.session_state:
    st.session_state.last_year = default_year

# Navigation buttons with optimized state management
def navigate_to(section: str) -> None:
    """Navigate to a specific section, only rerunning if state changes."""
    if st.session_state.viz_type != section:
        st.session_state.viz_type = section
        st.rerun()

# Button styling
button_style = """
    <style>
    [data-testid="stSidebar"] [data-testid="stButton"] {
        margin: 4px 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        width: 100%;
        padding: 10px 12px;
        border: 2px solid transparent;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        text-align: left;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #5f3d8e 100%);
        color: white !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    /* Highlight active button */
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
        border-color: rgba(255,255,255,0.8) !important;
        box-shadow: 0 0 15px rgba(255,255,255, 0.4) !important;
        font-weight: 700 !important;
    }
    </style>
"""

st.sidebar.markdown(button_style, unsafe_allow_html=True)

st.sidebar.markdown('<p style="margin-bottom: 0px;"><strong>Click a button below to switch views:</strong></p>', unsafe_allow_html=True)

if st.sidebar.button(
    "Overview",
    key="nav_overview",
    use_container_width=True,
    type="primary" if st.session_state.viz_type == "Overview" else "secondary"
):
    navigate_to("Overview")

if st.sidebar.button(
    "Population Pyramid",
    key="nav_pyramid",
    use_container_width=True,
    type="primary" if st.session_state.viz_type == "Population Pyramid" else "secondary"
):
    navigate_to("Population Pyramid")

if st.sidebar.button(
    "Demographic Analysis",
    key="nav_trends",
    use_container_width=True,
    type="primary" if st.session_state.viz_type == "Demographic Analysis" else "secondary"
):
    navigate_to("Demographic Analysis")

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

# Render selected section
try:
    if "Overview" in viz_type:
        show_overview(
            selected_year,
            demographics,
            pyramid,
            pyramid_percent,
            regions_gdf,
            geojson,
            project_root,
            CHOROPLETH_AVAILABLE
        )
    elif "Population Pyramid" in viz_type:
        show_pyramid(selected_year, project_root)
    elif "Demographic Analysis" in viz_type:
        show_analysis(selected_year, project_root, demographics)
except Exception as e:
    logger.error(f"Error rendering {viz_type}: {e}")
    st.error(f"Failed to render {viz_type}. Please try again or contact support.")
    st.exception(e)

# Footer
st.markdown("---")
try:
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
                style={
                    "textAlign": "center",
                    "color": "#95a5a6",
                    "display": "block",
                    "marginTop": "8px"
                }
            ),
            style={"padding": "15px", "textAlign": "center"}
        )
except Exception as e:
    # Fallback footer if elements fails
    st.markdown(
        "<p style='text-align: center; color: #7f8c8d;'>"
        "Macao Demographics Dashboard | Data: 1999-2024<br>"
        "<small>Source: Macao Statistics and Census Service</small></p>",
        unsafe_allow_html=True
    )
