import streamlit as st
from pathlib import Path

from graphs import macao_population_pyramid
from modules.ui_components import decorative_header


def show_pyramid(selected_year, project_root):
    load_csv = macao_population_pyramid.load_pyramid_csv
    pivot_df = macao_population_pyramid.pivot_pyramid_df
    build_figure = macao_population_pyramid.build_pyramid_figure
    
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
            df = load_csv(str(csv_path))
            long, age_order = pivot_df(df)
            # Use 'off' startup mode so the figure is static until the user plays it
            fig = build_figure(long, age_order, mode="abs", start_mode=start_mode)
            st.plotly_chart(fig, key="pyramid_abs", width="stretch")
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
            df = load_csv(str(csv_path))
            long, age_order = pivot_df(df)
            # Use 'off' startup mode so the figure is static until the user plays it
            fig = build_figure(long, age_order, mode="pct", start_mode=start_mode)
            st.plotly_chart(fig, key="pyramid_pct", width="stretch")
        except FileNotFoundError:
            st.error(f"❌ File `population_pyramid_data_percentage.csv` not found.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")