import os
from typing import List, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio


def load_pyramid_csv(csv_path: str) -> pd.DataFrame:
    # Read everything as string to avoid ambiguous date parsing warnings,
    # then convert numeric columns explicitly.
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    df = df.replace({"": pd.NA}).dropna(how="all")

    # Convert population/measurement columns to numeric, keep other columns (e.g. "Age Group") as-is
    for col in df.columns:
        if col != "Age Group":
            # remove thousands separators and whitespace, then coerce to numeric
            df[col] = pd.to_numeric(df[col].str.replace(",", "", regex=False).str.strip(), errors="coerce")

    return df


def pivot_pyramid_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    value_cols = [c for c in df.columns if c != "Age Group"]

    long = df.melt(id_vars=["Age Group"], value_vars=value_cols, var_name="Year_Sex", value_name="Population")

    long["Sex"] = long["Year_Sex"].str[0].map({"M": "Male", "F": "Female"})
    long["Year"] = long["Year_Sex"].str.split("_").str[1].astype(int)

    long["Population"] = pd.to_numeric(long["Population"], errors="coerce").fillna(0.0)
    long["Population_Neg"] = long.apply(lambda r: -r["Population"] if r["Sex"] == "Male" else r["Population"], axis=1)
    # Add absolute value column for hover - this is the key fix
    long["Population_Abs"] = long["Population"].abs()

    age_order = list(df["Age Group"].dropna().unique())

    return long, age_order


