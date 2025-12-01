"""Choropleth builder module for Macao demographics - Enhanced Edition"""

import json
from pathlib import Path
from typing import Tuple, Dict, Optional, List

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

try:
    import geopandas as gpd
    import fiona
    import shapely.geometry as geom
    import shapely.ops as ops
    from shapely.geometry import Point, box
except ImportError as e:
    print(f"⚠️ Warning: Missing geospatial packages. Choropleth may not work. {e}")


ROOT = Path(__file__).resolve().parent
# project root (one level up from graphs/) so the module can find data/ at repo root
PROJECT_ROOT = ROOT.parent

# Search common locations for shapefiles and geojsons: graphs/data/ and project_root/data/
SHP_PATHS = [
    ROOT / "data" / "macao.shp",
    ROOT / "data" / "macao-shapefile" / "macao.shp",
    PROJECT_ROOT / "data" / "macao.shp",
    PROJECT_ROOT / "data" / "macao-shapefile" / "macao.shp",
]

GEOJSON_PATH = next(
    (p for p in [ROOT / "data" / "macaushape.geojson", PROJECT_ROOT / "data" / "macaushape.geojson"] if p.exists()),
    ROOT / "data" / "macaushape.geojson"
)


def find_region_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    """Find the region name column in the GeoDataFrame."""
    candidates = [c for c in gdf.columns if any(x in c.lower() for x in ("name", "district", "area", "adm", "region"))]
    if candidates:
        return candidates[0]
    for c in gdf.columns:
        if c != gdf.geometry.name and gdf[c].dtype == 'object':
            return c
    return None


def load_shapefile() -> gpd.GeoDataFrame:
    """Load the Macao shapefile (contains the whole Macau boundary)."""
    shp_path = next((p for p in SHP_PATHS if p.exists()), SHP_PATHS[0])
    
    if not shp_path.exists():
        raise FileNotFoundError(f"❌ Shapefile not found at {shp_path}")
    
    try:
        gdf = gpd.read_file(shp_path)
    except Exception:
        try:
            with fiona.Env(SHAPE_RESTORE_SHX="YES"):
                gdf = gpd.read_file(shp_path)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to read shapefile: {e}")
    
    # Clean and validate
    print(f"✅ Loaded {len(gdf)} features from shapefile")
    
    # Remove empty/none geometries
    initial_len = len(gdf)
    gdf = gdf[~gdf.geometry.isna() & ~gdf.geometry.is_empty]
    if len(gdf) < initial_len:
        print(f"🗑️ Removed {initial_len - len(gdf)} empty geometries")
    
    # Ensure CRS
    if gdf.crs is None:
        print("⚠️ CRS not set, defaulting to EPSG:4326 (WGS84)")
        gdf = gdf.set_crs(epsg=4326)
    
    return gdf


def load_geojson() -> gpd.GeoDataFrame:
    """Load Macau, Taipa, and Coloane polygons from the Macao geojson file."""
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(f"❌ GeoJSON file not found at {GEOJSON_PATH}")
    
    try:
        gdf = gpd.read_file(GEOJSON_PATH)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to read geojson: {e}")
    
    # Filter to main administrative regions: Macau, Taipa, Coloane
    # Be specific to avoid matching boundary segments
    macau_filter = (gdf['name'] == '澳門 Macau') | (gdf['name:en'] == 'Macau')
    taipa_filter = (gdf['name'] == '氹仔 Taipa') | (gdf['name:en'] == 'Taipa')
    coloane_filter = (gdf['name'] == '路環 Coloane') | (gdf['name:en'] == 'Coloane')
    gdf = gdf[macau_filter | taipa_filter | coloane_filter]
    
    # Clean and validate
    print(f"✅ Loaded {len(gdf)} region polygons from GeoJSON")
    
    # Remove empty/none geometries
    initial_len = len(gdf)
    gdf = gdf[~gdf.geometry.isna() & ~gdf.geometry.is_empty]
    if len(gdf) < initial_len:
        print(f"🗑️ Removed {initial_len - len(gdf)} empty geometries")
    
    # Ensure CRS
    if gdf.crs is None:
        print("⚠️ CRS not set, defaulting to EPSG:4326 (WGS84)")
        gdf = gdf.set_crs(epsg=4326)
    
    return gdf
    
    # Clean and validate
    print(f"✅ Loaded {len(gdf)} administrative/island features from GeoJSON")
    
    # Remove empty/none geometries
    initial_len = len(gdf)
    gdf = gdf[~gdf.geometry.isna() & ~gdf.geometry.is_empty]
    if len(gdf) < initial_len:
        print(f"🗑️ Removed {initial_len - len(gdf)} empty geometries")
    
    # Ensure CRS
    if gdf.crs is None:
        print("⚠️ CRS not set, defaulting to EPSG:4326 (WGS84)")
        gdf = gdf.set_crs(epsg=4326)
    
    return gdf


