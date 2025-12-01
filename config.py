from pathlib import Path

# Project root (folder where config.py lives)
PROJECT_ROOT = Path(__file__).resolve().parent

# Directories
DATA_DIR = PROJECT_ROOT / "data" / "processed"
GRAPHS_DIR = PROJECT_ROOT / "graphs"

# File names
FILE_NAMES = {
    "demographics": "macao_demographics_1999_2024.csv",
    "pyramid": "population_pyramid_data.csv",
    "abs_pyramid": "macao_population_pyramid_abs_value.html",
    "percent_pyramid": "macao_population_pyramid_percentage.html",
    "trends": "Macao_Demographic_Trends.html",
    "age_structure": "agestructure_analysis.html"
}

# Colors
COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "success": "#27ae60",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "dark_blue": "#1e3a5f",
    "medium_blue": "#2c5aa0"
}

# Page configuration
PAGE_CONFIG = {
    "page_title": "Macao Demographics Dashboard",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "auto"
}