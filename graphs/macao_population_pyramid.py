"""Population pyramid figure builder.

Reads preprocessed pyramid CSVs and builds an animated Plotly population pyramid
for absolute values or percentages.
"""

from __future__ import annotations

# NOTE: No runtime script runner is provided; `os` was previously used by runner.
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple, Literal

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


Mode = Literal["abs", "pct"]


def _resolve_csv_path(csv_path: str) -> Path:
    """Resolve CSV path relative to common working directories."""
    path = Path(csv_path)
    if path.exists():
        return path
    alt = Path("../") / path
    if alt.exists():
        return alt
    return path


@lru_cache(maxsize=8)
def _read_pyramid_csv_cached(path_str: str, mtime_ns: int) -> pd.DataFrame:
    """Read a pyramid CSV as strings (cache keyed by mtime)."""
    # NOTE: mtime_ns is intentionally unused except as part of the cache key.
    return pd.read_csv(path_str, dtype=str, keep_default_na=False)


def load_pyramid_csv(csv_path: str) -> pd.DataFrame:
    """Load a pyramid CSV.

    Schema:
      - "Age Group" column
      - year/sex columns like "M_1999", "F_1999", ...

    Notes:
      - read as strings first; explicitly coerce numeric columns
      - strip commas to support thousands separators
    """
    path = _resolve_csv_path(csv_path)
    mtime_ns = path.stat().st_mtime_ns if path.exists() else 0
    df = _read_pyramid_csv_cached(str(path), mtime_ns).copy()
    df = df.replace({"": pd.NA}).dropna(how="all")

    for col in df.columns:
        if col != "Age Group":
            df[col] = pd.to_numeric(
                df[col].str.replace(",", "", regex=False).str.strip(),
                errors="coerce",
            )

    return df