def _fallback_voronoi_split(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Advanced Voronoi fallback with manual region verification."""
    print("\n🔄 Using Voronoi fallback method...")
    
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    
    gdf_4326 = gdf.to_crs(epsg=4326) if gdf.crs.to_epsg() != 4326 else gdf
    
    # Get Macao boundary
    macao_poly = gdf_4326.geometry.unary_union
    if macao_poly.is_empty:
        raise RuntimeError("Empty geometry union")
    
    macao_proj = gpd.GeoSeries([macao_poly], crs=gdf_4326.crs).to_crs(epsg=3857).iloc[0]
    
    # === CORRECTED SEED POINTS ===
    seeds = {
        "Macao Peninsula": (22.1987, 113.5439),
        "Taipa": (22.1568, 113.5637),
        "Coloane": (22.1135, 113.5530),
    }
    
    try:
        seed_points = []
        for name, (lat, lon) in seeds.items():
            p = Point(lon, lat)
            p_proj = gpd.GeoSeries([p], crs=4326).to_crs(epsg=3857).iloc[0]
            seed_points.append(p_proj)
        
        # Create Voronoi diagram
        multip = geom.MultiPoint(seed_points)
        envelope = macao_proj.buffer(5000)  # Large envelope
        vor = ops.voronoi_diagram(multip, envelope=envelope)
        vor_polys = list(vor.geoms) if hasattr(vor, 'geoms') else [vor]
        
        # Clip Voronoi cells to Macao boundary
        records = []
        names = list(seeds.keys())
        
        for i, seed in enumerate(seed_points):
            # Find cell containing this seed
            cell = min(vor_polys, key=lambda vp: vp.distance(seed))
            clipped = cell.intersection(macao_proj)
            
            if not clipped.is_empty:
                records.append({"region_name": names[i], "geometry": clipped})
        
        if not records:
            raise RuntimeError("Voronoi produced no valid regions")
        
        out = gpd.GeoDataFrame(records, geometry='geometry', crs='EPSG:3857')
        out = out.to_crs(gdf_4326.crs)
        
        print(f"✅ Voronoi fallback created {len(out)} regions: {out['region_name'].tolist()}")
        return out.reset_index(drop=True)
        
    except Exception as e:
        print(f"❌ Voronoi fallback failed: {e}")
        raise RuntimeError(f"Failed to create regions from shapefile: {e}")


def prepare_geospatial_data(use_manual_regions=False) -> Tuple[gpd.GeoDataFrame, Dict]:
    """Load and prepare geospatial data for choropleth with whole Macau base layer and regions from GeoJSON."""
    print("\n" + "="*60)
    print("PREPARING GEOSPATIAL DATA")
    print("="*60)

    # Load whole Macau shape from shapefile as base layer
    try:
        macau_gdf = load_shapefile()
        print("✅ Loaded whole Macau boundary from shapefile")
        print(f"   Geometry type: {macau_gdf.geometry[0].geom_type}")
        if macau_gdf.geometry[0].geom_type == 'MultiPolygon':
            print(f"   Number of parts: {len(list(macau_gdf.geometry[0].geoms))}")
    except Exception as e:
        print(f"❌ Failed to load shapefile: {e}")
        raise

    # Load polygons from macaushape.geojson
    try:
        regions_gdf = load_geojson()
        print("✅ Loaded regions from macaushape.geojson")
    except Exception as e:
        print(f"❌ Failed to load GeoJSON: {e}")
        raise

    # Filter to Taipa and Coloane from GeoJSON
    taipa_filter = (regions_gdf['name'] == '氹仔 Taipa') | (regions_gdf['name:en'] == 'Taipa')
    coloane_filter = (regions_gdf['name'] == '路環 Coloane') | (regions_gdf['name:en'] == 'Coloane')
    islands_gdf = regions_gdf[taipa_filter | coloane_filter]
    
    print(f"📍 Found {len(islands_gdf)} island polygons from GeoJSON")
    
    # Extract Taipa and Coloane geometries
    taipa_geom = islands_gdf[taipa_filter].iloc[0].geometry if taipa_filter.any() else None
    coloane_geom = islands_gdf[coloane_filter].iloc[0].geometry if coloane_filter.any() else None
    
    if taipa_geom is None or coloane_geom is None:
        raise ValueError("Could not find Taipa and Coloane polygons in GeoJSON")
    
    print(f"   Taipa area: {taipa_geom.area:.6f}")
    print(f"   Coloane area: {coloane_geom.area:.6f}")
    
    # Get the complete Macau boundary from shapefile
    macau_boundary = macau_gdf.iloc[0].geometry
    
    # Derive peninsula by subtracting Taipa and Coloane from complete boundary
    print("🔧 Deriving peninsula polygon from shapefile...")
    
    # Clean geometries using buffer(0) to fix any topology issues
    macau_boundary_clean = macau_boundary.buffer(0)
    taipa_geom_clean = taipa_geom.buffer(0)
    coloane_geom_clean = coloane_geom.buffer(0)
    
    # Perform difference operations
    peninsula_geom = macau_boundary_clean.difference(taipa_geom_clean).difference(coloane_geom_clean)
    
    # If result is a MultiPolygon, combine parts and filter out tiny fragments
    if peninsula_geom.geom_type == 'MultiPolygon':
        print(f"   Result is MultiPolygon with {len(peninsula_geom.geoms)} parts")
        # Filter out tiny fragments (less than 1% of total area)
        parts = list(peninsula_geom.geoms)
        total_area = sum(p.area for p in parts)
        significant_parts = [p for p in parts if p.area > total_area * 0.01]
        
        print(f"   Filtered to {len(significant_parts)} significant parts")
        for i, part in enumerate(significant_parts[:5]):  # Show first 5
            print(f"     Part {i}: area = {part.area:.6f}")
        
        # Take the largest part as the peninsula
        peninsula_geom = max(significant_parts, key=lambda g: g.area)
        print(f"   Selected largest part as peninsula")
    
    print(f"   Peninsula area: {peninsula_geom.area:.6f}")
    
    # Combine whole Macau base layer with region polygons
    records = []

    # Add whole Macau as base layer (dark grey)
    records.append({
        'region_name': 'Macau Base',
        'geometry': macau_boundary,
        'is_base_layer': True  # Mark as base layer for styling
    })

    # Add derived peninsula from shapefile
    records.append({
        'region_name': 'Macao Peninsula',
        'geometry': peninsula_geom,
        'is_base_layer': False
    })
    
    # Add Taipa and Coloane from GeoJSON
    records.append({
        'region_name': 'Taipa',
        'geometry': taipa_geom,
        'is_base_layer': False
    })
    
    records.append({
        'region_name': 'Coloane',
        'geometry': coloane_geom,
        'is_base_layer': False
    })

    # Create combined GeoDataFrame
    gdf = gpd.GeoDataFrame(records, geometry='geometry', crs=macau_gdf.crs)
    print(f"📝 Combined regions: {gdf['region_name'].unique().tolist()}")

    print(f"📝 Final regions: {gdf['region_name'].unique().tolist()}")

    # Build GeoJSON
    try:
        geojson = json.loads(gdf.to_json())
        print(f"✅ GeoJSON created with {len(geojson.get('features', []))} features")
    except Exception as e:
        print(f"⚠️ Standard GeoJSON export failed ({e}), using manual mapping")
        from shapely.geometry import mapping
        features = []
        for _, row in gdf.iterrows():
            geom_obj = row.geometry
            if geom_obj is None or geom_obj.is_empty:
                continue
            features.append({
                "type": "Feature",
                "geometry": mapping(geom_obj),
                "properties": {"region_name": row["region_name"]}
            })
        geojson = {"type": "FeatureCollection", "features": features}
        print(f"✅ Manual GeoJSON created with {len(features)} features")
    
    print("="*60)
    return gdf, geojson


def debug_region_split(gdf: gpd.GeoDataFrame, show_seed_points=True) -> None:
    """
    Visualize the regions with matplotlib to verify correctness.
    Call this immediately after prepare_geospatial_data()
    """
    try:
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        
        # Plot 1: Regions colored by name
        gdf.plot(column='region_name', ax=ax1, cmap='tab10', legend=True, categorical=True, alpha=0.7)
        ax1.set_title("Final Region Assignment", fontsize=14)
        ax1.set_xlabel("Longitude")
        ax1.set_ylabel("Latitude")
        
        # Plot 2: Regions with area labels
        gdf.plot(ax=ax2, color='lightgray', edgecolor='black', linewidth=0.8, alpha=0.5)
        
        for idx, row in gdf.iterrows():
            centroid = row.geometry.centroid
            area_km2 = row.geometry.to_crs(epsg=3857).area / 1e6
            
            # Plot centroid
            ax2.plot(centroid.x, centroid.y, 'ro', markersize=8)
            
            # Add annotation
            ax2.annotate(
                f"{row['region_name']}\n{area_km2:.1f} km²",
                xy=(centroid.x, centroid.y),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=10,
                ha='left',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='red')
            )
        
        # Show seed points if requested
        if show_seed_points:
            seeds = {
                "Macao Peninsula": (22.1987, 113.5439),
                "Taipa": (22.1568, 113.5637),
                "Coloane": (22.1135, 113.5530),
            }
            for name, (lat, lon) in seeds.items():
                ax1.plot(lon, lat, 'g*', markersize=15, label=name)
                ax2.plot(lon, lat, 'g*', markersize=15, label=name)
        
        ax2.set_title("Regions with Centroids & Areas", fontsize=14)
        ax2.set_xlabel("Longitude")
        ax2.legend()
        
        plt.tight_layout()
        plt.show()
        
        # Print summary
        print("\n" + "="*50)
        print("REGION VERIFICATION SUMMARY")
        print("="*50)
        for _, row in gdf.iterrows():
            area_km2 = row.geometry.to_crs(epsg=3857).area / 1e6
            bounds = row.geometry.bounds
            print(f"{row['region_name']:15s} | Area: {area_km2:8.2f} km² | Bounds: {bounds}")
        
    except ImportError:
        print("💡 Install matplotlib for visual debugging: pip install matplotlib")
    except Exception as e:
        print(f"❌ Debug visualization failed: {e}")


def build_choropleth_figure(
    selected_year: int,
    demographics_df: pd.DataFrame,
    regions_gdf: gpd.GeoDataFrame,
    geojson: Dict,
    global_vmin: float = None,
    global_vmax: float = None
) -> go.Figure:
    """
    Build a beautiful choropleth with enhanced colors and global scaling.
    """
    
    # Get data for the selected year
    year_data = demographics_df[demographics_df['Year'] == selected_year]
    
    if year_data.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No data available for {selected_year}", showarrow=False)
        return fig
    
    year_data = year_data.iloc[0]
    
    # Region density columns
    region_density_cols = {
        "Macao Peninsula": "Macao Peninsula a",
        "Taipa": "Taipa a", 
        "Coloane": "Coloane a"
    }
    
    # Get sorted region list (exclude base layer)
    all_regions = regions_gdf["region_name"].astype(str).unique().tolist()
    regions_list = sorted([r for r in all_regions if r != 'Macau Base'])
    
    # Extract density values
    values = []
    region_to_value = {}
    
    # Get overall density for fallback (1999-2006)
    overall_density = year_data.get('Population density', None)
    has_regional_data = False
    
    for region_name, col_name in region_density_cols.items():
        if col_name in demographics_df.columns:
            density_val = year_data.get(col_name, None)
            if density_val is not None and pd.notna(density_val) and density_val > 0:
                region_to_value[region_name] = float(density_val)
                has_regional_data = True
    
    # For years 1999-2006 (when regional data is not available), use overall density for all regions
    if not has_regional_data and overall_density is not None and pd.notna(overall_density) and overall_density > 0:
        for region_name in region_density_cols.keys():
            region_to_value[region_name] = float(overall_density)
    
    # Build values list matching sorted regions
    for region in regions_list:
        values.append(region_to_value.get(region, 0.0))
    
    # === GLOBAL COLOR SCALING ===
    if global_vmin is None or global_vmax is None:
        # Use fixed range from 0 to 60 km² as requested
        global_vmin, global_vmax = 0, 60
    
    # Ensure current year's values fit in global range
    vmin = max(0, global_vmin)
    vmax = global_vmax
    
    # === CONTINUOUS WHITE -> DARK RED COLOR SCALE ===
    # Create a discrete color scale with one step per 1 km² (0..60)
    def _interpolate_rgb(start_rgb, end_rgb, t):
        return tuple(int(start + (end - start) * t) for start, end in zip(start_rgb, end_rgb))

    # Light yellow -> orange -> a bit dark red
    start_rgb = (255, 255, 204)  # light yellow
    mid_rgb = (255, 165, 0)      # orange at midpoint
    end_rgb = (180, 0, 0)        # slightly dark red at end

    # For 0.1 unit steps from 0 to 60 we need 600 steps: 60 / 0.1 = 600 -> plus 1 for inclusive endpoint -> 601 stops
    n_steps = 600  # 0..60 inclusive -> 601 stops (0.1 per step)
    colorscale = []
    for i in range(n_steps + 1):
        t = i / n_steps
        # t in [0,1]; midpoint at 0.5
        if t <= 0.5:
            local_t = t / 0.5
            r, g, b = _interpolate_rgb(start_rgb, mid_rgb, local_t)
        else:
            local_t = (t - 0.5) / 0.5
            r, g, b = _interpolate_rgb(mid_rgb, end_rgb, local_t)
        colorscale.append([t, f'rgb({r},{g},{b})'])

    # Fallback to Jet if something goes wrong
    if not colorscale:
        colorscale = px.colors.sequential.Jet

    choropleth_trace = go.Choropleth(
        geojson=geojson,
        locations=regions_list,
        z=values,
        featureidkey="properties.region_name",
        colorscale=colorscale,
        zmin=vmin,
        zmax=vmax,
        marker=dict(
            line=dict(color='white', width=2.5),  # Slightly thicker borders
            opacity=0.95
        ),
        colorbar=dict(
            title=dict(
                text="Population Density<br>(1000 persons per km²)",
                font=dict(size=12, color='#333333', family="Arial"),
                side='right'
            ),
            tickfont=dict(size=10, color='#333333'),
            thickness=22,  # Slightly wider colorbar thickness
                len=0.65,      # Slightly taller colorbar length for improved visibility
            x=1.03,
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='#666666',
            borderwidth=1.0,
            # Show a tick every 5 km², with tick labels outside
            dtick=5,
            ticks='outside',
            tickvals=[i for i in range(0, 61, 5)],
            ticktext=[str(i) for i in range(0, 61, 5)],
            tickformat='.0f'  # Show whole numbers for cleaner display
        ),
        hovertemplate='<b>Macau</b><br>Overall density: %{z}k/km²<extra></extra>' if 1999 <= selected_year <= 2006 else '<b>%{location}</b><br>Density: %{z}k/km²<extra></extra>',
        name=''
    )
    
    # Create base layer trace for whole Macau (very dark grey) if it exists
    traces = []
    
    if 'Macau Base' in regions_gdf['region_name'].values:
        base_layer_trace = go.Choropleth(
            geojson=geojson,
            locations=['Macau Base'],  # Only the base layer
            z=[0],  # Dummy value
            featureidkey="properties.region_name",
            colorscale=[[0, 'white'], [1, 'white']],  # White color
            showscale=False,  # Don't show colorbar for base layer
            marker=dict(
                line=dict(color='white', width=1.5),
                opacity=1.0  # Fully opaque white
            ),
            hoverinfo='skip',  # Don't show hover for base layer
            name='Macau Base'
        )
        traces.append(base_layer_trace)
    
    traces.append(choropleth_trace)
    
    fig = go.Figure(data=traces)
    
    # Add text labels directly on regions
    regions_geo = regions_gdf.copy()
    if regions_geo.crs is None:
        regions_geo = regions_geo.set_crs(epsg=4326)
    
    if getattr(regions_geo.crs, 'to_epsg', lambda: None)() != 4326:
        regions_geo = regions_geo.to_crs(epsg=4326)
    
    # Calculate label positions
    label_lons = []
    label_lats = []
    label_texts = []
    label_colors = []
    label_bgcolors = []
    label_borders = []

    for idx, region_name in enumerate(regions_list):
        match = regions_geo[regions_geo['region_name'] == region_name]
        if not match.empty:
            geom_obj = match.geometry.unary_union
            centroid = geom_obj.centroid
            lon = centroid.x
            lat = centroid.y
        else:
            centroid = regions_geo.geometry.unary_union.centroid
            lon = centroid.x
            lat = centroid.y

        val = values[idx]
        label_lons.append(lon)
        label_lats.append(lat)
        label_texts.append(f"<b>{region_name}</b><br>{val:.1f}k/km²")

        # Dynamic text color based on density
        normalized_val = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
        
        # Use darker text for light backgrounds, white for dark backgrounds
        if normalized_val < 0.25:
            label_colors.append('#ffffff')  # White text
            label_bgcolors.append('rgba(0,0,0,0.5)')
            label_borders.append('rgba(255,255,255,0.3)')
        elif normalized_val > 0.75:
            label_colors.append('#000000')  # Black text
            label_bgcolors.append('rgba(255,255,255,0.4)')
            label_borders.append('rgba(0,0,0,0.2)')
        else:
            label_colors.append('#000000')
            label_bgcolors.append('rgba(255,255,255,0.3)')
            label_borders.append('rgba(0,0,0,0.1)')
    
    # Add annotations
    for lon, lat, text, color, bgcolor, border in zip(
        label_lons, label_lats, label_texts, label_colors, label_bgcolors, label_borders
    ):
        fig.add_annotation(
            x=lon, y=lat,
            text=text,
            showarrow=False,
            font=dict(size=14, color=color, family="Arial, sans-serif"),
            bgcolor=bgcolor,
            bordercolor=border,
            borderwidth=1,
            borderpad=6,
            xanchor="center",
            yanchor="middle",
            opacity=0.9
        )
    
    # Update layout
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        projection=dict(type='natural earth'),
        bgcolor='rgba(180, 180, 180, 0.8)'  # Darker grey background for map area
    )

    # Add a white header strip behind the title and increase top margin
    fig.update_layout(
        title=dict(
            text=f"Macao Population Density - {selected_year}",
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2c3e50', family="Arial")
        ),
        height=420,  # Set fixed height for consistent display
        margin=dict(l=20, r=120, t=60, b=20),  # Increase top margin to prevent title clipping
        paper_bgcolor='white',  # Page background should be white
        plot_bgcolor='white',  # Plot background (outer area) should be white
        hovermode='closest',
        font=dict(family="Arial, sans-serif"),
        # Enable zoom controls in modebar
        showlegend=False,
        shapes=[
            # white rectangle behind the title to make the title appear on white background
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                x1=1,
                y0=1.02,
                y1=1.12,
                fillcolor='white',
                opacity=1,
                layer='below',
                line=dict(width=0)
            )
        ]
    )
    
    return fig


