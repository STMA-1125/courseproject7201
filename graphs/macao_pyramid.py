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

    # Treat values as absolute numbers (already in the CSV). Keep numeric and create mirrored negative
    long["Population"] = pd.to_numeric(long["Population"], errors="coerce").fillna(0.0)
    long["Population_Neg"] = long.apply(lambda r: -r["Population"] if r["Sex"] == "Male" else r["Population"], axis=1)
    # Absolute value column for hover/display
    long["Population_Abs"] = long["Population"].abs()

    age_order = list(df["Age Group"].dropna().unique())

    return long, age_order


def build_pyramid_figure(long: pd.DataFrame, age_order: List[str]) -> go.Figure:
    """Build and return the animated population pyramid with clean hover."""
    color_map = {"Male": "#5DADE2", "Female": "#F1948A"}
    # Use absolute axis max (thousands). We'll use 45k as the max to match tick range.
    xmax = 45.0

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
        labels={"Population_Neg": "Population (thousands)", "Age Group": "Age Group"},
        height=700,
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

    # Use customdata[0] instead of x|abs for reliability (show absolute numbers)
    male_template = "Male<br>Population (thousands) = %{customdata[0]:.1f}<extra></extra>"
    female_template = "Female<br>Population (thousands) = %{customdata[0]:.1f}<extra></extra>"

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

    # Set symmetric ticks and labels: -45,-40,...,0,...,40,45 with labels 45,40,...0,5,10,...45
    tickvals = [float(v) for v in range(-int(xmax), int(xmax) + 5, 5)]  # -45,-40,...,45
    ticktext = [str(int(abs(v))) for v in tickvals]

    fig.update_layout(
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext,
            range=[-xmax, xmax],
            title="Population (thousands)",
        ),
        yaxis=dict(autorange="reversed"),
        bargap=0.05,
        legend_title_text="Sex",
        margin=dict(l=80, r=40, t=80, b=160),
    )

    # Position slider and adjust play/pause buttons
    if fig.layout.sliders:
        s = fig.layout.sliders[0]
        s.len = 0.80
        s.x = 0.5 - s.len/2
        s.y = -0.12
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

    if fig.layout.updatemenus:
        fig.layout.updatemenus = []

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
            hovertemplate="Male (%{customdata[0]})<br>Population (thousands) : %{customdata[1]:.1f}<extra></extra>"
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
            hovertemplate="Female (%{customdata[0]})<br>Population (thousands) : %{customdata[1]:.1f}<extra></extra>"
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

    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=year_options,
                x=0.92,
                y=-0.15,
                xanchor='left',
                yanchor='middle',
                direction='down'
            )
        ]
    )

    # Add label annotation
    current_annotations = list(fig.layout.annotations) if fig.layout.annotations else []
    current_annotations.append(
        dict(
            text="Select a year for comparison",
            x=0.92,
            y=-0.1,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            showarrow=False,
            font=dict(size=12, color="black")
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

    csv_path = os.path.join(project_root, "data", "processed", "population_pyramid_data.csv")
    out_html = os.path.join(project_root, "macao_population_pyramid_abs_value.html")

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        print("Please ensure 'population_pyramid_data.csv' is present in data/processed relative to project root.")
        return

    df = load_pyramid_csv(csv_path)
    long, age_order = pivot_pyramid_df(df)
    build_and_save(long, age_order, out_html)


if __name__ == "__main__":
    main()