def pivot_pyramid_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Convert a wide pyramid dataframe into a long form suitable for Plotly."""

    value_cols = [c for c in df.columns if c != "Age Group"]

    long = df.melt(
        id_vars=["Age Group"],
        value_vars=value_cols,
        var_name="Year_Sex",
        value_name="Population",
    )

    long["Sex"] = long["Year_Sex"].str[0].map({"M": "Male", "F": "Female"})
    long["Year"] = long["Year_Sex"].str.split("_").str[1].astype(int)

    long["Population"] = pd.to_numeric(long["Population"], errors="coerce").fillna(0.0)
    # Mirror males to the left so both sexes share one centered axis.
    long["Population_Neg"] = np.where(long["Sex"] == "Male", -long["Population"], long["Population"])
    long["Population_Abs"] = long["Population"].abs()

    age_order = list(df["Age Group"].dropna().unique())

    return long, age_order


def build_pyramid_figure(
    long: pd.DataFrame,
    age_order: List[str],
    *,
    mode: Mode,
    start_mode: str = "last",
) -> go.Figure:
    """Build the animated population pyramid.

    start_mode controls the initial snapshot:
      - "last": show the latest year
      - "off": keep a static initial state (no implicit autoplay)
      - "first": show the first year
    """

    color_map = {"Male": "#5DADE2", "Female": "#F1948A"}

    if mode == "abs":
        x_axis_title = "Population (thousands)"
        labels = {"Population_Neg": x_axis_title, "Age Group": "Age Group"}
        hover_unit = x_axis_title
        xmax = 45.0
    elif mode == "pct":
        x_axis_title = "Percentage of population (%)"
        labels = {"Population_Neg": x_axis_title, "Age Group": "Age Group"}
        hover_unit = x_axis_title
        # Use the data-driven max with padding for readable axis breathing room.
        actual_max = long["Population"].abs().max()
        xmax = max(15.0, float(actual_max) * 1.2)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

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
        labels=labels,
        width=1000,
        height=800,
        custom_data=["Population_Abs"],
    )

    fig.update_layout(
        hovermode="y unified",
        hoverlabel=dict(
            namelength=-1,
            bgcolor="white",
            bordercolor="rgba(0,0,0,0)",
            font_family="Arial",
            font_size=12,
            font_color="black",
        ),
    )

    # Plotly Express generates a hovertemplate per trace; override for consistent formatting.
    male_template = f"Male<br>{hover_unit} = %{{customdata[0]:.1f}}<extra></extra>"
    female_template = f"Female<br>{hover_unit} = %{{customdata[0]:.1f}}<extra></extra>"

    for trace in fig.data:
        if trace.name == "Male":
            trace.hovertemplate = male_template
        elif trace.name == "Female":
            trace.hovertemplate = female_template

    # Animated figures store trace copies in frames; keep hovertemplates aligned there too.
    if hasattr(fig, "frames") and fig.frames:
        for frame in fig.frames:
            for trace in frame.data:
                if trace.name == "Male":
                    trace.hovertemplate = male_template
                elif trace.name == "Female":
                    trace.hovertemplate = female_template

    years = sorted(long["Year"].unique())
    if start_mode == "last":
        initial_year = years[-1] if len(years) > 0 else ""
    elif start_mode == "off":
        initial_year = years[0] if len(years) > 0 else ""
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

    if mode == "abs":
        tickvals = [float(v) for v in range(-int(xmax), int(xmax) + 5, 5)]
        ticktext = [str(int(abs(v))) for v in tickvals]
    else:
        # Symmetric ticks with absolute-value labels for percent view.
        step = 2.5
        pos_vals = [round(v * step, 10) for v in range(0, int(xmax / step) + 1)]
        tickvals = [-v for v in reversed(pos_vals[1:])] + pos_vals
        ticktext = [f"{abs(v):g}%" for v in tickvals]

    fig.update_layout(
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext,
            range=[-xmax, xmax],
            title=x_axis_title,
        ),
        yaxis=dict(autorange="reversed"),
        bargap=0.05,
        legend_title_text="Sex",
        margin=dict(l=80, r=40, t=80, b=300),
    )

    # Reposition slider and the default play button so controls sit under the chart.
    if fig.layout.sliders:
        s = fig.layout.sliders[0]
        s.len = 0.80
        s.x = 0.5 - s.len / 2
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

        dropdown_x = s.x + s.len
        dropdown_y = s.y + 0.02

    # Replace Plotly's built-in menus with a custom year dropdown + play/pause/stop buttons.
    if fig.layout.updatemenus:
        fig.layout.updatemenus = []

    # Avoid implicit transition on initial render.
    fig.layout.transition = fig.layout.transition or {}
    fig.layout.transition.duration = 0

    # Set the initial slider position.
    if fig.layout.sliders:
        if start_mode == "last":
            fig.layout.sliders[0].active = len(fig.frames) - 1
        elif start_mode == "off":
            fig.layout.sliders[0].active = 0
        else:
            fig.layout.sliders[0].active = 0

    # Extra line traces are used for year-by-year comparison overlays.
    for year in years:
        year_data = long[long["Year"] == year]
        male_data = year_data[year_data["Sex"] == "Male"]
        female_data = year_data[year_data["Sex"] == "Female"]

        fig.add_trace(
            go.Scatter(
                x=male_data["Population_Neg"],
                y=male_data["Age Group"],
                mode="lines+markers",
                line=dict(color="black", width=2),
                marker=dict(size=4, color="black"),
                opacity=0.5,
                visible=False,
                showlegend=False,
                customdata=male_data[["Year", "Population"]].to_numpy(),
                hovertemplate=f"Male (%{{customdata[0]}})<br>{hover_unit} : %{{customdata[1]:.1f}}<extra></extra>",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=female_data["Population_Neg"],
                y=female_data["Age Group"],
                mode="lines+markers",
                line=dict(color="black", width=2),
                marker=dict(size=4, color="black"),
                opacity=0.5,
                visible=False,
                showlegend=False,
                customdata=female_data[["Year", "Population"]].to_numpy(),
                hovertemplate=f"Female (%{{customdata[0]}})<br>{hover_unit} : %{{customdata[1]:.1f}}<extra></extra>",
            )
        )

    year_options = []
    num_years = len(years)
    for i, year in enumerate(years):
        visible = [True, True] + [False] * (2 * num_years)
        visible[2 + 2 * i] = True
        visible[2 + 2 * i + 1] = True
        year_options.append(dict(label=str(year), method="restyle", args=[{"visible": visible}]))

    off_visible = [True, True] + [False] * (2 * num_years)
    year_options.insert(0, dict(label="Off", method="restyle", args=[{"visible": off_visible}]))

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

    pause_button = dict(
        label="Pause",
        method="animate",
        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
    )

    stop_button = dict(label="Stop", method="restyle", args=[{"visible": off_visible}])

    play_btn = play_button.copy()
    play_btn["label"] = "▶"
    pause_btn = pause_button.copy()
    pause_btn["label"] = "⏸"

    stop_btn = stop_button.copy()
    stop_btn["label"] = "⏹"
    # Reset stops at the first frame (fast jump, no animation).
    if years:
        stop_btn = dict(
            label="⏹",
            method="animate",
            args=[[str(years[0])], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
        )

    os_slider_x = 0.5
    if fig.layout.sliders:
        os_slider_x = fig.layout.sliders[0].x

    if fig.layout.sliders:
        controls_y = s.y + 0.008
    else:
        controls_y = -0.09

    controls_menu = dict(
        type="buttons",
        direction="left",
        showactive=False,
        buttons=[play_btn, pause_btn, stop_btn],
        x=max(0.02, os_slider_x - 0.02),
        y=controls_y,
        xanchor="left",
        yanchor="bottom",
        font=dict(size=16),
    )

    dropdown_x = locals().get("dropdown_x", 0.92)
    dropdown_y = locals().get("dropdown_y", -0.15)
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=year_options,
                x=dropdown_x,
                y=dropdown_y,
                xanchor="center",
                yanchor="bottom",
                direction="down",
                font=dict(size=16),
            ),
            controls_menu,
        ]
    )

    current_annotations = list(fig.layout.annotations) if fig.layout.annotations else []
    label_x = locals().get("dropdown_x", 0.92)
    label_y = locals().get("dropdown_y", -0.15) + 0.10
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
            font=dict(size=16, color="black"),
        )
    )
    fig.update_layout(annotations=current_annotations)

    return fig

def build_pyramid_figure_abs(long: pd.DataFrame, age_order: List[str], start_mode: str = "last") -> go.Figure:
    return build_pyramid_figure(long, age_order, mode="abs", start_mode=start_mode)


def build_pyramid_figure_pct(long: pd.DataFrame, age_order: List[str], start_mode: str = "last") -> go.Figure:
    return build_pyramid_figure(long, age_order, mode="pct", start_mode=start_mode)

