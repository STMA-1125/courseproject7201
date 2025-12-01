import streamlit as st
import os
from pathlib import Path

def show_pyramid(selected_year, project_root):
    graphs_dir = project_root / "graphs"
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

    # Tabs for pyramid views
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
            abs_pyramid_file = graphs_dir / "macao_population_pyramid_abs_value.html"
            html_content = abs_pyramid_file.read_text(encoding='utf-8')
            st.components.v1.html(html_content, height=750)
        except FileNotFoundError:
            st.error(f"❌ File `macao_population_pyramid_abs_value.html` not found. Expected at: {abs_pyramid_file}")
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
            percent_pyramid_file = graphs_dir / "macao_population_pyramid_percentage.html"
            html_content = percent_pyramid_file.read_text(encoding='utf-8')
            st.components.v1.html(html_content, height=750)
        except FileNotFoundError:
            st.error(f"❌ File `macao_population_pyramid_percentage.html` not found. Expected at: {percent_pyramid_file}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")