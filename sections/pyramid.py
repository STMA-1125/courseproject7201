import streamlit as st
import re
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

    tab1, tab2 = st.tabs(["Absolute Numbers", "Percentage"])
    
    # --- FINAL FIX: PROMISE-AWARE LAZY RENDER ---
    # This replacement function waits for the tab to be visible.
    # CRITICALLY, it returns a Promise. This ensures that any subsequent 
    # .then() blocks (which load animation frames/sliders) still execute 
    # after we finally render the chart.
    
    def intelligent_render(html_str):
        # 1. CSS to clean up layout
        style_patch = """
        <style>
            body { margin: 0; padding: 0; overflow: hidden; }
            .plotly-graph-div { height: 100vh; width: 100%; }
        </style>
        """
        
        # 2. The JavaScript Wrapper
        # It wraps the Plotly.newPlot arguments and returns a new Promise.
        # This Promise resolves only after the element is visible and drawn.
        replacement_js = """
        (function(gd, data, layout, config) {
            return new Promise(function(resolve, reject) {
                // Check visibility every 100ms
                var interval = setInterval(function() {
                    // Handle case where gd is an ID string or an Element object
                    var el = (typeof gd === 'string') ? document.getElementById(gd) : gd;
                    
                    // If element exists and has width (tab is visible)
                    if (el && el.clientWidth > 0) {
                        clearInterval(interval);
                        
                        // Force autosize to prevent 0-width bugs
                        if (layout) {
                            delete layout.width;
                            delete layout.height;
                            layout.autosize = true;
                        }
                        
                        // Render and chain the success
                        Plotly.newPlot(el, data, layout, config)
                            .then(function(graphDiv) {
                                window.Plotly.Plots.resize(graphDiv);
                                resolve(graphDiv); // Trigger the original .then() (frames)
                            })
                            .catch(reject);
                    }
                }, 100);
            });
        })("""

        # 3. Inject CSS
        if "<body>" in html_str:
            html_str = html_str.replace("<body>", "<body>" + style_patch)
        else:
            html_str = style_patch + html_str

        # 4. Apply the replacement
        # Matches 'Plotly.newPlot(' and replaces it with our wrapper start
        html_str = re.sub(r"Plotly\.newPlot\s*\(", replacement_js, html_str)
        
        return html_str

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
            st.components.v1.html(intelligent_render(html_content), height=750)
        except FileNotFoundError:
            st.error(f"❌ File `macao_population_pyramid_abs_value.html` not found.")
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
            # Apply the fix
            st.components.v1.html(intelligent_render(html_content), height=750)
        except FileNotFoundError:
            st.error(f"❌ File `macao_population_pyramid_percentage.html` not found.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")