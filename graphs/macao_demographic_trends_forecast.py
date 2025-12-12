"""Demographic forecast figure builder.

Builds a Plotly figure projecting Macao's population and aging ratio through 2035
under baseline/high/low scenarios.

The forecast is intentionally simple (linear interpolation) and is designed for
dashboard storytelling rather than formal demographic modeling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Fallback historical series used when a dataframe is not provided.
historical_years = list(range(1999, 2025))
historical_data = {
    'Year': historical_years,
    'Total_Population': [429.632, 437.9, 436.7, 440.515, 446.7, 462.6, 484.3, 513.4, 538.1, 549.2, 533.259, 
                        540.578, 557.365, 582, 607.5, 636.2, 646.8, 644.9, 653.1, 667.4, 679.6, 683.1, 683.2, 672.8, 683.7, 688.3],
    'Aging_Ratio': [7, 7.97, 7.37, 7.42, 7.5, 7.44, 7.29, 7.01, 7.12, 7.19, 7.25, 
                   7.37, 7.34, 7.56, 8.02, 8.42, 8.98, 9.83, 10.55, 11.1, 11.89, 12.93, 12.18, 13.29, 13.98, 14.56]
}

df_historical = pd.DataFrame(historical_data)

future_years = list(range(2025, 2036))

def generate_forecast_baseline(last_pop, last_aging):
    """Baseline scenario: moderate growth with gradual aging."""
    pop_2035 = 720
    population = np.linspace(last_pop, pop_2035, len(future_years))
    aging_2035 = 18.0
    aging = np.linspace(last_aging, aging_2035, len(future_years))
    return population, aging

def generate_forecast_high(last_pop, last_aging):
    """High-growth scenario: higher population with slower aging."""
    pop_2035 = 780
    population = np.linspace(last_pop, pop_2035, len(future_years))
    aging_2035 = 16.5
    aging = np.linspace(last_aging, aging_2035, len(future_years))
    return population, aging

def generate_forecast_low(last_pop, last_aging):
    """Low-growth scenario: lower population with faster aging."""
    pop_2035 = 650
    population = np.linspace(last_pop, pop_2035, len(future_years))
    aging_2035 = 20.5
    aging = np.linspace(last_aging, aging_2035, len(future_years))
    return population, aging

def build_forecast_figure(df=None):
    """Build the forecast Plotly figure.

    Args:
        df: Optional processed demographics dataframe (preferred). When omitted,
            the module loads `data/processed/macao_demographics_1999_2024.csv`.

    Returns:
        A Plotly figure with historical series and 2025–2035 scenario envelopes.
    """

    # Use the provided dataframe for historical data if present.
    if df is not None:
        hist_df = df.copy()
        # Normalize columns if necessary
        if 'Total population' in hist_df.columns and 'Total_Population' not in hist_df.columns:
            hist_df['Total_Population'] = hist_df['Total population']
        if 'Age 65 and above' in hist_df.columns and 'Aging_Ratio' not in hist_df.columns and 'Total_Population' in hist_df.columns:
            # If Age 65 and above is absolute number (thousands), convert to a percentage of total
            try:
                hist_df['Aging_Ratio'] = (hist_df['Age 65 and above'] / hist_df['Total_Population']) * 100
            except Exception:
                # If densities/units mismatch, fallback to existing sample df
                hist_df = df_historical
    else:
        hist_df = pd.read_csv('data/processed/macao_demographics_1999_2024.csv')
        hist_df['Total_Population'] = hist_df['Total population']
        hist_df['Aging_Ratio'] = (hist_df['Age 65 and above'] / hist_df['Total population']) * 100

    last_pop = hist_df['Total_Population'].iloc[-1]
    last_aging = hist_df['Aging_Ratio'].iloc[-1]

    # Generate scenario curves anchored at the last historical point.
    pop_baseline, aging_baseline = generate_forecast_baseline(last_pop, last_aging)
    pop_high, aging_high = generate_forecast_high(last_pop, last_aging)
    pop_low, aging_low = generate_forecast_low(last_pop, last_aging)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    colors = {
        'population': '#3366CC',
        'aging': '#FF6633',
        'baseline': '#666666',
        'high': '#33CC33',
        'low': '#CC3333',
        'background': '#f8f9fa',
        'grid': '#e9ecef'
    }

    fig.add_trace(go.Scatter(
        x=future_years + future_years[::-1],
        y=list(pop_high) + list(pop_low)[::-1],
        fill='toself',
        fillcolor='rgba(51, 102, 204, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Population Range',
        showlegend=False,
        hoverinfo='skip'
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=future_years + future_years[::-1],
        y=list(aging_high) + list(aging_low)[::-1],
        fill='toself',
        fillcolor='rgba(255, 102, 51, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Aging Range',
        showlegend=False,
        hoverinfo='skip'
    ), secondary_y=True)

    fig.add_trace(
        go.Scatter(x=hist_df['Year'], y=hist_df['Total_Population'],
               name="Historical Population", 
               line=dict(color=colors['population'], width=4),
               mode='lines',
               hovertemplate="<b>📊 Historical</b><br>Year: %{x}<br>Population: <b>%{y}K</b><extra></extra>"),
        secondary_y=False,
)

    fig.add_trace(
        go.Scatter(x=hist_df['Year'], y=hist_df['Aging_Ratio'],
               name="Historical Aging", 
               line=dict(color=colors['aging'], width=4),
               mode='lines',
               hovertemplate="<b>👵 Historical</b><br>Year: %{x}<br>Aging Ratio: <b>%{y:.1f}%</b><extra></extra>"),
    secondary_y=True,
)

    fig.add_trace(
        go.Scatter(x=future_years, y=pop_baseline,
               name="Baseline Population",
               line=dict(color=colors['population'], width=3, dash='solid'),
               mode='lines',
               opacity=0.9,
               hovertemplate="<b>📈 Baseline</b><br>Year: %{x}<br>Population: <b>%{y:.0f}K</b><extra></extra>"),
    secondary_y=False,
)

    fig.add_trace(
        go.Scatter(x=future_years, y=aging_baseline,
               name="Baseline Aging",
               line=dict(color=colors['aging'], width=3, dash='solid'),
               mode='lines',
               opacity=0.9,
               hovertemplate="<b>📈 Baseline</b><br>Year: %{x}<br>Aging: <b>%{y:.1f}%</b><extra></extra>"),
    secondary_y=True,
)

    fig.add_trace(
        go.Scatter(x=future_years, y=pop_high,
               name="High Growth Population",
               line=dict(color=colors['high'], width=2, dash='dash'),
               mode='lines',
               hovertemplate="<b>🚀 High Growth</b><br>Year: %{x}<br>Population: <b>%{y:.0f}K</b><extra></extra>"),
    secondary_y=False,
)

    fig.add_trace(
        go.Scatter(x=future_years, y=aging_high,
               name="High Growth Aging", 
               line=dict(color=colors['high'], width=2, dash='dash'),
               mode='lines',
               hovertemplate="<b>🚀 High Growth</b><br>Year: %{x}<br>Aging: <b>%{y:.1f}%</b><extra></extra>"),
    secondary_y=True,
)

    fig.add_trace(
        go.Scatter(x=future_years, y=pop_low,
               name="Low Growth Population",
               line=dict(color=colors['low'], width=2, dash='dot'),
               mode='lines',
               hovertemplate="<b>📉 Low Growth</b><br>Year: %{x}<br>Population: <b>%{y:.0f}K</b><extra></extra>"),
    secondary_y=False,
)

    fig.add_trace(
        go.Scatter(x=future_years, y=aging_low,
               name="Low Growth Aging",
               line=dict(color=colors['low'], width=2, dash='dot'),
               mode='lines',
               hovertemplate="<b>📉 Low Growth</b><br>Year: %{x}<br>Aging: <b>%{y:.1f}%</b><extra></extra>"),
    secondary_y=True,
)

    # Visual boundary between historical and forecast segments.
    fig.add_vline(
        x=2024.5,
        line_width=2,
        line_dash="solid",
        line_color=colors['baseline'],
        opacity=0.7,
    )

    fig.update_xaxes(
    title_text="Year",
    tickangle=0,
    dtick=5,
    showgrid=True,
    gridwidth=1,
    gridcolor=colors['grid'],
    showline=True,
    linewidth=1,
    linecolor='black'
)

    fig.update_yaxes(
    title_text="Total Population (Thousand)",
    range=[400, 800],
    secondary_y=False,
    showgrid=True,
    gridwidth=1,
    gridcolor=colors['grid'],
    showline=True,
    linewidth=1,
    linecolor='black'
)

    fig.update_yaxes(
    title_text="Aging Ratio (%)",
    range=[5, 25],
    secondary_y=True,
    showgrid=False,
    showline=True,
    linewidth=1,
    linecolor='black'
)

    fig.update_layout(
    title=dict(
        text="Macao Demographic Outlook 1999-2035",
        x=0.5,
        font=dict(size=16, family="Arial, sans-serif", color="#2c3e50"),
        xanchor='center',
        y=0.96,
        yanchor='bottom'
    ),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        # Move the legend a little bit upward to avoid overlap with the plot
        y=1.05,
        xanchor="center",
        x=0.5,
        font=dict(size=11, family="Arial, sans-serif"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=colors['grid'],
        borderwidth=1
    ),
    height=600,  
    # Increase top margin so the title + legend (moved upward) are not clipped
    margin=dict(t=110, l=80, r=80, b=80), 
    plot_bgcolor=colors['background'],
    paper_bgcolor='white',
    font=dict(family="Arial, sans-serif", color="#2c3e50"),
    showlegend=True
    )

    fig.add_annotation(
    x=2028, y=750,  
    text="<b>Population Range</b><br>650K - 780K",
    showarrow=False,
    font=dict(color=colors['population'], size=10, family="Arial, sans-serif"),
    bgcolor="white",
    bordercolor=colors['population'],
    borderwidth=1,
    borderpad=3,
    opacity=0.9
    )

    fig.add_annotation(
    x=2028, y=19,  
    text="<b>Aging Range</b><br>16.5% - 20.5%", 
    showarrow=False,
    font=dict(color=colors['aging'], size=10, family="Arial, sans-serif"),
    bgcolor="white",
    bordercolor=colors['aging'],
    borderwidth=1,
    borderpad=3,
    opacity=0.9
    )

    fig.add_annotation(
    x=2024.5, y=0.05, yref="paper",  
    text="FORECAST START",
    showarrow=False,
    textangle=-90,
    font=dict(color=colors['baseline'], size=9, family="Arial, sans-serif", weight="bold"),
    bgcolor="white",
    bordercolor=colors['baseline'],
    borderwidth=1,
    borderpad=2
    )

    return fig


if __name__ == "__main__":
    ffig = build_forecast_figure()
  
