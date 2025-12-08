"""Configuration file for Macao Demographics Dashboard.

Contains paths, color schemes, and page configuration settings.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data" / "processed"
GRAPHS_DIR = PROJECT_ROOT / "graphs"
IMAGES_DIR = PROJECT_ROOT / "images"
STATIC_DIR = PROJECT_ROOT / "static"

# Data file names
FILE_NAMES = {
    "demographics": "macao_demographics_1999_2024.csv",
    "pyramid": "population_pyramid_data.csv",
    "pyramid_percent": "population_pyramid_data_percentage.csv",
    "abs_pyramid": "macao_population_pyramid_abs_value.html",
    "percent_pyramid": "macao_population_pyramid_percentage.html",
    "trends": "Macao_Demographic_Trends.html",
    "age_structure": "agestructure_analysis.html"
}

# Color scheme for visualizations
COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "success": "#27ae60",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "info": "#3498db",
    "dark_blue": "#1e3a5f",
    "medium_blue": "#2c5aa0",
    "light_gray": "#ecf0f1",
    "dark_gray": "#34495e"
}

# Page configuration
PAGE_CONFIG = {
    "page_title": "Macao Demographics Dashboard",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "auto"
}

# Cache configuration (in seconds)
CACHE_TTL = {
    "data": 3600,  # 1 hour
    "plots": 1800,  # 30 minutes
}

# Data validation thresholds
DATA_VALIDATION = {
    "min_year": 1999,
    "max_year": 2024,
    "min_population": 0,
    "max_population": 1_000_000
}