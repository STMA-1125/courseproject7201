# Macao Demographics Dashboard

An interactive Streamlit-based dashboard for analyzing and visualizing demographic data of Macao Special Administrative Region (SAR) from 1999 to 2024.

## Features

- **Overview**: Key demographic metrics, population age structure and trends, non-resident workers, and regional choropleth map
- **Population Pyramid**: Interactive age-gender population pyramids with absolute and percentage views
- **Demographic Analysis**: Multi-dimensional trend visualizations, age structure analysis, and forecasting
- **Interactive Controls**: Year selection slider and navigation between different analysis sections
- **Responsive Design**: Wide layout with enhanced styling and sidebar controls
- **Performance Optimized**: Efficient caching and vectorized computations

## Installation

1. **Clone this repository:**
   ```bash
   git clone <repository-url>
   cd courseproject7201
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure data files are present:**
   - Demographic data in `data/processed/`
   - Geospatial files in `data/` 

## Usage

**Run the Streamlit application (local):**
```bash
streamlit run streamlit_app.py
```

**Navigate the dashboard:**
- Use the year slider (1999-2024) in the sidebar
- Click section buttons to switch views:
  - Overview
  - Population Pyramid
  - Demographic Analysis

## Deployment
The dashboard has been deployed to Streamlit Cloud for web access: https://courseproject7201-groupbh.streamlit.app/

**Hosted App Note:**
During development, we've encountered some issues with the Streamlit Cloud deployment.
- **Primary:** The main app at https://courseproject7201-groupbh.streamlit.app/ may not work due to unexpected issues.
- **Fallback:** If the main app is not working, please use our fallback app at https://finalproject-groupbh.streamlit.app/.

## Project Structure

```
courseproject7201/
├── streamlit_app.py           # Main application entry point
├── config.py                  # Configuration (paths, colors, settings)
├── requirements.txt           # Python dependencies
│
├── data/                      # Data directory
│   ├── processed/            # Cleaned demographic CSVs
│   │   ├── macao_demographics_1999_2024.csv
│   │   ├── population_pyramid_data.csv
│   │   └── population_pyramid_data_percentage.csv
│   ├── raw/                  # Original datasets
│   │   ├── dsec_dataset.csv                 # DSEC dataset
│   │   ├── time-series_preprocessing.py     # Preprocessing script
│   └── macao-shapefile/      # Geospatial files 
│
├── modules/                   # Core modules
│   ├── data_loader.py        # Data loading utilities
│   └── ui_components.py      # Reusable UI components
│
├── sections/                  # Page sections
│   ├── overview.py           # Overview page
│   ├── pyramid.py            # Population pyramid page
│   └── analysis.py           # Analysis page
│
├── graphs/                    # Visualization builders
│   ├── choropleth_builder.py # Choropleth map generation
│   └── [other visualization scripts]
│
├── utils/                     # Utility functions
│   └── calculations.py       # Demographic calculations
│
├── static/                    # Static assets
│   └── styles.css            # Custom CSS
│
└── images/                    # Icons and images
```

## Dependencies

### Core
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **plotly**: Interactive visualizations

### Geospatial 
- **geopandas**: Geospatial data handling
- **shapely**: Geometric operations
- **fiona**: Geospatial file I/O
- **pyproj**: Coordinate transformations
- **folium**: Leaflet maps
- **branca**: Color schemes for maps

### UI Components
- **streamlit-elements**  Enhanced UI elements

## Data Sources

- **Primary Data**: Macao Statistics and Census Service (DSEC)
- **Geospatial Data**: Macao administrative boundaries (shapefiles and GeoJSON)
- **Time Period**: 1999-2024
- **Update Frequency**: Annual

## Troubleshooting

### Common Issues

**Choropleth maps not loading:**
- Ensure geospatial files exist in `data/` directory
- Install geospatial dependencies: `pip install geopandas fiona shapely`
- Check file paths in `config.py`

**Import errors:**
- Verify all dependencies: `pip install -r requirements.txt`
- Check Python version (3.7+ required, 3.9+ recommended)
- Consider using a virtual environment

**Data loading issues:**
- Verify CSV files exist in `data/processed/`
- Check file permissions
- Review logs for specific errors



