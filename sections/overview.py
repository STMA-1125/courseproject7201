import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import os
from streamlit_elements import elements, mui, html

from modules.ui_components import section_header, decorative_header
from utils.calculations import format_yoy_label, get_yoy_style

# Import choropleth builder (optional dependency)
try:
    from graphs.choropleth_builder import build_choropleth_figure
except ImportError:
    build_choropleth_figure = None

def show_overview(selected_year, demographics, pyramid, pyramid_percent, regions_gdf, geojson, project_root, choropleth_available=False):
    # Get current year data
    current_data = demographics[demographics['Year'] == selected_year].iloc[0]

    # Decorative header
    decorative_header(
        "Macao Demographics Dashboard",
        f"Year {int(selected_year)} • Population & Demographic Overview",
        ["📊 Population Insights", "📈 Demographic Trends", "🗺️ Regional Data"],
        icon='dashboard_icon',
        project_root=str(project_root),
        icon_bg= None,
        icon_bg_size=48,
        icon_inner_size=28,
        icon_margin_right=12,
        icon_size=36,
        padding='28px 32px',
        title_font_size='2.5em'
    )

    # Key Metrics Section
    section_header("Key Demographic Metrics", "🎯")

    # Get previous year data for year-on-year comparison
    prev_year = selected_year - 1
    prev_data = demographics[demographics['Year'] == prev_year]
    prev_data = prev_data.iloc[0] if not prev_data.empty else None

    # Create a two-column layout: KPIs (left, 3/4) and Age distribution (right, 1/4)
    col_kpis, col_age = st.columns([3, 1])

    with col_kpis:
        with elements("key_metrics"):
            # Prepare metric data
            total_pop = current_data['Total population'] if pd.notna(current_data.get('Total population')) else 0
            male_pop = current_data['Male'] if pd.notna(current_data.get('Male')) else 0
            female_pop = current_data['Female'] if pd.notna(current_data.get('Female')) else 0
            density = current_data['Population density'] if pd.notna(current_data.get('Population density')) else 0
            non_resident_workers = current_data['Non-resident workers total'] if pd.notna(current_data.get('Non-resident workers total')) else 0
            annual_growth = current_data['Annual growth rate'] if pd.notna(current_data.get('Annual growth rate')) else 0
            natural_growth = current_data['Rate of natural increase'] if pd.notna(current_data.get('Rate of natural increase')) else 0
            dependency = current_data.get('Dependency ratio', None)
            median_age = current_data.get('Median age', None)

            # Calculate year-on-year changes
            yoy_total_pop = None
            if prev_data is not None and pd.notna(prev_data.get('Total population')) and prev_data['Total population'] > 0:
                yoy_total_pop = ((total_pop - prev_data['Total population']) / prev_data['Total population']) * 100

            yoy_density = None
            if prev_data is not None and pd.notna(prev_data.get('Population density')):
                yoy_density = density - prev_data['Population density']

            yoy_workers = None
            if prev_data is not None and pd.notna(prev_data.get('Non-resident workers total')) and prev_data['Non-resident workers total'] > 0:
                yoy_workers = ((non_resident_workers - prev_data['Non-resident workers total']) / prev_data['Non-resident workers total']) * 100

            # Compute YoY for other KPIs if previous data exists
            yoy_annual_growth = None
            if prev_data is not None and pd.notna(prev_data.get('Annual growth rate')) and pd.notna(annual_growth):
                yoy_annual_growth = annual_growth - prev_data['Annual growth rate']

            yoy_natural_growth = None
            if prev_data is not None and pd.notna(prev_data.get('Rate of natural increase')) and pd.notna(natural_growth):
                yoy_natural_growth = natural_growth - prev_data['Rate of natural increase']

            yoy_crude_birth = None
            if prev_data is not None and pd.notna(prev_data.get('Crude birth rate')) and pd.notna(current_data.get('Crude birth rate')):
                yoy_crude_birth = current_data.get('Crude birth rate') - prev_data['Crude birth rate']

            yoy_crude_death = None
            if prev_data is not None and pd.notna(prev_data.get('Crude mortality rate')) and pd.notna(current_data.get('Crude mortality rate')):
                yoy_crude_death = current_data.get('Crude mortality rate') - prev_data['Crude mortality rate']

            yoy_dependency = None
            if prev_data is not None and pd.notna(prev_data.get('Dependency ratio')) and pd.notna(dependency):
                yoy_dependency = dependency - prev_data['Dependency ratio']

            yoy_median_age = None
            if prev_data is not None and pd.notna(prev_data.get('Median age')) and pd.notna(median_age):
                yoy_median_age = median_age - prev_data['Median age']

            # Prepare formatted YoY labels and styles with 1 decimal rounding
            pop_yoy_label = format_yoy_label(yoy_total_pop, '%', decimals=1, use_sign=True) if yoy_total_pop is not None else "YoY change"
            pop_yoy_style = get_yoy_style(round(yoy_total_pop, 1) if yoy_total_pop is not None else None)

            density_yoy_label = format_yoy_label(yoy_density, '', decimals=1, use_sign=True) if yoy_density is not None else "YoY change"
            density_yoy_style = get_yoy_style(yoy_density)

            workers_yoy_label = format_yoy_label(yoy_workers, '%', decimals=1, use_sign=True) if yoy_workers is not None else "YoY change"
            workers_yoy_style = get_yoy_style(yoy_workers)

            annual_yoy_label = format_yoy_label(yoy_annual_growth, '', decimals=1, use_sign=True) if 'yoy_annual_growth' in locals() and yoy_annual_growth is not None else "YoY change"
            annual_yoy_style = get_yoy_style(round(yoy_annual_growth, 1)) if 'yoy_annual_growth' in locals() and yoy_annual_growth is not None else get_yoy_style(None)

            natural_yoy_label = format_yoy_label(yoy_natural_growth, '', decimals=1, use_sign=True) if 'yoy_natural_growth' in locals() and yoy_natural_growth is not None else "YoY change"
            natural_yoy_style = get_yoy_style(yoy_natural_growth) if 'yoy_natural_growth' in locals() else get_yoy_style(None)

            crude_birth_yoy_label = format_yoy_label(yoy_crude_birth, '', decimals=1, use_sign=True) if 'yoy_crude_birth' in locals() and yoy_crude_birth is not None else "YoY change"
            crude_birth_yoy_style = get_yoy_style(yoy_crude_birth) if 'yoy_crude_birth' in locals() else get_yoy_style(None)

            crude_death_yoy_label = format_yoy_label(yoy_crude_death, '', decimals=1, use_sign=True) if 'yoy_crude_death' in locals() and yoy_crude_death is not None else "YoY change"
            crude_death_yoy_style = get_yoy_style(yoy_crude_death) if 'yoy_crude_death' in locals() else get_yoy_style(None)

            dependency_yoy_label = format_yoy_label(yoy_dependency, '', decimals=1, use_sign=True) if 'yoy_dependency' in locals() and yoy_dependency is not None else "YoY change"
            dependency_yoy_style = get_yoy_style(yoy_dependency) if 'yoy_dependency' in locals() else get_yoy_style(None)

            median_yoy_label = format_yoy_label(yoy_median_age, '', decimals=1, use_sign=True) if 'yoy_median_age' in locals() and yoy_median_age is not None else "YoY change"
            median_yoy_style = get_yoy_style(yoy_median_age) if 'yoy_median_age' in locals() else get_yoy_style(None)

            # 3 rows x 2 columns layout: set md=6 so 2 cards per row (12/6=2)
            mui.Grid(container=True, spacing=2)(
                # Total Population
                mui.Grid(item=True, xs=12, sm=6, md=6)(
                    mui.Card(style={"height": "105px", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()(
                            mui.Typography("Total Population", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{total_pop:.1f}", variant="h5", style={"color": "#2980b9", "fontWeight": "bold"}),
                                *[mui.Typography(pop_yoy_label, variant="body1", style=pop_yoy_style)] if selected_year != 1999 else [],
                            ),
                            mui.Typography("thousands", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Population Density
                mui.Grid(item=True, xs=12, sm=6, md=6)(
                    mui.Card(style={"height": "105px", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()(
                            mui.Typography("Population Density", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{density:.1f}", variant="h5", style={"color": "#9b59b6", "fontWeight": "bold"}),
                                *[mui.Typography(density_yoy_label, variant="body1", style=density_yoy_style)] if selected_year != 1999 else [],
                            ),
                            mui.Typography("'000 /km²", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Annual Growth Rate
                mui.Grid(item=True, xs=12, sm=6, md=6)(
                    mui.Card(style={"height": "105px", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()(
                            mui.Typography("Annual Growth Rate", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{annual_growth:.1f}", variant="h5", style={"color": "#3498db" if annual_growth >= 0 else "#e67e22", "fontWeight": "bold"}),
                                *[mui.Typography(annual_yoy_label, variant="body1", style=annual_yoy_style)] if selected_year != 1999 else [],
                            ),
                            mui.Typography("%", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Natural Population Growth Rate
                mui.Grid(item=True, xs=12, sm=6, md=6)(
                    mui.Card(style={"height": "105px", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()(
                            mui.Typography("Natural Growth Rate", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{natural_growth:.1f}", variant="h5", style={"color": "#f39c12", "fontWeight": "bold"}),
                                *[mui.Typography(natural_yoy_label, variant="body1", style=natural_yoy_style)] if selected_year != 1999 else [],
                            ),
                            mui.Typography("‰", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Crude Birth Rate
                mui.Grid(item=True, xs=12, sm=6, md=6)(
                    mui.Card(style={"height": "105px", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()(
                            mui.Typography("Crude Birth Rate", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{current_data.get('Crude birth rate', 0):.1f}", variant="h5", style={"color": "#27ae60", "fontWeight": "bold"}),
                                *[mui.Typography(crude_birth_yoy_label, variant="body1", style=crude_birth_yoy_style)] if selected_year != 1999 else [],
                            ),
                            mui.Typography("‰", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Crude Death Rate
                mui.Grid(item=True, xs=12, sm=6, md=6)(
                    mui.Card(style={"height": "105px", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()(
                            mui.Typography("Crude Death Rate", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{current_data.get('Crude mortality rate', 0):.1f}", variant="h5", style={"color": "#e74c3c", "fontWeight": "bold"}),
                                *[mui.Typography(crude_death_yoy_label, variant="body1", style=crude_death_yoy_style)] if selected_year != 1999 else [],
                            ),
                            mui.Typography("‰", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Dependency Ratio
                mui.Grid(item=True, xs=12, sm=6, md=6)(
                    mui.Card(style={"height": "105px", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()( 
                            mui.Typography("Dependency Ratio", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{dependency:.1f}" if dependency is not None else "N/A", variant="h5", style={"color": "#8e44ad", "fontWeight": "bold"}),
                                *[mui.Typography(dependency_yoy_label, variant="body1", style=dependency_yoy_style)] if selected_year != 1999 else [],
                            ),
                            mui.Typography("%", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Median Age
                mui.Grid(item=True, xs=12, sm=6, md=6)(
                    mui.Card(style={"height": "105px", "borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()( 
                            mui.Typography("Median Age", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{median_age:.1f}" if median_age is not None else "N/A", variant="h5", style={"color": "#2c3e50", "fontWeight": "bold"}),
                                *[mui.Typography(median_yoy_label, variant="body1", style=median_yoy_style)] if selected_year != 1999 else [],
                            ),
                            mui.Typography("yrs", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
            )
    # Right column: Gender/Sex distribution chart
    with col_age:
        st.markdown("**Gender Distribution**")

        # Get gender data
        male_pop = current_data.get('Male', 0)
        female_pop = current_data.get('Female', 0)
        total_pop = male_pop + female_pop

        # Calculate YoY changes for gender distribution
        yoy_male = None
        yoy_female = None
        if selected_year > 1999:
            prev_year = selected_year - 1
            prev_data = demographics[demographics['Year'] == prev_year]
            if not prev_data.empty:
                prev_data = prev_data.iloc[0]
                prev_male = prev_data.get('Male', 0)
                prev_female = prev_data.get('Female', 0)
                
                if pd.notna(prev_male) and prev_male > 0:
                    yoy_male = ((male_pop - prev_male) / prev_male) * 100
                if pd.notna(prev_female) and prev_female > 0:
                    yoy_female = ((female_pop - prev_female) / prev_female) * 100

        if total_pop > 0:
            # Calculate percentages
            male_pct = (male_pop / total_pop) * 100
            female_pct = (female_pop / total_pop) * 100

            fig_gender = go.Figure()

            # Toilet/restroom gender images (or fallback to emoji icons)
            def image_to_uri(path):
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                    encoded = base64.b64encode(data).decode('utf-8')
                    # Guess mime type from extension (basic)
                    ext = os.path.splitext(path)[1].lower()
                    mime = 'image/png'
                    if ext in ['.jpg', '.jpeg']:
                        mime = 'image/jpeg'
                    return f"data:{mime};base64,{encoded}"
                except Exception:
                    return None

            # Determine custom image paths 
            # Use project_root to find images
            male_custom_path = project_root / 'images' / 'male_custom.png'
            female_custom_path = project_root / 'images' / 'female_custom.png'
            # Fallback to default images if custom not provided
            male_default_path = project_root / 'images' / 'male.png'
            female_default_path = project_root / 'images' / 'female.png'

            male_uri = image_to_uri(male_custom_path) or image_to_uri(male_default_path)
            female_uri = image_to_uri(female_custom_path) or image_to_uri(female_default_path)

            if male_uri:
                fig_gender.add_layout_image(dict(
                    source=male_uri,
                    xref='x', yref='y',
                    x=0.25, y=0.5,
                    xanchor='center', yanchor='middle',
                    sizex=0.55, sizey=0.7,
                    sizing='contain',
                    layer='above'
                ))
            else:
                # Fallback to emoji
                fig_gender.add_trace(go.Scatter(
                    x=[0.25], y=[0.7], mode="text",
                    text=["🚹"], textfont=dict(size=60, color="#2c3e50", family="Arial"),
                    hoverinfo="skip", showlegend=False
                ))

            if female_uri:
                fig_gender.add_layout_image(dict(
                    source=female_uri,
                    xref='x', yref='y',
                    x=0.75, y=0.5,
                    xanchor='center', yanchor='middle',
                    sizex=0.55, sizey=0.7,
                    sizing='contain',
                    layer='above'
                ))
            else:
                fig_gender.add_trace(go.Scatter(
                    x=[0.75], y=[0.7], mode="text",
                    text=["🚺"], textfont=dict(size=60, color="#2c3e50", family="Arial"),
                    hoverinfo="skip", showlegend=False
                ))

            # Layout settings for clean, simple look
            fig_gender.update_xaxes(visible=False, range=[0, 1])
            fig_gender.update_yaxes(visible=False, range=[0, 1])
            fig_gender.update_layout(
                height=220,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor="white",
                plot_bgcolor="white",
                showlegend=False,
                title=dict(
                    text="Population by Gender",
                    x=0.5,
                    y=0.95,
                    xanchor="center",
                    yanchor="top",
                    font=dict(size=16, color="#2c3e50", family="Arial", weight="bold")
                )
            )

            st.plotly_chart(fig_gender, width="stretch", config={"displayModeBar": False})

            # Two cards under the male and female images
            col_male, col_female = st.columns(2)

            with col_male:
                yoy_male_html = ""
                if yoy_male is not None:
                    # Use +/ - sign for male YoY
                    yoy_label = format_yoy_label(yoy_male, '%', decimals=1, use_sign=True)
                    # Use rounded value for color decision so a printed Δ0.0 is neutral
                    rounded_yoy_male = round(yoy_male, 1)
                    if rounded_yoy_male > 0:
                        yoy_style = "background-color: #e8f5e8; color: #2e7d32;"
                    elif rounded_yoy_male < 0:
                        yoy_style = "background-color: #ffebee; color: #c62828;"
                    else:
                        yoy_style = "background-color: #f5f5f5; color: #616161;"
                    yoy_style += " border-radius: 12px; padding: 2px 8px; font-size: 13px; font-weight: bold; display: inline-block; margin-top: 6px;"
                    yoy_male_html = f"<div style='{yoy_style}'>{yoy_label}</div>"
                
                st.markdown(f"""
                <div style="background-color: #add8e6; padding: 12px; border-radius: 8px; min-height: 160px; display: flex; flex-direction: column; justify-content: center; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-weight: bold; color: #2c3e50; font-size: 16px; margin-bottom: 4px;">Male</div>
                    <div style="font-size: 26px; font-weight: 800; color: #2c3e50; margin: 2px 0;">{male_pct:.1f}%</div>
                    <div style="font-size: 15px; color: #555; margin: 2px 0;">{male_pop:.1f}K</div>
                    {yoy_male_html}
                </div>
                """, unsafe_allow_html=True)

            with col_female:
                yoy_female_html = ""
                if yoy_female is not None:
                    # Use +/ - sign for female YoY
                    yoy_label = format_yoy_label(yoy_female, '%', decimals=1, use_sign=True)
                    rounded_yoy_female = round(yoy_female, 1)
                    if rounded_yoy_female > 0:
                        yoy_style = "background-color: #e8f5e8; color: #2e7d32;"
                    elif rounded_yoy_female < 0:
                        yoy_style = "background-color: #ffebee; color: #c62828;"
                    else:
                        yoy_style = "background-color: #f5f5f5; color: #616161;"
                    yoy_style += " border-radius: 12px; padding: 2px 8px; font-size: 13px; font-weight: bold; display: inline-block; margin-top: 6px;"
                    yoy_female_html = f"<div style='{yoy_style}'>{yoy_label}</div>"
                
                st.markdown(f"""
                <div style="background-color: #ffb6c1; padding: 12px; border-radius: 8px; min-height: 160px; display: flex; flex-direction: column; justify-content: center; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-weight: bold; color: #2c3e50; font-size: 16px; margin-bottom: 4px;">Female</div>
                    <div style="font-size: 26px; font-weight: 800; color: #2c3e50; margin: 2px 0;">{female_pct:.1f}%</div>
                    <div style="font-size: 15px; color: #555; margin: 2px 0;">{female_pop:.1f}K</div>
                    {yoy_female_html}
                </div>
                """, unsafe_allow_html=True)

        else:
            st.info("⚠️ Gender data not available for this year")
    
    # Regional Statistics
    section_header("Regional Statistics", "🗺️")
    st.markdown("""
    <p style="color: #666; margin-top: -10px; margin-bottom: 12px; font-size: 0.95em;">Displaying Population Density by Region (Values in '000 per km²)</p>
    """, unsafe_allow_html=True)
    
    # Get regional data
    region_cols = {
        "Macao Peninsula": "Macao Peninsula a",
        "Taipa": "Taipa a",
        "Coloane": "Coloane a"
    }

    # Calculate regional densities and average
    region_densities = {}
    valid_densities = []

    for region_name, col_name in region_cols.items():
        density_val = current_data.get(col_name, None)
        if pd.notna(density_val) and density_val > 0:
            region_densities[region_name] = density_val
            valid_densities.append(density_val)

    # Calculate average density
    avg_density = sum(valid_densities) / len(valid_densities) if valid_densities else None

    # Compute region YoY values
    region_yoy = {}
    for region_name, col_name in region_cols.items():
        curr_val = current_data.get(col_name, None)
        yoy_val = None
        if prev_data is not None and pd.notna(prev_data.get(col_name)) and pd.notna(curr_val):
            try:
                # Compute absolute difference in density for regional YoY (not percent)
                yoy_val = curr_val - prev_data.get(col_name)
            except Exception:
                yoy_val = None
        region_yoy[region_name] = yoy_val

    # Create two columns: choropleth and metrics; adjust width to make the map area smaller
    col_map, col_metrics = st.columns([2.6, 1])

    with col_map:
        st.markdown("**Population Density Map**")
        if choropleth_available and regions_gdf is not None and geojson is not None and build_choropleth_figure is not None:
            try:
                fig_choropleth = build_choropleth_figure(
                    selected_year,
                    demographics,
                    regions_gdf,
                    geojson
                )
                # Render the choropleth with a constrained height to align with the metric cards
                st.plotly_chart(fig_choropleth, width="stretch", config={
                    "displayModeBar": True,
                    "displaylogo": False,
                    "scrollZoom": False
                })
            except Exception as e:
                st.warning(f"⚠️ Could not render choropleth: {e}")
        else:
            st.info("⚠️ Choropleth map not available")

    with col_metrics:
        st.markdown("**Regional Density**")

        with elements("regional_density_metrics"):
            # For years before or equal to 2007 regional YoY isn't available
            def region_yoy_label_and_style(region_name):
                val = region_yoy.get(region_name)
                if selected_year <= 2007:
                    return "N/A", get_yoy_style(None)
                if val is None:
                    return "YoY change", get_yoy_style(None)
                return format_yoy_label(val, '', decimals=1, use_sign=True), get_yoy_style(val)

            mp_label, mp_style = region_yoy_label_and_style('Macao Peninsula')
            taipa_label, taipa_style = region_yoy_label_and_style('Taipa')
            coloane_label, coloane_style = region_yoy_label_and_style('Coloane')
            mui.Grid(container=True, spacing=1)(
                # Macao Peninsula Density
                mui.Grid(item=True, xs=12)(
                    mui.Card(style={"height": "105px", "borderRadius": "8px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)", "marginBottom": "8px"})(
                        mui.CardContent()(
                            mui.Typography("Macao Peninsula", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography("N/A" if 1999 <= selected_year <= 2006 else f"{region_densities.get('Macao Peninsula', 0):.1f}", variant="h5", style={"color": "#2980b9", "fontWeight": "bold"}),
                                *[mui.Typography(mp_label, variant="body1", style=mp_style)] if selected_year > 2006 else [],
                            ),
                            mui.Typography("'000 /km²", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Taipa Density
                mui.Grid(item=True, xs=12)(
                    mui.Card(style={"height": "105px", "borderRadius": "8px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)", "marginBottom": "8px"})(
                        mui.CardContent()(
                            mui.Typography("Taipa", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography("N/A" if 1999 <= selected_year <= 2006 else f"{region_densities.get('Taipa', 0):.1f}", variant="h5", style={"color": "#27ae60", "fontWeight": "bold"}),
                                *[mui.Typography(taipa_label, variant="body1", style=taipa_style)] if selected_year > 2006 else [],
                            ),
                            mui.Typography("'000 /km²", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Coloane Density
                mui.Grid(item=True, xs=12)(
                    mui.Card(style={"height": "105px", "borderRadius": "8px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)", "marginBottom": "8px"})(
                        mui.CardContent()(
                            mui.Typography("Coloane", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography("N/A" if 1999 <= selected_year <= 2006 else f"{region_densities.get('Coloane', 0):.1f}", variant="h5", style={"color": "#e74c3c", "fontWeight": "bold"}),
                                *[mui.Typography(coloane_label, variant="body1", style=coloane_style)] if selected_year > 2006 else [],
                            ),
                            mui.Typography("'000 /km²", variant="caption", style={"color": "#555"}),
                        )
                    )
                ),
                # Population Density
                mui.Grid(item=True, xs=12)(
                    mui.Card(style={"height": "105px", "borderRadius": "8px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})(
                        mui.CardContent()(
                            mui.Typography("Overall Density", variant="body1", style={"color": "#7f8c8d"}),
                            mui.Box(style={"display": "flex", "alignItems": "center", "gap": "16px"})(
                                mui.Typography(f"{density:.1f}", variant="h5", style={"color": "#9b59b6", "fontWeight": "bold"}),
                                *[mui.Typography(format_yoy_label(yoy_density, '', decimals=1, use_sign=True), variant="body1", style=get_yoy_style(yoy_density))] if selected_year != 1999 else [],
                            ),
                            mui.Typography("'000 /km²", variant="caption", style={"color": "#555"}),
                        )
                    )
                )
            )

    # Alert for regional density data availability in choropleth
    if selected_year < 2007:
        st.info("⚠️ Regional population density data is available from 2007 onwards. The choropleth map shows overall density values for all regions during 1999-2006 for consistency.")
        # Add data-footnote for regional statistics (visible under the header for clarity)
    st.markdown("""
    <div style='display:flex; align-items:flex-start; gap:8px; margin-bottom:12px;'>
        <span class='badge badge-warning' style='padding:4px 10px; font-size:0.9em;'>Note</span>
        <div style='font-size:0.95em; color:#333; line-height:1.35;'>The calculation of population density by district does not include the land area of the Cotai reclamation zone, the Macao Port Administration Area on the artificial island of the Hong Kong-Zhuhai-Macao Bridge Zhuhai-Macao border crossing facilities, Zone A and C of the New District.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Charts Section - Population Distribution
    section_header(f"Population Distribution - {int(selected_year)}", "🧑‍🤝‍🧑")
    st.markdown("""
    <p style="color: #666; margin-top: -10px; margin-bottom: 12px; font-size: 0.95em;">Revealing the Age Composition of Macao’s Population</p>
    """, unsafe_allow_html=True)
    
    # Make the right column slightly wider so heatmap and charts can use more horizontal space — keep a 0.9:1.1 ratio
    col1, col2 = st.columns([0.9, 1.1])
    
    with col1:
        st.markdown("**Population Structure**")
        # Age group pie chart with total population in center
        age_0_14 = current_data.get('Below Age 15', 0)
        age_15_64 = (current_data.get('Age 15-24', 0) + current_data.get('Age 25-34', 0) + 
                     current_data.get('Age 35-44', 0) + current_data.get('Age 45-54', 0) + 
                     current_data.get('Age 55-64', 0))
        age_65_plus = current_data.get('Age 65 and above', 0)
        
        if pd.notna(age_0_14) and pd.notna(age_15_64) and pd.notna(age_65_plus):
            age_structure_df = pd.DataFrame([
                {"Age Group": "0-14 years", "Population": float(age_0_14), "Percentage": float(age_0_14)/total_pop*100 if total_pop > 0 else 0},
                {"Age Group": "15-64 years", "Population": float(age_15_64), "Percentage": float(age_15_64)/total_pop*100 if total_pop > 0 else 0},
                {"Age Group": "65 years and older", "Population": float(age_65_plus), "Percentage": float(age_65_plus)/total_pop*100 if total_pop > 0 else 0}
            ])
            
            # Create pie chart with total population in center
            # Use the provided Percentage column for slice labels (avoid relying on auto-calculated percent)
            fig_age_pie = go.Figure(data=[go.Pie(
                labels=[f"{row['Age Group']}" for _, row in age_structure_df.iterrows()],
                values=age_structure_df['Population'],
                customdata=age_structure_df[['Percentage']].values,
                hole=0.6,  # Create donut chart for center text
                marker_colors=['#FF9999', '#66B2FF', '#99FF99'],
                # Display the stored percentage value with 1 decimal place inside slices
                textinfo='none',
                texttemplate='%{customdata[0]:.1f}%',
                textfont=dict(color='black', size=14, family='Arial, bold'),
                textposition='inside',
                insidetextorientation='radial',
                hovertemplate='Age Group: %{label}<br>Percentage: %{customdata[0]:.1f}%<br>Population: %{value:.1f}K<extra></extra>'
            )])
            
            # Add total population text in center
            fig_age_pie.add_annotation(
                text=f"<b>{total_pop:.1f}K</b><br>Total<br>Population",
                x=0.5, y=0.5,
                font=dict(size=16, color="#2c3e50"),
                showarrow=False,
                xref="paper", yref="paper"
            )
            
            fig_age_pie.update_layout(
                height=350,
                showlegend=True,
                legend=dict(
                    font=dict(
                        color='white',
                        size=12,
                        family='Arial, bold'
                    ),
                    bgcolor='rgba(0,0,0,0.7)',
                    bordercolor='white',
                    borderwidth=1,
                    x=1.05,
                    y=0.5,
                    xanchor='left',
                    yanchor='middle'
                ),
                margin=dict(l=20, r=100, t=30, b=20),
                paper_bgcolor="white",
                plot_bgcolor="white"
            )
            st.plotly_chart(fig_age_pie, width="stretch", config={"displayModeBar": False})
    
    with col2:
        st.markdown("**Age Group distribution Heatmap (by percentage)**")
        
        # Age distribution bar chart
        age_cols = ['Below Age 15', 'Age 15-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-64', 'Age 65 and above']
        age_data = []
        for col in age_cols:
            if col in current_data.index:
                val = current_data[col]
                if pd.notna(val):
                    age_data.append({"Age Group": col.replace("Age ", "").replace("Below ", "<"), "Population (in thousands)": float(val)})
        
        if age_data:
            # Build a heatmap matrix: Years x Age Groups
            # We prefer to use the detailed pyramid file for better age buckets, if available
            try:
                # Grouping bins mapping from the pyramid csv age groups
                groups = {
                    '0-14': ['0–4', '5–9', '10–14'],
                    '15-24': ['15–19', '20–24'],
                    '25-34': ['25–29', '30–34'],
                    '35-44': ['35–39', '40–44'],
                    '45-54': ['45–49', '50–54'],
                    '55-64': ['55–59', '60–64'],
                    '65-74': ['65–69', '70–74'],
                    '75+': ['75+']
                }

                years = sorted(list({int(c.split('_')[-1]) for c in pyramid.columns if c.startswith('M_')}))

                # Build z (percentage) and customdata (population K) arrays
                z = []  # percent
                customdata = []  # population in K
                for group_name, age_rows in groups.items():
                    row_percent = []
                    row_pop = []
                    for yr in years:
                        # Sum male+female for the relevant age_rows
                        pop_k = 0.0
                        for seg in age_rows:
                            seg_row = pyramid[pyramid['Age Group'] == seg]
                            if not seg_row.empty:
                                mcol = f"M_{yr}"
                                fcol = f"F_{yr}"
                                if mcol in seg_row.columns and fcol in seg_row.columns:
                                    try:
                                        pop_k += float(seg_row[mcol].values[0]) + float(seg_row[fcol].values[0])
                                    except Exception:
                                        pop_k += 0.0
                        # Get total population for the year from demographics (in thousands)
                        total_row = demographics[demographics['Year'] == float(yr)]
                        if not total_row.empty:
                            total_k = float(total_row['Total population'].values[0])
                        else:
                            total_k = 0.0
                        percent = (pop_k / total_k * 100) if total_k and not pd.isna(total_k) else 0.0
                        row_percent.append(percent)
                        row_pop.append(pop_k)
                    z.append(row_percent)
                    customdata.append(row_pop)

                # Convert to lists for plotting
                years_str = [int(y) for y in years]
                age_labels = list(groups.keys())

                # Heatmap expects z as 2D list; customdata should match shape
                # Create customdata array of shape len(age_labels) x len(years) with pop values
                cd = [[customdata[r][c] for c in range(len(years_str))] for r in range(len(age_labels))]

                fig_age_heat = go.Figure(data=go.Heatmap(
                    x=years_str,
                    y=age_labels,
                    z=z,
                    customdata=cd,
                    colorscale='Blues',
                    zmin=0,
                    zmax=max([max(row) for row in z]) if z else 100,
                    colorbar=dict(
                        # Keep the built-in colorbar title empty — we'll display a left-side vertical title with an annotation
                        title={'text': ''},
                        thickness=12,  # default-like thickness for better readability
                        len=0.82,      # long enough to aid reading
                        x=1.06,        # move colorbar further away from the heatmap
                        y=0.5,
                        outlinewidth=0,
                        ticks='outside'
                    ),
                    hovertemplate='Age Group: %{y}<br>Population: %{customdata:.1f}K<br>Percentage: %{z:.1f}%<extra></extra>'
                ))

                fig_age_heat.update_layout(
                    height=450,
                    xaxis_title='Year',
                    yaxis_title='Age Group',
                    # Adjust margin and heatmap domain so it widens inside the column and leaves small room for colorbar
                    margin=dict(l=30, r=120, t=40, b=60),
                    # Use more of the horizontal space for the heatmap (but keep room for a vertical colorbar positioned outside)
                    xaxis=dict(domain=[0, 0.94]),
                    paper_bgcolor='white',
                    plot_bgcolor='white'
                )

                # Add a vertical annotation positioned to the left of the colorbar to emulate a left-side title
                # Note: use xref='paper' to position relative to plot area; adjust x coordinate to be slightly left of colorbar x
                try:
                    fig_age_heat.add_annotation(
                        x=1.02, y=0.5, xref='paper', yref='paper',
                        text='Population (%)', showarrow=False, textangle=-90,
                        font=dict(size=11, color='#333'),
                        xanchor='left', yanchor='middle'
                    )
                except Exception:
                    # Annotations may fail for some plotly versions; ignore if not supported
                    pass

                # Force integer ticks and clamp x range slightly to show full outer cells
                minyr = int(min(years_str))
                maxyr = int(max(years_str))
                fig_age_heat.update_xaxes(type='linear', tick0=minyr, dtick=1, tickformat='.0f', range=[minyr-0.5, maxyr+0.5])

                # Display the heatmap inside the right-hand column; keep width='stretch' so it scales within column
                st.plotly_chart(fig_age_heat, width='stretch', config={'displayModeBar': False})
            except Exception as e:
                # Fallback to original bar if pyramid file missing or error
                age_df = pd.DataFrame(age_data)
                gradient_colors = ['#B3D9FF', '#80BFFF', '#4DA6FF', '#1A8CFF', '#0066CC', '#003D7A', '#001A33']
                fig_age = px.bar(age_df, x='Age Group', y='Population (in thousands)', text=age_df['Population (in thousands)'])
                fig_age.update_traces(marker=dict(color=gradient_colors[:len(age_df)]), textposition='outside', texttemplate='%{y:.1f}', hovertemplate='Age Group: %{x}<br>Population: %{y:.1f}K<extra></extra>')
                fig_age.update_layout(height=450, showlegend=False, xaxis_tickangle=-45, yaxis_title='Population (in thousands)', margin=dict(l=40, r=40, t=40, b=60), paper_bgcolor='white', plot_bgcolor='white')
                fig_age.update_yaxes(tickvals=[0, 25, 50, 75, 100, 125, 150])
                # Fallback chart - display inside column
                st.plotly_chart(fig_age, width='stretch', config={'displayModeBar': False})
        else:
            st.info("⚠️ Age group data not available for this year")

    # ---------- Age Dependency Ratio chart (Child + Senior + Total) ----------
    # Build time series from the demographics DF
    try:
        dep_df = demographics[['Year', 'Below Age 15', 'Age 15-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-64', 'Age 65 and above']].dropna(subset=['Year'])
        # Combine 15-64 as working age
        dep_df['Working Age (15-64)'] = dep_df[['Age 15-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-64']].sum(axis=1)
        dep_df['Child Dependency'] = dep_df['Below Age 15'] / dep_df['Working Age (15-64)'] * 100
        dep_df['Senior Dependency'] = dep_df['Age 65 and above'] / dep_df['Working Age (15-64)'] * 100
        dep_df['Total Dependency'] = dep_df['Child Dependency'] + dep_df['Senior Dependency']

        # Use full available range for the chart (e.g., 1999-2024)
        # If you want to cap to the CSV range explicitly, use min/max in the file
        chart_df = dep_df.sort_values('Year').copy()

        # Build the stacked bar + line chart
        fig_dependency = go.Figure()
        fig_dependency.add_trace(go.Bar(
            x=chart_df['Year'],
            y=chart_df['Child Dependency'],
            name='Child dependency',
            marker_color='#ff7f0e',
            hovertemplate='Child dependency: %{y:.1f}%<extra></extra>'
        ))
        fig_dependency.add_trace(go.Bar(
            x=chart_df['Year'],
            y=chart_df['Senior Dependency'],
            name='Senior dependency',
            marker_color='#bdbdbd',
            hovertemplate='Senior dependency: %{y:.1f}%<extra></extra>'
        ))

        # Line trace for total dependency (same scale)
        fig_dependency.add_trace(go.Scatter(
            x=chart_df['Year'],
            y=chart_df['Total Dependency'],
            name='Age dependency',
            mode='lines+markers',
            line=dict(color='#2a6fda', width=2),
            marker=dict(size=7),
            hovertemplate='Total dependency: %{y:.1f}%<extra></extra>'
        ))

        fig_dependency.update_layout(
            barmode='stack',
            height=420,
            title=dict(text=f"Age Dependency Ratios (Child + Senior) - {int(chart_df['Year'].min())}-{int(chart_df['Year'].max())}", x=0.5, xanchor='center'),
            xaxis_title='Year',
            yaxis_title='Dependency ratio (per 100 working-age people)',
            margin=dict(l=40, r=40, t=60, b=60),
            paper_bgcolor='white',
            plot_bgcolor='rgba(240,240,240,0.3)',
            hovermode='x unified'
        )

        # Position legend inside the plot area, top-right, with a subtle grey background
        fig_dependency.update_layout(legend=dict(
            title='',
            orientation='v',
            x=0.98,
            y=0.98,
            xanchor='right',
            yanchor='top',
            bgcolor='rgba(200,200,200,0.15)',
            bordercolor='rgba(0,0,0,0.08)',
            borderwidth=1,
            font=dict(color='#222', size=11)
        ))

        # Keep consistent y-axis range based on max total+small margin to avoid jumps
        max_total = chart_df['Total Dependency'].max() if not chart_df['Total Dependency'].isna().all() else 60
        fig_dependency.update_yaxes(range=[0, max(60, (int(max_total) + 8))])
        # Show yearly ticks on x-axis and ensure years are integers
        try:
            minyr = int(chart_df['Year'].min())
            maxyr = int(chart_df['Year'].max())
            # Use explicit tick values (all integer years in the series) so Plotly doesn't add extra side ticks
            years = list(chart_df['Year'].astype(int).unique())
            # Expand the left/right range by half a year so the bars at the ends are fully visible
            left = minyr - 0.5
            right = maxyr + 0.5
            fig_dependency.update_xaxes(
                type='linear',
                range=[left, right],
                tick0=minyr,
                dtick=1,
                tickvals=years,
                tickformat='.0f'
            )
        except Exception:
            pass

        # Annotate the first and last total points (as in the sample)
        if not chart_df.empty:
            first_total = chart_df['Total Dependency'].iloc[0]
            last_total = chart_df['Total Dependency'].iloc[-1]
            first_year = int(chart_df['Year'].iloc[0])
            last_year = int(chart_df['Year'].iloc[-1])
            fig_dependency.add_annotation(x=first_year, y=first_total, text=f"{first_total:.0f}", showarrow=False, yshift=8, font=dict(size=11, color='#2a6fda'))
            fig_dependency.add_annotation(x=last_year, y=last_total, text=f"{last_total:.0f}", showarrow=False, yshift=8, font=dict(size=12, color='#2a6fda', weight='bold'))

        st.plotly_chart(fig_dependency, width="stretch", config={"displayModeBar": False})
    except Exception as e:
        # If something goes wrong with the computation, show a gentle message
        st.info("⚠️ Could not build dependency ratio chart: " + str(e))

    st.markdown("---")

    # ========== NEW TRENDS GRAPH ==========
    section_header("Population Trends Over Time", "📅")
    st.markdown("""
    <p style="color: #666; margin-top: -10px; margin-bottom: 12px; font-size: 0.95em;">Visualizing 25 years of demographic transition in Macao</p>
    """, unsafe_allow_html=True)
    
    # Create line chart for population trends
    # Include birth and death rates for trend analysis
    trends_data = demographics[['Year', 'Total population', 'Male', 'Female', 'Crude birth rate', 'Crude mortality rate']].dropna(subset=['Year', 'Total population'])
    
    fig_trends = go.Figure()
    
    fig_trends.add_trace(go.Scatter(
        x=trends_data['Year'],
        y=trends_data['Total population'],
        name='Total Population (K)',
        mode='lines+markers',
        line=dict(color='#2980b9', width=3),
        marker=dict(size=6),
        hovertemplate='Total Population: %{y:.1f}K<extra></extra>'
    ))
    
    fig_trends.add_trace(go.Scatter(
        x=trends_data['Year'],
        y=trends_data['Male'],
        name='Male Population (K)',
        mode='lines',
        line=dict(color='#5DADE2', width=2, dash='dash'),
        hovertemplate='Male Population: %{y:.1f}K<extra></extra>'
    ))
    
    fig_trends.add_trace(go.Scatter(
        x=trends_data['Year'],
        y=trends_data['Female'],
        name='Female Population (K)',
        mode='lines',
        line=dict(color='#F1948A', width=2, dash='dash'),
        hovertemplate='Female Population: %{y:.1f}K<extra></extra>'
    ))

    # Add Birth Rate trend as a secondary y-axis
    if 'Crude birth rate' in trends_data.columns:
        fig_trends.add_trace(go.Scatter(
            x=trends_data['Year'],
            y=trends_data['Crude birth rate'],
            name='Birth Rate (per 1,000)',
            mode='lines',
            yaxis='y2',
            line=dict(color='#27ae60', width=2, dash='dot'),
            hovertemplate='Birth Rate: %{y:.1f} per 1,000<extra></extra>'
        ))
    
    # Add Death Rate trend as a secondary y-axis
    if 'Crude mortality rate' in trends_data.columns:
        fig_trends.add_trace(go.Scatter(
            x=trends_data['Year'],
            y=trends_data['Crude mortality rate'],
            name='Death Rate (per 1,000)',
            mode='lines',
            yaxis='y2',
            line=dict(color='#e74c3c', width=2, dash='dot'),
            hovertemplate='Death Rate: %{y:.1f} per 1,000<extra></extra>'
        ))
    
    # Add vertical line for current year
    fig_trends.add_vline(
        x=selected_year,
        line_dash="dot",
        line_color="red",
        annotation_text=f"  {int(selected_year)}",
        annotation_position="top right"
    )
    
    fig_trends.update_layout(
        height=400,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor="white",
        plot_bgcolor="rgba(240,240,240,0.3)",
        xaxis_title="Year",
        yaxis_title="Population (in Thousands)",
        yaxis2=dict(
            title="Rates (per 1,000 people)",
            overlaying='y',
            side='right'
        ),
        font=dict(size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    st.plotly_chart(fig_trends, width="stretch", config={"displayModeBar": True})

    st.markdown("---")

    # Non-Resident Workers Section
    section_header(f"Non-Resident Workers - {int(selected_year)}", "👥")
    st.markdown("""
    <p style="color: #666; margin-top: -10px; margin-bottom: 12px; font-size: 0.95em;">Mapping the Source Regions Behind Macao’s Non-Resident Workers</p>
    """, unsafe_allow_html=True)
    
    if selected_year < 2008:
        st.info("⚠️ Regional breakdown data available from 2008 onwards")
    else:
        region_cols = {
            'Chinese mainland': 'Chinese mainland',
            'Philippines': 'Philippines',
            'Vietnam': 'Vietnam',
            'Others': 'Others'
        }
        
        # Create two columns for the charts — set to 1:1 ratio as requested
        col1, col2 = st.columns([1, 1])
        
        # Left column: Pie chart (existing)
        with col1:
            st.markdown("**Worker Distribution by Region**")
            region_data = []
            region_colors = {'Chinese mainland': '#3498db', 'Philippines': '#e74c3c', 'Vietnam': '#2ecc71', 'Others': '#f39c12'}
            
            for col, label in region_cols.items():
                if col in current_data.index:
                    val = current_data[col]
                    if pd.notna(val):
                        region_data.append({"Region": label, "Workers": float(val)})
                elif col == 'Others':
                    # Calculate Others as total - china - philippines - vietnam
                    total_workers = current_data.get('Non-resident workers total', 0)
                    china = current_data.get('Chinese mainland', 0)
                    philippines = current_data.get('Philippines', 0)
                    vietnam = current_data.get('Vietnam', 0)
                    
                    if pd.notna(total_workers):
                        others_val = total_workers - (china if pd.notna(china) else 0) - (philippines if pd.notna(philippines) else 0) - (vietnam if pd.notna(vietnam) else 0)
                        if others_val > 0:
                            region_data.append({"Region": label, "Workers": float(others_val)})
            
            if region_data:
                region_df = pd.DataFrame(region_data)
                colors_list = [region_colors.get(row['Region'], '#95a5a6') for _, row in region_df.iterrows()]
                fig_pie = px.pie(
                    region_df, 
                    names='Region', 
                    values='Workers',
                    color_discrete_sequence=colors_list
                )
                fig_pie.update_traces(
                    textposition='auto',
                    textfont=dict(color='white', size=12, family='Arial')
                )
                fig_pie.update_layout(
                    height=350,
                    showlegend=True,
                    legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.9,
                    xanchor="right",
                    x=1.45,
                    font=dict(
                        size=12
                    )
                ),
                margin=dict(l=40, r=80, t=15, b=10),
                    paper_bgcolor="white",
                    plot_bgcolor="white"
                )
                st.plotly_chart(fig_pie, width="stretch", config={"displayModeBar": False})
        
        # Right column: New trend bar chart
        with col2:
            st.markdown("**Year-Over-Year Shift in Worker Origins**")
            
            # Calculate year-over-year changes
            if selected_year > 2008:  # Need previous year data
                prev_year = selected_year - 1
                prev_data = demographics[demographics['Year'] == prev_year]
                
                if not prev_data.empty:
                    prev_data = prev_data.iloc[0]
                    trend_data = []
                    
                    for col, label in region_cols.items():
                        if col in current_data.index and col in prev_data.index:
                            curr_val = current_data[col] if pd.notna(current_data[col]) else 0
                            prev_val = prev_data[col] if pd.notna(prev_data[col]) else 0
                            
                            # Calculate percentage change
                            if prev_val > 0 and curr_val >= 0:
                                change = ((curr_val - prev_val) / prev_val) * 100
                                # Format with + sign for positive changes
                                formatted_change = (f"+{change:.1f}%" if change > 0 else f"{change:.1f}%")
                                trend_data.append({
                                    "Region": label,
                                    "Change (%)": change,  # Keep numeric for sorting/coloring
                                    "Change Label": formatted_change  # Use formatted string for display
                                })
                        elif col == 'Others':
                            # Calculate Others for current and previous year
                            curr_total = current_data.get('Non-resident workers total', 0)
                            curr_china = current_data.get('Chinese mainland', 0)
                            curr_philippines = current_data.get('Philippines', 0)
                            curr_vietnam = current_data.get('Vietnam', 0)
                            
                            prev_total = prev_data.get('Non-resident workers total', 0)
                            prev_china = prev_data.get('Chinese mainland', 0)
                            prev_philippines = prev_data.get('Philippines', 0)
                            prev_vietnam = prev_data.get('Vietnam', 0)
                            
                            if pd.notna(curr_total) and pd.notna(prev_total):
                                curr_others = curr_total - (curr_china if pd.notna(curr_china) else 0) - (curr_philippines if pd.notna(curr_philippines) else 0) - (curr_vietnam if pd.notna(curr_vietnam) else 0)
                                prev_others = prev_total - (prev_china if pd.notna(prev_china) else 0) - (prev_philippines if pd.notna(prev_philippines) else 0) - (prev_vietnam if pd.notna(prev_vietnam) else 0)
                                
                                if prev_others > 0 and curr_others >= 0:
                                    change = ((curr_others - prev_others) / prev_others) * 100
                                    # Format with + sign for positive changes
                                    formatted_change = (f"+{change:.1f}%" if change > 0 else f"{change:.1f}%")
                                    trend_data.append({
                                        "Region": label,
                                        "Change (%)": change,  # Keep numeric for sorting/coloring
                                        "Change Label": formatted_change  # Use formatted string for display
                                    })
                    
                    if trend_data:
                        trend_df = pd.DataFrame(trend_data)
                        
                        # Create horizontal bar chart
                        fig_trend = px.bar(
                            trend_df,
                            x="Change (%)",
                            y="Region",
                            orientation='h',
                            color="Region",
                            color_discrete_map=region_colors,
                            text='Change Label',
                            hover_data={'Change (%)': False, 'Change Label': False}
                        )
                        
                        fig_trend.update_traces(
                            marker_line_width=0.5,
                            marker_line_color='rgb(0,0,0,0.2)',
                            cliponaxis=False,
                            textposition='outside',
                            texttemplate='%{text}',
                            textfont=dict(size=12, color='#333'),
                            hovertemplate='Region=%{y}<br>Change=%{text}<extra></extra>'
                        )
                        
                        # Determine separate positive/negative extents so the axis isn't unnecessarily symmetric
                        pos_max = trend_df.loc[trend_df['Change (%)'] > 0, 'Change (%)'].max() if not trend_df.empty else 0
                        neg_max = abs(trend_df.loc[trend_df['Change (%)'] < 0, 'Change (%)'].min()) if not trend_df.empty else 0
                        max_change = max(pos_max, neg_max, 1)
                        # Add small padding proportional to values to avoid labels being cut off but avoid huge whitespace
                        right_padding = max(0.8, pos_max * 0.18) if pos_max > 0 else 1.0
                        left_padding = max(0.8, neg_max * 0.18) if neg_max > 0 else 1.0
                        # Compute explicit asymmetric x-axis range so empty side doesn't waste visual space
                        x_range_left = round(neg_max + left_padding, 1)
                        x_range_right = round(pos_max + right_padding, 1)
                        
                        fig_trend.update_layout(
                            height=420,
                            showlegend=False,
                            xaxis_title="Percentage Change",
                            yaxis_title="",
                            xaxis_range=[-x_range_left, x_range_right],
                            margin=dict(l=140, r=120, t=25, b=30),  
                            paper_bgcolor="white",
                            plot_bgcolor="white"
                        )
                        
                        st.plotly_chart(fig_trend, width='stretch', config={"displayModeBar": False})
                    else:
                        st.info("⚠️ No data available for trend analysis")
                else:
                    st.info("⚠️ Previous year data not available for trend analysis")
            else:
                st.info("⚠️ Year-over-year comparison available from 2009 onwards")

    # Worker KPI Cards Grid
    
    # Create 1x5 grid with larger first card
    kpi_cols = st.columns([2, 1, 1, 1, 1])
    
    # Total workers card (larger)
    with kpi_cols[0]:
        total_workers = current_data.get('Non-resident workers total', 0)
        if pd.notna(total_workers):
            total_k = total_workers / 1000
            st.markdown(f"""
            <div class='stat-box' style="
                background: linear-gradient(135deg, rgba(52, 152, 219, 0.12) 0%, rgba(41, 128, 185, 0.12) 100%);
                border-left-color: #3498db;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-weight: 800; color: #1e3a5f; margin-bottom: 15px; font-size: 1.2em;">👥 Total Non-Resident Workers</div>
                <div style="font-size: 2.5em; font-weight: 900; color: #2c3e50; line-height: 1;">{total_k:.1f}K</div>
                {('''<div style="font-size: 0.95em; background: ''' + (workers_yoy_style.get('background', 'rgba(240,240,240,0.4)') if 'workers_yoy_style' in locals() else 'rgba(240,240,240,0.4)') + '''; color: ''' + (workers_yoy_style.get('color', '#555') if 'workers_yoy_style' in locals() else '#555') + '''; padding: 4px 10px; border-radius: 18px; display:inline-block; margin-top: 6px; font-weight: 700;">''' + (workers_yoy_label if ('workers_yoy_label' in locals() and workers_yoy_label != 'YoY change') else '') + '''</div>''' if selected_year != 1999 else '')}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='stat-box' style="
                background: linear-gradient(135deg, rgba(52, 152, 219, 0.12) 0%, rgba(41, 128, 185, 0.12) 100%);
                border-left-color: #3498db;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-weight: 800; color: #1e3a5f; margin-bottom: 15px; font-size: 1.2em;">👥 Total Non-Resident Workers</div>
                <div style="font-size: 2.5em; font-weight: 900; color: #7f8c8d; line-height: 1;">N/A</div>
                {('''<div style="font-size: 0.95em; background: ''' + (workers_yoy_style.get('background', 'rgba(240,240,240,0.4)') if 'workers_yoy_style' in locals() else 'rgba(240,240,240,0.4)') + '''; color: ''' + (workers_yoy_style.get('color', '#555') if 'workers_yoy_style' in locals() else '#555') + '''; padding: 4px 10px; border-radius: 18px; display:inline-block; margin-top: 6px; font-weight: 700;">''' + (workers_yoy_label if ('workers_yoy_label' in locals() and workers_yoy_label != 'YoY change') else '') + '''</div>''' if selected_year != 1999 else '')}
            </div>
            """, unsafe_allow_html=True)
    
    # Region cards
    regions = ['Chinese mainland', 'Philippines', 'Vietnam', 'Others']
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    
    for i, (region, color) in enumerate(zip(regions, colors)):
        with kpi_cols[i+1]:
            if selected_year <= 2007:
                # Show N/A for 1999-2007 since limited data availability for regional breakdown
                st.markdown(f"""
                <div class='stat-box' style="
                    background: linear-gradient(135deg, rgba(52, 152, 219, 0.08) 0%, rgba(41, 128, 185, 0.08) 100%);
                    border-left-color: {color};
                    padding: 15px;
                    text-align: center;
                    margin-top: 40px;
                ">
                    <div style="font-weight: 700; color: #1e3a5f; margin-bottom: 10px; font-size: 0.9em;">{region}</div>
                    <div style="font-size: 1.8em; font-weight: 800; color: #7f8c8d; line-height: 1;">N/A</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                if region == 'Others':
                    # Calculate Others
                    total = current_data.get('Non-resident workers total', 0)
                    china = current_data.get('Chinese mainland', 0)
                    philippines = current_data.get('Philippines', 0)
                    vietnam = current_data.get('Vietnam', 0)
                    val = total - (china if pd.notna(china) else 0) - (philippines if pd.notna(philippines) else 0) - (vietnam if pd.notna(vietnam) else 0)
                else:
                    val = current_data.get(region, 0)
                
                if pd.notna(val) and val > 0:
                    val_k = val / 1000
                    st.markdown(f"""
                    <div class='stat-box' style="
                        background: linear-gradient(135deg, rgba(52, 152, 219, 0.08) 0%, rgba(41, 128, 185, 0.08) 100%);
                        border-left-color: {color};
                        padding: 15px;
                        text-align: center;
                        margin-top: 40px;
                    ">
                        <div style="font-weight: 700; color: #1e3a5f; margin-bottom: 10px; font-size: 0.9em;">{region}</div>
                        <div style="font-size: 1.8em; font-weight: 800; color: {color}; line-height: 1;">{val_k:.1f}K</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='stat-box' style="
                        background: linear-gradient(135deg, rgba(52, 152, 219, 0.08) 0%, rgba(41, 128, 185, 0.08) 100%);
                        border-left-color: {color};
                        padding: 15px;
                        text-align: center;
                        margin-top: 40px;
                    ">
                        <div style="font-weight: 700; color: #1e3a5f; margin-bottom: 10px; font-size: 0.9em;">{region}</div>
                        <div style="font-size: 1.8em; font-weight: 800; color: #7f8c8d; line-height: 1;">N/A</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ========== SUMMARY FOOTER ==========
    section_header(f"Summary Report for {int(selected_year)}", "📋")
    
    # Ensure summary variables exist (leave no dependence on previous local variables)
    median_age = current_data.get('Median age', None)
    dependency = current_data.get('Dependency ratio', None)
    # Recompute YoY for summary to avoid scope issues
    yoy_dependency = None
    yoy_median_age = None
    if prev_data is not None:
        if pd.notna(prev_data.get('Dependency ratio')) and pd.notna(dependency):
            yoy_dependency = dependency - prev_data['Dependency ratio']
        if pd.notna(prev_data.get('Median age')) and pd.notna(median_age):
            yoy_median_age = median_age - prev_data['Median age']
    summary_col1, summary_col2 = st.columns(2)
    summary_col3, summary_col4 = st.columns(2)
    
    with summary_col1:
        male_female_ratio = male_pop / female_pop if female_pop > 0 else 0
        # Safely calculate percentages for male and female relative to total
        _tot_sum = total_pop if (total_pop is not None and total_pop > 0) else 0
        male_pct = (male_pop / _tot_sum * 100) if _tot_sum > 0 else None
        female_pct = (female_pop / _tot_sum * 100) if _tot_sum > 0 else None
        
        # Additional population metrics to show under the ratio
        _annual_growth_val = current_data.get('Annual growth rate')
        _annual_growth = _annual_growth_val if (_annual_growth_val is not None and pd.notna(_annual_growth_val)) else None
        _crude_birth_val = current_data.get('Crude birth rate')
        _crude_birth = _crude_birth_val if (_crude_birth_val is not None and pd.notna(_crude_birth_val)) else None
        _crude_death_val = current_data.get('Crude mortality rate')
        _crude_death = _crude_death_val if (_crude_death_val is not None and pd.notna(_crude_death_val)) else None

        # Get non-resident workers for summary display, fall back to None for 'N/A'
        _non_res_val = current_data.get('Non-resident workers total')
        _non_res = _non_res_val if (_non_res_val is not None and pd.notna(_non_res_val)) else None
        # Display non-resident workers in thousands (K) by dividing by 1000
        _non_res_k = (_non_res / 1000.0) if _non_res is not None else None
        st.markdown(f"""
        <div class='stat-box' style="
            background: linear-gradient(135deg, rgba(230, 126, 34, 0.08) 0%, rgba(241, 196, 15, 0.08) 100%);
            border-left-color: #e67e22;
        ">
            <div style="font-weight: 800; color: #1e3a5f; margin-bottom: 12px; font-size: 1.1em;">👨‍👩‍👧‍👦 Population</div>
            <div style="font-size: 0.95em; line-height: 1.8; color: #555;">
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #e67e22;">●</span> Total Population: {total_pop:.1f}K</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #e67e22;">●</span> Male: {male_pop:.1f}K ({(f"{male_pct:.1f}%" if male_pct is not None else "N/A")}) | Female: {female_pop:.1f}K ({(f"{female_pct:.1f}%" if female_pct is not None else "N/A")})</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #e67e22;">●</span> Annual growth rate: {(f"{_annual_growth:.1f}%" if _annual_growth is not None else "N/A")} | Birth rate: {(f"{_crude_birth:.1f}‰" if _crude_birth is not None else "N/A")} | Death rate: {(f"{_crude_death:.1f}‰" if _crude_death is not None else "N/A")}</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #e67e22;">●</span> Non-resident workers: {(f"{_non_res_k:.1f}K" if _non_res_k is not None else "N/A")}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col2:
        # Compute age group percentages and ensure safe defaults
        _tot = total_pop if (total_pop is not None and total_pop > 0) else 0
        _c_pct = (float(current_data.get('Below Age 15', 0)) / _tot * 100) if _tot > 0 else None
        _w_val = (current_data.get('Age 15-24', 0) + current_data.get('Age 25-34', 0) +
                  current_data.get('Age 35-44', 0) + current_data.get('Age 45-54', 0) +
                  current_data.get('Age 55-64', 0))
        _w_pct = (float(_w_val) / _tot * 100) if _tot > 0 else None
        _o_pct = (float(current_data.get('Age 65 and above', 0)) / _tot * 100) if _tot > 0 else None
        st.markdown(f"""
        <div class='stat-box' style="
            background: linear-gradient(135deg, rgba(39, 174, 96, 0.08) 0%, rgba(46, 204, 113, 0.08) 100%);
            border-left-color: #27ae60;
        ">
            <div style="font-weight: 800; color: #1e3a5f; margin-bottom: 12px; font-size: 1.1em;">👥 Age Structure</div>
            <div style="font-size: 0.95em; line-height: 1.8; color: #555;">
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #27ae60;">●</span> Median Age: {(f"{median_age:.1f} years" if median_age is not None else "N/A")}</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #27ae60;">●</span> Dependency Ratio: {(f"{dependency:.1f}%" if dependency is not None else "N/A")}</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #27ae60;">●</span> Children (0-14): {(f"{_c_pct:.1f}%" if _c_pct is not None else "N/A")} | Working age (15-64): {(f"{_w_pct:.1f}%" if _w_pct is not None else "N/A")} | Older people (65+): {(f"{_o_pct:.1f}%" if _o_pct is not None else "N/A")}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col3:
        # Compute overall density if needed; show at top of the region density card
        # Use None for missing data so we can display 'N/A'
        overall_density_val = current_data.get('Population density')
        overall_density = overall_density_val if (overall_density_val is not None and pd.notna(overall_density_val)) else None
        macao_peninsula_raw = current_data.get('Macao Peninsula a')
        macao_peninsula_density = macao_peninsula_raw if (macao_peninsula_raw is not None and pd.notna(macao_peninsula_raw)) else None
        taipa_raw = current_data.get('Taipa a')
        taipa_density = taipa_raw if (taipa_raw is not None and pd.notna(taipa_raw)) else None
        coloane_raw = current_data.get('Coloane a')
        coloane_density = coloane_raw if (coloane_raw is not None and pd.notna(coloane_raw)) else None
        st.markdown(f"""
        <div class='stat-box' style="
            background: linear-gradient(135deg, rgba(41, 128, 185, 0.08) 0%, rgba(52, 152, 219, 0.08) 100%);
            border-left-color: #2980b9;
        ">
            <div style="font-weight: 800; color: #1e3a5f; margin-bottom: 12px; font-size: 1.1em;">🏙️ Regional Density</div>
            <div style="font-size: 0.95em; line-height: 1.8; color: #555;">
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #2980b9;">●</span> Overall density: {(f"{overall_density:.1f}k/km²" if overall_density is not None else "N/A")}</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #2980b9;">●</span> Macao Peninsula: {(f"{macao_peninsula_density:.1f}k/km²" if macao_peninsula_density is not None else "N/A")}</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #2980b9;">●</span> Taipa: {(f"{taipa_density:.1f}k/km²" if taipa_density is not None else "N/A")}</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #2980b9;">●</span> Coloane: {(f"{coloane_density:.1f}k/km²" if coloane_density is not None else "N/A")}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col4:
        # Calculate year-on-year changes
        yoy_pop = ""
        if yoy_total_pop is not None:
            # Use plus/minus sign for total population YoY (signed style)
            yoy_pop = f"Population: {format_yoy_label(yoy_total_pop, '%', decimals=1, use_sign=True)}"
        
        yoy_growth = ""
        if yoy_annual_growth is not None:
            # Use plus/minus sign for growth in cards (not arrows)
            yoy_growth = f"Growth: {format_yoy_label(yoy_annual_growth, '%', decimals=1, use_sign=True)}"
        
        # Calculate density YoY as absolute change in people/km² (not percent)
        density = current_data.get('Population density', 0)
        yoy_density = None
        if prev_data is not None and pd.notna(prev_data.get('Population density')):
            yoy_density = density - prev_data['Population density']

        yoy_density_str = ""
        if yoy_density is not None:
            # No percentage symbol, report absolute difference in density (km²) with +/-
            yoy_density_str = f"Density: {format_yoy_label(yoy_density, '', decimals=1, use_sign=True)}k/km²"
        
        # Non-resident workers YoY
        yoy_workers_str = ""
        if yoy_workers is not None:
            yoy_workers_str = f"Non-resident workers: {format_yoy_label(yoy_workers, '%', decimals=1, use_sign=True)}"

        # Helper to determine text color based on YoY value (positive green, negative red, zero black)
        def _yoy_text_color(val, decimals=1):
            try:
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    return '#555'  # gray for missing
                # If within our target year range apply the color rule
                if 2000 <= int(selected_year) <= 2024:
                    # Determine color based on rounded value to match formatting
                    rounded_val = round(float(val), decimals)
                    if float(rounded_val) > 0:
                        return '#27ae60'
                    elif float(rounded_val) < 0:
                        return '#e74c3c'
                    else:
                        return '#555'  # neutral grey for exactly zero (match summary text)
                return '#555'
            except Exception:
                return '#555'

        # Compute value-only formatted strings
        pop_value_str = format_yoy_label(yoy_total_pop, '%', decimals=1, use_sign=True) if yoy_total_pop is not None else None
        growth_value_str = format_yoy_label(yoy_annual_growth, '%', decimals=1, use_sign=True) if yoy_annual_growth is not None else None
        density_value_str = (format_yoy_label(yoy_density, '', decimals=1, use_sign=True) + "k/km²") if yoy_density is not None else None
        workers_value_str = format_yoy_label(yoy_workers, '%', decimals=1, use_sign=True) if yoy_workers is not None else None

        # Compute color-coded display strings (use labels like 'Population: ' etc.)
        if selected_year == 1999:
            yoy_pop_display = "Population: N/A"
            yoy_growth_display = "Growth: N/A"
            yoy_density_display = "Density: N/A"
            yoy_workers_display = "Non-resident workers: N/A"
        else:
            # Population
            if pop_value_str is not None:
                pop_color = _yoy_text_color(yoy_total_pop, decimals=1)
                yoy_pop_display = f"Population: <span style=\"color: {pop_color};\">{pop_value_str}</span>"
            else:
                yoy_pop_display = "Population: N/A"
            # Growth (annual growth rate)
            if growth_value_str is not None:
                growth_color = _yoy_text_color(yoy_annual_growth, decimals=1)
                yoy_growth_display = f"Growth: <span style=\"color: {growth_color};\">{growth_value_str}</span>"
            else:
                yoy_growth_display = "Growth: N/A"
            # Density
            if density_value_str is not None:
                density_color = _yoy_text_color(yoy_density, decimals=1)
                # density_value_str already contains '/km²'
                yoy_density_display = f"Density: <span style=\"color: {density_color};\">{density_value_str}</span>"
            else:
                yoy_density_display = "Density: N/A"
            # Non-resident workers
            if workers_value_str is not None:
                workers_color = _yoy_text_color(yoy_workers, decimals=1)
                yoy_workers_display = f"Non-resident workers: <span style=\"color: {workers_color};\">{workers_value_str}</span>"
            else:
                yoy_workers_display = "Non-resident workers: N/A"
            
        st.markdown("""
        <div class='stat-box' style="
            background: linear-gradient(135deg, rgba(155, 89, 182, 0.08) 0%, rgba(155, 89, 182, 0.08) 100%);
            border-left-color: #9b59b6;
        ">
            <div style="font-weight: 800; color: #1e3a5f; margin-bottom: 12px; font-size: 1.1em;">📈 Year-over-Year Changes</div>
            <div style="font-size: 0.95em; line-height: 1.8; color: #555;">
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #9b59b6;">●</span> """ + yoy_pop_display + """</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #9b59b6;">●</span> """ + yoy_growth_display + """</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #9b59b6;">●</span> """ + yoy_density_display + """</span>
                <span style="display: block; margin: 4px 0; font-weight: 600;"><span style="color: #9b59b6;">●</span> """ + yoy_workers_display + """</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
