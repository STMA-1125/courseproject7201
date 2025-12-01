import pandas as pd
import streamlit as st
from pathlib import Path
from config import DATA_DIR, GRAPHS_DIR

# Import choropleth builder if available
try:
    from graphs.choropleth_builder import prepare_geospatial_data, build_choropleth_figure
    CHOROPLETH_AVAILABLE = True
except ImportError:
    CHOROPLETH_AVAILABLE = False

@st.cache_data
def load_data():
    try:
        demographics = pd.read_csv(DATA_DIR / 'macao_demographics_1999_2024.csv')
        pyramid = pd.read_csv(DATA_DIR / 'population_pyramid_data.csv')
        pyramid_percent = pd.read_csv(DATA_DIR / 'population_pyramid_data_percentage.csv')
        return demographics, pyramid, pyramid_percent
    except FileNotFoundError:
        st.error("Data files not found. Please ensure CSV files are in data/processed/")
        return None, None, None

@st.cache_data
def load_choropleth_data():
    """Load geospatial data for choropleth visualization."""
    if not CHOROPLETH_AVAILABLE:
        return None, None
    try:
        regions_gdf, geojson = prepare_geospatial_data()
        return regions_gdf, geojson
    except Exception as e:
        st.warning(f"⚠️ Could not load choropleth data: {e}")
        return None, None