def build_pyramid_figure(long: pd.DataFrame, age_order: List[str], start_mode: str = 'last') -> go.Figure:
    """Build and return the animated population pyramid with clean hover."""
    color_map = {"Male": "#5DADE2", "Female": "#F1948A"}
    xmax = 15.0

    # Create figure with px.bar
    fig = px.bar(
        long,
        x="Population_Neg",
        y="Age Group",
        color="Sex",
        animation_frame="Year",
        orientation="h",
        category_orders={"Age Group": age_order},
        color_discrete_map=color_map,
        title="Macao Population Pyramid (1999–2024)",
        labels={"Population_Neg": "Percentage of population (%)", "Age Group": "Age Group"},
        width=1000,
        height=800,
        custom_data=["Population_Abs"]  # Pass absolute values for hover
    )

    # --- Custom Hover Configuration ---
    fig.update_layout(
        hovermode="y unified",
        hoverlabel=dict(
            namelength=-1,
            bgcolor="white",
            bordercolor="rgba(0,0,0,0)",
            font_family="Arial",
            font_size=12,
            font_color="black"
        )
    )

    # Use customdata[0] instead of x|abs for reliability
    male_template = "Male<br>Percentage of population (%) = %{customdata[0]:.1f}<extra></extra>"
    female_template = "Female<br>Percentage of population (%) = %{customdata[0]:.1f}<extra></extra>"

    # Loop through the traces and apply the correct template
    for trace in fig.data:
        if trace.name == "Male":
            trace.hovertemplate = male_template
        elif trace.name == "Female":
            trace.hovertemplate = female_template
            
    # --- CRITICAL: Also update the hovertemplate in frames ---
    if hasattr(fig, "frames") and fig.frames:
        for frame in fig.frames:
            for trace in frame.data:
                if trace.name == "Male":
                    trace.hovertemplate = male_template
                elif trace.name == "Female":
                    trace.hovertemplate = female_template
    # --- End Custom Hover Configuration ---

    # Add year annotation
    years = sorted(long["Year"].unique())
    # start_mode controls how the chart appears on initial render in the page:
    #  - 'last': show the latest year's frame (useful for snapshot view of latest data)
    #  - 'off' : disable startup animation and show an empty/off view until the user plays
    #  - 'first' : shows the first year and is the default behavior of many animations
    # You can change this when calling the function from a UI (e.g., Streamlit) by
    # passing start_mode='off' to prevent any autoplay behavior.
    # The initial_year annotation is controlled by start_mode (last, off, first)
    if start_mode == 'last':
        initial_year = years[-1] if len(years) > 0 else ""
    elif start_mode == 'off':
        initial_year = years[0] if len(years) > 0 else ""  # Show first year when 'off'
    else:
        initial_year = years[0] if len(years) > 0 else ""

    def create_year_annotation(year_text):
        return dict(
            text=str(year_text),
            x=0.98,
            y=0.98,
            xref="paper",
            yref="paper",
            xanchor="right",
            yanchor="top",
            showarrow=False,
            font=dict(size=48, color="rgba(0,0,0,0.25)"),
        )

    fig.update_layout(annotations=[create_year_annotation(initial_year)])

    if hasattr(fig, "frames") and fig.frames:
        for fr in fig.frames:
            try:
                fyear = int(fr.name)
            except Exception:
                fyear = fr.name
            fr.layout = fr.layout or {}
            fr.layout.annotations = [create_year_annotation(fyear)]
            fr.layout.xaxis = dict(range=[-xmax, xmax])
            fr.layout.yaxis = dict(autorange="reversed")

    # Set symmetric ticks and labels
    step = 2.5
    pos_vals = [round(v * step, 10) for v in range(0, int(xmax/step) + 1)]
    tickvals = [-v for v in reversed(pos_vals[1:])] + pos_vals
    ticktext = [f"{abs(v):g}%" for v in tickvals]

    fig.update_layout(
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext,
            range=[-xmax, xmax],
            title="Percentage of population (%)",
        ),
        yaxis=dict(autorange="reversed"),
        bargap=0.05,
        legend_title_text="Sex",
        margin=dict(l=80, r=40, t=80, b=300),
    )

    # Position slider and adjust play/pause buttons
    if fig.layout.sliders:
        s = fig.layout.sliders[0]
        s.len = 0.80
        s.x = 0.5 - s.len/2
        s.y = -0.26
        s.currentvalue.prefix = "Year: "

        years = sorted(long["Year"].unique())
        for i, step in enumerate(s.steps):
            step.label = str(years[i])

        um = fig.layout.updatemenus[0]
        um.x = s.x - 0.01
        um.xanchor = "right"
        um.y = s.y
        um.yanchor = "middle"
        um.direction = "left"

        # Compute dropdown position based on the end of the slider (s.x + s.len)
        dropdown_x = s.x + s.len
        dropdown_y = s.y + 0.02

    if fig.layout.updatemenus:
        # Clear any built-in updatemenus (including default Play/Pause)
        fig.layout.updatemenus = []

    # Alternative: ensure transition and animation defaults won't auto-play
    fig.layout.transition = fig.layout.transition or {}
    fig.layout.transition.duration = 0

    # Set initial slider to last year as a fallback (keeps the most recent snapshot visible)
    if fig.layout.sliders:
        # Choose startup behavior.
        if start_mode == 'last':
            fig.layout.sliders[0].active = len(fig.frames) - 1
        elif start_mode == 'off':
            fig.layout.sliders[0].active = 0
        else:
            fig.layout.sliders[0].active = 0

    # Add line traces for each year
    for year in years:
        year_data = long[long["Year"] == year]
        male_data = year_data[year_data["Sex"] == "Male"]
        female_data = year_data[year_data["Sex"] == "Female"]
        
        # Add male line
        fig.add_trace(go.Scatter(
            x=male_data["Population_Neg"],
            y=male_data["Age Group"],
            mode='lines+markers',
            line=dict(color='black', width=2),
            marker=dict(size=4, color='black'),
            opacity=0.5,
            visible=False,
            showlegend=False,
            customdata=male_data[["Year", "Population"]].to_numpy(),
            hovertemplate="Male (%{customdata[0]})<br>Percentage of population (%) : %{customdata[1]:.1f}<extra></extra>"
        ))
        
        # Add female line
        fig.add_trace(go.Scatter(
            x=female_data["Population_Neg"],
            y=female_data["Age Group"],
            mode='lines+markers',
            line=dict(color='black', width=2),
            marker=dict(size=4, color='black'),
            opacity=0.5,
            visible=False,
            showlegend=False,
            customdata=female_data[["Year", "Population"]].to_numpy(),
            hovertemplate="Female (%{customdata[0]})<br>Percentage of population (%) : %{customdata[1]:.1f}<extra></extra>"
        ))

    # Add dropdown for year selection
    year_options = []
    num_years = len(years)
    for i, year in enumerate(years):
        visible = [True, True] + [False] * (2 * num_years)
        visible[2 + 2 * i] = True
        visible[2 + 2 * i + 1] = True
        year_options.append(dict(label=str(year), method='restyle', args=[{'visible': visible}]))
    
    # Add 'Off' option
    off_visible = [True, True] + [False] * (2 * num_years)
    year_options.insert(0, dict(label='Off', method='restyle', args=[{'visible': off_visible}]))

    # --- Add Play/Pause/Stop controls ---
    # Play button
    play_button = dict(
        label="Play",
        method="animate",
        args=[
            None,
            {
                "frame": {"duration": 800, "redraw": True},
                "transition": {"duration": 300},
                "fromcurrent": True,
            },
        ],
    )

    # Pause button (immediate, stops animation by setting frame duration to 0)
    pause_button = dict(
        label="Pause",
        method="animate",
        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
    )

    # Stop button: switch to 'Off' view by setting visibility to the Off option
    stop_button = dict(
        label="Stop",
        method="restyle",
        args=[{"visible": off_visible}],
    )

    # Position controls slightly above the year slider; use icons for buttons
    # create copies to avoid overriding the original dicts
    play_btn = play_button.copy()
    play_btn['label'] = '▶'
    pause_btn = pause_button.copy()
    pause_btn['label'] = '⏸'
    # Stop needs to reset to first year (using animate to jump to the first frame)
    stop_btn = stop_button.copy()
    stop_btn['label'] = '⏹'
    if years:
        stop_btn = dict(
            label='⏹',
            method='animate',
            args=[[str(years[0])], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
        )
    # Position controls to left side of the slider. We'll base it on s.x so it sits just to the left
    # of the slider start. If slider is defined, set x accordingly.
    os_slider_x = 0.5
    if fig.layout.sliders:
        os_slider_x = fig.layout.sliders[0].x

    # Align controls bottom to slightly above the slider by using yanchor='bottom'
    # Place controls just above the "Year: XXXX" label (slightly above the slider)
    if fig.layout.sliders:
        controls_y = s.y + 0.008  # keep buttons just barely above the slider handle
    else:
        controls_y = -0.09

    controls_menu = dict(
        type="buttons",
        direction="left",
        showactive=False,
        buttons=[play_btn, pause_btn, stop_btn],
        x=max(0.02, os_slider_x - 0.02),
        y=controls_y,
        xanchor='left',
        yanchor='bottom',
        font=dict(size=16)
    )

    # Year dropdown + custom controls
    # Position dropdown below the legend (legend is at top-right by default)
    # Place the dropdown above the right end of the slider if slider present,
    # otherwise keep the default bottom-right placement.
    dropdown_x = locals().get('dropdown_x', 0.92)
    dropdown_y = locals().get('dropdown_y', -0.15)
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=year_options,
                x=dropdown_x,
                y=dropdown_y,
                xanchor='center',
                yanchor='bottom',
                direction='down'
                ,
                font=dict(size=16)
            ),
            controls_menu,
        ]
    )

    # Add label annotation above the dropdown
    current_annotations = list(fig.layout.annotations) if fig.layout.annotations else []
    # Place the label right above the dropdown (if computed from slider, use that)
    label_x = locals().get('dropdown_x', 0.92)
    # Place the label a bit higher above the dropdown to avoid overlap
    label_y = locals().get('dropdown_y', -0.15) + 0.10
    current_annotations.append(
        dict(
            text="Select a year for comparison",
            x=label_x,
            y=label_y,
            xref="paper",
            yref="paper",
            xanchor="center",
            yanchor="bottom",
            showarrow=False,
            font=dict(size=16, color="black")
        )
    )
    fig.update_layout(annotations=current_annotations)

    return fig


def build_and_save(long: pd.DataFrame, age_order: List[str], out_html: str) -> None:
    """Build figure and save to HTML (for standalone use)."""
    fig = build_pyramid_figure(long, age_order)
    fig.write_html(out_html, include_plotlyjs="cdn")
    print(f"Saved population pyramid to: {out_html}")


def main():
    # Resolve project root (parent of this `graphs` directory) so CSV is read from data/processed
    graphs_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(graphs_dir, os.pardir))

    csv_path = os.path.join(project_root, "data", "processed", "population_pyramid_data_percentage.csv")
    out_html = os.path.join(project_root, "macao_population_pyramid_percentage.html")

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        print("Please ensure 'population_pyramid_data_percentage.csv' is present in data/processed relative to project root.")
        return

    df = load_pyramid_csv(csv_path)
    long, age_order = pivot_pyramid_df(df)
    build_and_save(long, age_order, out_html)


if __name__ == "__main__":
    main()