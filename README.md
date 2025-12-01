# Macao Demographics Dashboard

An interactive Streamlit-based dashboard for analyzing and visualizing demographic data of Macao Special Administrative Region (SAR) from 1999 to 2024.

## Features

- **Overview**: Key demographic metrics, population trends, and regional choropleth maps
- **Population Pyramid**: Interactive age-gender population pyramids with absolute and percentage views
- **Demographic Analysis**: Multi-dimensional trend visualizations, age structure analysis, and forecasting
- **Interactive Controls**: Year selection slider and navigation between different analysis sections
- **Responsive Design**: Wide layout with enhanced styling and sidebar controls

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd courseproject7201
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure geospatial data files are present in the `data/` directory (e.g., `macao.shp`, `macaushape.geojson`).

## Usage

Run the Streamlit application:
```bash
streamlit run Streamlit.py
```

Navigate through the dashboard using the sidebar controls:
- Select a year using the slider (1999-2024)
- Click on section buttons: Overview, Population Pyramid, Demographic Analysis

## Data Sources

- **Primary Data**: Macao Statistics and Census Service
- **Geospatial Data**: Macao administrative boundaries (shapefiles and GeoJSON)
- **Time Period**: 1999-2024

## Project Structure

```
courseproject7201/
├── config.py                 # Configuration settings and file paths
├── requirements.txt          # Python dependencies
├── Streamlit.py             # Main Streamlit application
├── data/                    # Data directory
│   ├── macaushape.geojson   # Geospatial boundary data
│   ├── macao-shapefile/     # Shapefile components
│   └── processed/           # Processed CSV data files
├── graphs/                  # Generated visualizations and HTML files
├── modules/                 # Reusable modules
│   ├── data_loader.py       # Data loading utilities
│   └── ui_components.py     # UI component helpers
├── sections/                # Dashboard sections
│   ├── overview.py          # Overview section
│   ├── pyramid.py           # Population pyramid section
│   └── analysis.py          # Analysis section
└── utils/                   # Utility functions
    └── calculations.py      # Demographic calculations
```

## Dependencies

- geopandas: Geospatial data handling
- pandas: Data manipulation
- plotly: Interactive visualizations
- shapely: Geometric operations
- fiona: Geospatial file I/O
- pyproj: Coordinate transformations
- folium: Leaflet maps
- branca: Color schemes for maps
- streamlit_elements: Enhanced Streamlit UI components

## Requirements

- Python 3.7+
- Streamlit
- Geospatial libraries (GeoPandas, Fiona, etc.)

## Troubleshooting

- **Choropleth maps not loading**: Ensure geospatial files (`macao.shp` or `macaushape.geojson`) are present in the `data/` directory.
- **Import errors**: Verify all dependencies are installed via `pip install -r requirements.txt`.
- **Data loading issues**: Check that processed CSV files exist in `data/processed/`.
