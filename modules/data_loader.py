"""Data loading utilities for Macao Demographics Dashboard.

Handles loading and caching of demographic and geospatial data.
"""
import logging
import pandas as pd
import streamlit as st

from config import DATA_DIR

# Configure logging
logger = logging.getLogger(__name__)


def _file_mtime_ns(path) -> int:
    """Return file modified time in nanoseconds.

    Used to invalidate Streamlit caches when underlying files change.
    """
    return path.stat().st_mtime_ns


@st.cache_data(show_spinner=False)
def _read_csv_cached(path_str: str, mtime_ns: int) -> pd.DataFrame:
    """Read a CSV with cache invalidation controlled by file mtime."""
    # NOTE: mtime_ns is intentionally unused except as part of the cache key.
    return pd.read_csv(path_str)

# Import choropleth builder if available (optional geospatial dependency)
try:
    from graphs.choropleth_builder import GEO_DEPS_AVAILABLE, prepare_geospatial_data
    CHOROPLETH_AVAILABLE = bool(GEO_DEPS_AVAILABLE)
except ImportError:
    CHOROPLETH_AVAILABLE = False
    logger.warning("Choropleth builder not available - geospatial dependencies may be missing")

@st.cache_data(show_spinner="Loading demographic data...")
def load_data():
    """Load demographic data from CSV files.
    
    Returns:
        tuple: (demographics, pyramid, pyramid_percent) DataFrames or (None, None, None) on error
    """
    try:
        demographics_path = DATA_DIR / 'macao_demographics_1999_2024.csv'
        pyramid_path = DATA_DIR / 'population_pyramid_data.csv'
        pyramid_percent_path = DATA_DIR / 'population_pyramid_data_percentage.csv'

        demographics = _read_csv_cached(str(demographics_path), _file_mtime_ns(demographics_path))
        pyramid = _read_csv_cached(str(pyramid_path), _file_mtime_ns(pyramid_path))
        pyramid_percent = _read_csv_cached(str(pyramid_percent_path), _file_mtime_ns(pyramid_percent_path))
        
        logger.info(f"Successfully loaded {len(demographics)} demographic records")
        return demographics, pyramid, pyramid_percent
    except FileNotFoundError as e:
        logger.error(f"Data files not found: {e}")
        st.error("Data files not found. Please ensure CSV files are in data/processed/")
        return None, None, None
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        st.error(f"Failed to load data: {str(e)}")
        return None, None, None

@st.cache_data(show_spinner="Loading geospatial data...")
def load_choropleth_data():
    """Load geospatial data for choropleth maps.
    
    Returns:
        tuple: (regions_gdf, geojson) or (None, None) if unavailable
    """
    if not CHOROPLETH_AVAILABLE:
        logger.info("Choropleth not available - skipping geospatial data loading")
        return None, None
    
    try:
        regions_gdf, geojson = prepare_geospatial_data()
        logger.info("Successfully loaded geospatial data")
        return regions_gdf, geojson
    except Exception as e:
        logger.warning(f"Could not load choropleth data: {e}")
        st.warning(f"⚠️ Could not load choropleth data: {e}")
        return None, None