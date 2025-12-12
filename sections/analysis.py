"""Demographic analysis section.

Renders the long-term trends and age-structure analysis views.
"""

from __future__ import annotations

import streamlit as st

from streamlit_elements import elements, mui, html

from modules.ui_components import decorative_header


def show_analysis(selected_year: int, project_root, demographics=None) -> None:
    """Render the Demographic Analysis section.

    Args:
        selected_year: Currently selected year from the sidebar. This section
            focuses on time series; the year is retained for consistent
            navigation and potential future highlighting.
        project_root: Absolute path to the project root folder.
        demographics: Full demographics dataframe if available (preferred).
            When not provided, the underlying graph modules will load the
            processed CSV directly.
    """
    decorative_header(
        "Demographic Analysis",
        "Population changes and demographic patterns over time",
        ["✨ Trend Analysis", "📈 Forecasting", "🎯 Historical Patterns"],
        icon='analysis',
        project_root=str(project_root),
        icon_bg='circle',
        icon_bg_size=48,
        icon_inner_size=28,
        icon_margin_right=12
        , padding='40px 35px', title_font_size='2.8em'
    )
    
    tab1, tab2 = st.tabs(["Trends", "Age Structure"])
    
    with tab1:
        st.markdown("""
        <div style="margin-top: 24px; margin-bottom: 12px;">
            <div class="section-header">
                Trends Analysis
            </div>
            <div class="section-underline"></div>
        </div>
        """, unsafe_allow_html=True)
        # Description section
        with elements("trends_description"):
            mui.Box(
                mui.Typography(
                    "Overview",
                    variant="h6",
                    style={"fontWeight": "bold", "color": "#2c3e50", "marginBottom": "12px"}
                ),
                mui.Typography(
                    "This chart illustrates key demographic trends in Macao over the 25-year period following its handover to China, using 1999 as the baseline (index = 100). It tracks four metrics against a timeline of major economic and social events.",
                    variant="body2",
                    style={"color": "#555", "marginBottom": "12px", "lineHeight": "1.6"}
                ),
                mui.Box(
                    html.ul(
                        html.li("🔵 Population Index: Total population growth indexed to 1999"),
                        html.li("🟣 Density Index: Population density changes over time"),
                        html.li("🟠 Aging Ratio: Proportion of elderly population (%)"),
                        html.li("🟤 Non-Resident Ratio: Percentage of non-resident workers in the population"),
                    ),
                    style={"marginLeft": "16px", "color": "#555", "fontSize": "14px"}
                ),
                mui.Typography(
                    "Major Events: Gaming liberalization (2002), labor surge (~2010), gaming peak (~2014), COVID-19 impact (2020 - 2022), and economic recovery (2022 - 2024).",
                    variant="body2",
                    style={"color": "#7f8c8d", "marginTop": "12px", "fontStyle": "italic"}
                ),
                style={"padding": "16px", "background": "#f9f9f9", "borderRadius": "8px", "marginBottom": "24px", "border": "1px solid #e0e0e0"}
            )
        
        # Prefer rendering a live Plotly figure; fall back to a pre-generated HTML artifact.
        try:
            from graphs.macao_demographic_trends import build_trends_figure
            # Build the figure using the main dataframe if available
            fig = build_trends_figure(demographics) if demographics is not None else build_trends_figure()
            st.plotly_chart(fig, width="stretch")
        except Exception:
            # Fallback: embed the pre-generated HTML if import/plotting fails.
            try:
                candidates = [project_root / 'graphs' / 'Macao_Demographic_Trends.html', project_root / 'Macao_Demographic_Trends.html']
                file_path = next((p for p in candidates if p.exists()), None)
                if file_path is None:
                    raise FileNotFoundError
                html_content = file_path.read_text(encoding='utf-8')
                # Allow scrolling for large standalone HTML files and ensure scripts run inside the iframe
                st.components.v1.html(html_content, height=500, scrolling=True)
            except FileNotFoundError:
                st.error("❌ File `Macao_Demographic_Trends.html` not found and the module import failed")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Forecasting section
        st.markdown("""
        <div style="margin-top: 24px; margin-bottom: 12px;">
            <div class="section-header">
                Trends Forecasting
            </div>
            <div class="section-underline"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Description section for forecasting
        with elements("forecasting_description"):
            mui.Box(
                mui.Typography(
                    "Overview",
                    variant="h6",
                    style={"fontWeight": "bold", "color": "#2c3e50", "marginBottom": "12px"}
                ),
                mui.Typography(
                    "This chart presents long-term demographic projections for Macao from 1999 to 2035, modeling population trends and aging under different scenarios.",
                    variant="body2",
                    style={"color": "#555", "marginBottom": "12px", "lineHeight": "1.6"}
                ),
                mui.Box(
                    html.ul(
                        html.li("Baseline Scenario: Most likely forecast assuming current trends continue"),
                        html.li("High Growth Scenario: Strong economic performance with higher population growth"),
                        html.li("Low Growth Scenario: Weaker economy with lower population growth and sharper aging"),
                    ),
                    style={"marginLeft": "16px", "color": "#555", "fontSize": "14px"}
                ),
                mui.Typography(
                    "Each scenario shows population size and aging ratio projections, highlighting the impact of economic policies and immigration on Macao's demographics.",
                    variant="body2",
                    style={"color": "#7f8c8d", "marginTop": "12px", "fontStyle": "italic"}
                ),
                style={"padding": "16px", "background": "#f9f9f9", "borderRadius": "8px", "marginBottom": "24px", "border": "1px solid #e0e0e0"}
            )
        
        # Prefer rendering a live Plotly figure; fall back to a pre-generated HTML artifact.
        try:
            from graphs.macao_demographic_trends_forecast import build_forecast_figure
            fig_forecast = build_forecast_figure(demographics) if demographics is not None else build_forecast_figure()
            st.plotly_chart(fig_forecast, width="stretch")
        except Exception:
            try:
                # Prefer graphs/ copy first then project root copy
                candidates = [project_root / 'graphs' / 'Macao_Demographic_Trends_Forecast.html', project_root / 'Macao_Demographic_Trends_Forecast.html']
                fpath = next((p for p in candidates if p.exists()), None)
                if fpath is None:
                    raise FileNotFoundError
                forecast_html_content = fpath.read_text(encoding='utf-8')
                st.components.v1.html(forecast_html_content, height=800, scrolling=True)
            except FileNotFoundError:
                st.warning("⚠️ Forecasting visualization not available")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.markdown("""
        <div style="margin-top: 24px; margin-bottom: 12px;">
            <div class="section-header">
                Age Structure Analysis
            </div>
            <div class="section-underline"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Description section for age structure
        with elements("age_structure_description"):
            mui.Box(
                mui.Typography(
                    "Overview",
                    variant="h6",
                    style={"fontWeight": "bold", "color": "#2c3e50", "marginBottom": "12px"}
                ),
                mui.Typography(
                    "This bubble scatter plot shows Macau's demographic shift from a young to an aged society from 1999 to 2024, highlighting declining child populations and rising elderly proportions.",
                    variant="body2",
                    style={"color": "#555", "marginBottom": "12px", "lineHeight": "1.6"}
                ),
                mui.Box(
                    html.ul(
                        html.li("X-axis: Balance from 'Young Society' (left) to 'Highly Aged Society' (right)"),
                        html.li("Y-axis: Percentage of children in population"),
                        html.li("Bubble Size: Total population per year"),
                        html.li("Color: Year progression from blue (1999) to red (2024)"),
                    ),
                    style={"marginLeft": "16px", "color": "#555", "fontSize": "14px"}
                ),
                mui.Typography(
                    "Key trend: Bubbles move down and right over time, indicating fewer children and more elderly, with early years clustered upper-left and recent years lower-right.",
                    variant="body2",
                    style={"color": "#7f8c8d", "marginTop": "12px", "fontStyle": "italic"}
                ),
                style={"padding": "16px", "background": "#f9f9f9", "borderRadius": "8px", "marginBottom": "24px", "border": "1px solid #e0e0e0"}
            )
        
        try:
            from graphs.bubble_chart import create_bubble_chart
            fig = create_bubble_chart()
            st.plotly_chart(fig, width="stretch")
        except Exception as e:
            st.error(f"❌ Error generating chart: {str(e)}")