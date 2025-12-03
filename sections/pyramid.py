import streamlit as st
import re
from pathlib import Path
import sys
import os
import importlib

def show_pyramid(selected_year, project_root):
    graphs_dir = project_root / "graphs"
    sys.path.insert(0, str(graphs_dir))
    macao_pyramid = importlib.import_module('macao_pyramid')
    macao_pyramid_percent = importlib.import_module('macao_pyramid_percent')
    
    load_abs_csv = macao_pyramid.load_pyramid_csv
    pivot_abs_df = macao_pyramid.pivot_pyramid_df
    build_abs_figure = macao_pyramid.build_pyramid_figure
    
    load_pct_csv = macao_pyramid_percent.load_pyramid_csv
    pivot_pct_df = macao_pyramid_percent.pivot_pyramid_df
    build_pct_figure = macao_pyramid_percent.build_pyramid_figure
    
    from modules.ui_components import decorative_header
    decorative_header(
        "Population Pyramid Analysis",
        "Understanding the age and sex distribution across decades",
        ["✨ Demographic Structure", "👥 Population Composition"],
        icon='population_pyramid',
        project_root=str(project_root),
        icon_size=40,
        padding='40px 35px',
        title_font_size='2.8em'
    )

    # Startup mode is implicitly 'off' to avoid autoplay; no need for a visible control
    start_mode = 'off'
    tab1, tab2 = st.tabs(["Absolute Numbers", "Percentage"])
    
    with tab1:
        st.markdown("""
        <div style="margin-top: 24px; margin-bottom: 12px;">
            <div class="section-header">
                Population by Age Group (Thousands)
            </div>
            <div class="section-underline"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("Shows the actual number of people in each age group and gender.")
        try:
            csv_path = project_root / "data" / "processed" / "population_pyramid_data.csv"
            df = load_abs_csv(str(csv_path))
            long, age_order = pivot_abs_df(df)
            # Use 'off' startup mode so the figure is static until the user plays it
            fig = build_abs_figure(long, age_order, start_mode=start_mode)
            st.plotly_chart(fig, key="pyramid_abs")
        except FileNotFoundError:
            st.error(f"❌ File `population_pyramid_data.csv` not found.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.markdown("""
        <div style="margin-top: 24px; margin-bottom: 12px;">
            <div class="section-header">
                Population Distribution as % of Total
            </div>
            <div class="section-underline"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("Shows the proportion of the total population in each age group and gender.")
        try:
            csv_path = project_root / "data" / "processed" / "population_pyramid_data_percentage.csv"
            df = load_pct_csv(str(csv_path))
            long, age_order = pivot_pct_df(df)
            # Use 'off' startup mode so the figure is static until the user plays it
            fig = build_pct_figure(long, age_order, start_mode=start_mode)
            st.plotly_chart(fig, key="pyramid_pct")
        except FileNotFoundError:
            st.error(f"❌ File `population_pyramid_data_percentage.csv` not found.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")