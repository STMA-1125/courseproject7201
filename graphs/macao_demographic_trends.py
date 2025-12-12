"""Demographic trends figure builder.

Provides `build_trends_figure(df=None)` which returns a Plotly figure for the main
demographic trends view (indices + ratios) used by the Streamlit dashboard.

This module is import-friendly (no Streamlit dependency). When run as a script it
builds the figure for local preview.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Legacy sample dataset (kept as a reference snapshot).
data = {
    'Year': [1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 
           2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    'Total_Population': [429.632, 437.9, 436.7, 440.515, 446.7, 462.6, 484.3, 513.4, 538.1, 549.2, 533.259, 
             540.578, 557.365, 582, 607.5, 636.2, 646.8, 644.9, 653.1, 667.4, 679.6, 683.1, 683.2, 672.8, 683.7, 688.3],
    'Total_Area': [23.8, 25.4, 25.8, 26.8, 27.3, 27.5, 28.2, 28.6, 29.2, 29.2, 29.5, 
             29.7, 29.9, 29.9, 30.3, 30.3, 30.4, 30.5, 30.8, 32.9, 32.9, 32.9, 33, 33.3, 33.3, 33.3],
    'Non_Resident_Workers': [32183, 27221, 25925, 23460, 24970, 27736, 18499, 64673, 85207, 92161, 74905, 
               75813, 94028, 110552, 137838, 170346, 181646, 177638, 179456, 188480, 196538, 177663, 171098, 154912, 176661, 182542],
    'Aging_Ratio': [7, 7.97, 7.37, 7.42, 7.5, 7.44, 7.29, 7.01, 7.12, 7.19, 7.25, 
                7.37, 7.34, 7.56, 8.02, 8.42, 8.98, 9.83, 10.55, 11.1, 11.89, 12.93, 12.18, 13.29, 13.98, 14.56]
}

def _default_df() -> pd.DataFrame:
    """Load the processed demographics CSV and normalize column names.

    Returns:
        A dataframe with the derived columns required by `build_trends_figure`.
    """
    df = pd.read_csv('data/processed/macao_demographics_1999_2024.csv')
    # Normalize columns
    df['Total_Population'] = df['Total population']
    df['Non_Resident_Workers'] = df['Non-resident workers total']
    df['Population_Density'] = df['Population density']
    df['Aging_Ratio'] = (df['Age 65 and above'] / df['Total population']) * 100
    # Compute indices
    base_year = 1999
    base_population = df.loc[df['Year'] == base_year, 'Total_Population'].values[0]
    base_density = df.loc[df['Year'] == base_year, 'Population_Density'].values[0]
    df['Population_Index'] = (df['Total_Population'] / base_population) * 100
    df['Density_Index'] = (df['Population_Density'] / base_density) * 100
    df['Non_Resident_Ratio'] = (df['Non_Resident_Workers'] / (df['Total_Population'] * 1000)) * 100
    return df


def build_trends_figure(df=None):
    """Build and return the Plotly figure for Macao demographic trends.

    Args:
        df (pd.DataFrame, optional): Dataframe with required columns (Year, Total_Population, Total_Area, Non_Resident_Workers, Aging_Ratio).
                                     If None, the internal sample dataset will be used.

    Returns:
        plotly.graph_objects.Figure: An interactive Plotly figure.
    """
    # Accept different column names from the processed CSV by normalizing to expected keys.
    if df is None:
        df = _default_df()
    else:
        # Make a copy to avoid mutating the caller's DataFrame
        df = df.copy()

        # Column standardization
        if 'Total population' in df.columns and 'Total_Population' not in df.columns:
            df['Total_Population'] = df['Total population']
        if 'Non-resident workers total' in df.columns and 'Non_Resident_Workers' not in df.columns:
            df['Non_Resident_Workers'] = df['Non-resident workers total']
        if 'Population density' in df.columns and 'Population_Density' not in df.columns:
            df['Population_Density'] = df['Population density']
        # 'Age 65 and above' is provided as counts (thousand); convert to percent if needed
        if 'Age 65 and above' in df.columns and 'Aging_Ratio' not in df.columns and 'Total_Population' in df.columns:
            try:
                df['Aging_Ratio'] = (df['Age 65 and above'] / df['Total_Population']) * 100
            except Exception:
                # If the total population is in thousands, multiply accordingly
                df['Aging_Ratio'] = (df['Age 65 and above'] / (df['Total_Population'])) * 100
        # If Population_Density not available but Total_Area exists, compute it
        if 'Population_Density' not in df.columns and 'Total_Area' in df.columns and 'Total_Population' in df.columns:
            df['Population_Density'] = (df['Total_Population'] * 1000) / df['Total_Area']

        # Compute index columns (Population_Index & Density_Index) if missing
        if 'Population_Index' not in df.columns and 'Total_Population' in df.columns:
            base_year = 1999
            try:
                base_population = df.loc[df['Year'] == base_year, 'Total_Population'].values[0]
                df['Population_Index'] = (df['Total_Population'] / base_population) * 100
            except Exception:
                # Fallback: use first value as base
                base_population = df['Total_Population'].iloc[0]
                df['Population_Index'] = (df['Total_Population'] / base_population) * 100
        if 'Density_Index' not in df.columns and 'Population_Density' in df.columns:
            base_year = 1999
            try:
                base_density = df.loc[df['Year'] == base_year, 'Population_Density'].values[0]
                df['Density_Index'] = (df['Population_Density'] / base_density) * 100
            except Exception:
                base_density = df['Population_Density'].iloc[0]
                df['Density_Index'] = (df['Population_Density'] / base_density) * 100

        # Compute Non_Resident_Ratio if needed (Non_Resident_Workers / total population)
        if 'Non_Resident_Ratio' not in df.columns and 'Non_Resident_Workers' in df.columns and 'Total_Population' in df.columns:
            df['Non_Resident_Ratio'] = (df['Non_Resident_Workers'] / (df['Total_Population'] * 1000)) * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    colors = {
        'population': '#1f77b4',      
        'density': '#9467bd',         
        'aging': '#ff7f0e',           
        'non_resident': '#8c564b'     
    }

    fig.add_trace(
        go.Scatter(x=df['Year'], y=df['Population_Index'],
                   name="Population Index (1999=100)", 
                   line=dict(color=colors['population'], width=3),
                   mode='lines+markers',
                   marker=dict(size=4),
                   hovertemplate="Year: %{x}<br>Population Index: %{y:.1f}<br>Actual Population: %{customdata}K<extra></extra>",
                   customdata=df['Total_Population']),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=df['Year'], y=df['Density_Index'],
                   name="Density Index (1999=100)", 
                   line=dict(color=colors['density'], width=2.5, dash='dash'),
                   mode='lines',
                   hovertemplate="Year: %{x}<br>Density Index: %{y:.1f}<br>Actual Density: %{customdata:.1f}k persons/km²<extra></extra>",
                   customdata=df['Population_Density']),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=df['Year'], y=df['Aging_Ratio'],
                   name="Aging Ratio (%)", 
                   line=dict(color=colors['aging'], width=2.5),
                   mode='lines+markers',
                   marker=dict(size=4, symbol='diamond'),
                   hovertemplate="Year: %{x}<br>Aging Ratio: %{y:.1f}%<extra></extra>"),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(x=df['Year'], y=df['Non_Resident_Ratio'],
                   name="Non-Resident Ratio (%)", 
                   line=dict(color=colors['non_resident'], width=2.5),
                   mode='lines+markers',
                   marker=dict(size=4, symbol='square'),
                   hovertemplate="Year: %{x}<br>Non-Resident Ratio: %{y:.1f}%<extra></extra>"),
        secondary_y=True,
    )

    events = [
        dict(year=2002, text="Gaming Liberalization"),
        dict(year=2006, text="Labor Surge"),
        dict(year=2014, text="Gaming Peak"),
        dict(year=2020, text="COVID-19"),
        dict(year=2023, text="Economic Recovery")
    ]

    for i, event in enumerate(events):
        fig.add_annotation(
            x=event['year'],
            y=0.02,
            yref="paper",
            text=event['text'],
            showarrow=False,
            textangle=0,
            font=dict(size=9, color='#666666'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#cccccc',
            borderwidth=1,
            borderpad=2
        )

    fig.update_xaxes(
        title_text="Year", 
        tickangle=0,
        dtick=2,
        showgrid=True,
        gridwidth=0.5,
        gridcolor='rgba(0,0,0,0.1)'
    )

    # Left Y-axis: Population and Density indices
    fig.update_yaxes(
        title_text="Index (1999=100)", 
        range=[90, 180],
        secondary_y=False,
        showgrid=True,
        gridwidth=0.5,
        gridcolor='rgba(0,0,0,0.1)'
    )

    # Right Y-axis: Ratio data
    fig.update_yaxes(
        title_text="Ratio (%)", 
        range=[0, 35],
        secondary_y=True,
        showgrid=False
    )

    fig.update_layout(
        title=dict(
            text="Macao Demographic Trends Analysis (1999-2024)",
            x=0.5,
            font=dict(size=16, color='#333333'),
            xanchor='center'
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="center", 
            x=0.5,
            font=dict(size=11)
        ),
        height=500,
        margin=dict(t=80, l=60, r=60, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        showlegend=True,
        xaxis=dict(showline=True, linewidth=1, linecolor='black'),
        yaxis=dict(showline=True, linewidth=1, linecolor='black'),
        yaxis2=dict(showline=True, linewidth=1, linecolor='black')
    )
    return fig


if __name__ == "__main__":
    fig = build_trends_figure()


