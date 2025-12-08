import plotly.graph_objects as go
import numpy as np
import pandas as pd
from pathlib import Path

def create_bubble_chart():
    # Load data
    data_path = Path("data/processed/macao_demographics_1999_2024.csv")
    
    # Fallback if running from different directory
    if not data_path.exists():
        data_path = Path("../data/processed/macao_demographics_1999_2024.csv")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Could not find data file at {data_path}")

    df = pd.read_csv(data_path)

    # Clean column names if necessary 
    df.columns = df.columns.str.strip()
    
    # Calculate percentages
    df['Elderly_Ratio'] = (df['Age 65 and above'] / df['Total population']) * 100
    df['Children_Ratio'] = (df['Below Age 15'] / df['Total population']) * 100
    
    # Calculate Gap (Elderly % - Children %)
    df['Gap'] = df['Elderly_Ratio'] - df['Children_Ratio']


    pop_raw = df['Total population']
    pop_min = pop_raw.min()
    pop_max = pop_raw.max()
    pop_norm = (pop_raw - pop_min) / (pop_max - pop_min)
    size_power = 2.0  
    min_diameter = 60  
    desired_ratio = 1.6  

    # Apply power transform to normalized pop values
    pop_norm_power = pop_norm ** size_power

    # Values for 1999 and 2024 (should exist); use numeric Year values
    s1 = pop_norm_power.loc[df['Year'] == 1999.0].values
    s2 = pop_norm_power.loc[df['Year'] == 2024.0].values
    if len(s1) == 0 or len(s2) == 0:
        # fallback: ensure we still have a sensible mapping if years are missing
        max_diameter = min_diameter * desired_ratio
        size_pixels = min_diameter + pop_norm_power * (max_diameter - min_diameter)
    else:
        s1 = float(s1[0])
        s2 = float(s2[0])
        denom = (s2 - desired_ratio * s1)
        if denom <= 1e-6:
            max_diameter = min_diameter * desired_ratio
            size_pixels = min_diameter + pop_norm_power * (max_diameter - min_diameter)
        else:
            A = (desired_ratio - 1.0) * min_diameter / denom
            if A <= 0 or A > 300:
                A = int(min_diameter * (desired_ratio - 1.0))
                if A < 1:
                    A = int(min_diameter * 0.6)
            size_pixels = min_diameter + pop_norm_power * A
    
    # Create hover text with detailed information
    hover_text = [
        f"<b>Year: {int(year)}</b><br>" +
        f"Elderly %: {e:.1f}%<br>" +
        f"Children %: {c:.1f}%<br>" +
        f"Gap: {g:.1f}%<br>" +
        f"Total Population: {p:.1f}k"
        for year, e, c, g, p in zip(
            df['Year'], 
            df['Elderly_Ratio'], 
            df['Children_Ratio'], 
            df['Gap'],
            df['Total population']
        )
    ]

    # Create figure
    fig = go.Figure()

    # Add scatter trace with bubble chart styling
    fig.add_trace(go.Scatter(
        x=df['Gap'],
        y=df['Children_Ratio'],
        mode='markers+text',
        text=df['Year'].astype(int).astype(str),
        textposition="middle center",
        textfont=dict(
            family="Arial, sans-serif",
            size=10,
            color="black",
            weight="bold"
        ),
        hovertemplate="%{hovertext}<extra></extra>",
        hovertext=hover_text,
        marker=dict(
            size=size_pixels,
            sizemode='diameter',
            sizemin=18,
            color=df['Year'],
            colorscale=[
                [0.0, '#4169B5'],
                [0.2, '#5B8FC4'],
                [0.35, '#87BADB'],
                [0.5, '#C8D6E8'],
                [0.6, '#F5E5B8'],
                [0.7, '#F0C088'],
                [0.8, '#E87461'],
                [0.9, '#D84855'],
                [1.0, '#B8193D']
            ],
            showscale=True,
            opacity=0.8,  # Reduced opacity for better overlap visibility
            line=dict(width=2, color='white'),
            colorbar=dict(
                title=dict(
                    text="<b>Year</b>",
                    side="top",
                    font=dict(size=12, color='#1a1a1a', family="Arial, sans-serif")
                ),
                thickness=15,
                len=0.6,
                x=1.02,
                tickmode="array",
                tickvals=[1999, 2004, 2009, 2014, 2019, 2024],
                ticktext=["1999", "2004", "2009", "2014", "2019", "2024"],
                ticks="outside",
                ticklen=5,
                tickfont=dict(size=10, color='#1a1a1a', family="Arial, sans-serif")
            )
        )
    ))

    # Add reference lines
    # Vertical line at x=0 (Balance point)
    fig.add_shape(
        type="line",
        x0=0, y0=8, x1=0, y1=25,
        line=dict(color="rgba(100, 100, 100, 0.5)", width=1.5, dash="solid")
    )

    fig.update_layout(
        title=dict(
            text="<b>Macao Population Aging and Children Decline Trend</b><br>" +
                 "<span style='font-size: 13px; font-weight: normal;'>Age Structure Evolution: Elderly vs Children (1999-2024)</span>",
            x=0.5,
            y=0.96,
            xanchor='center',
            yanchor='top',
            font=dict(size=18, color='#1a1a1a', family="Arial, sans-serif")
        ),
        xaxis=dict(
            title=dict(
                text="<b>Left: Young Society | Center: Balance | Right: Aged Society</b><br>Elderly % - Children %",
                font=dict(size=11, color='#1a1a1a', family="Arial, sans-serif")
            ),
            tickfont=dict(family="Arial, sans-serif", size=10, color='#1a1a1a'),
            range=[-20, 6],
            zeroline=False,
            showgrid=True,
            gridcolor='rgba(220, 220, 220, 0.4)',
            gridwidth=0.5
        ),
        yaxis=dict(
            title=dict(
                text="<b>Children Population Ratio (%)</b><br><span style='font-size: 10px; font-weight: normal;'>Percentage of Children</span>",
                font=dict(size=11, color='#1a1a1a', family="Arial, sans-serif")
            ),
            tickfont=dict(family="Arial, sans-serif", size=10, color='#1a1a1a'),
            range=[8, 25],
            showgrid=True,
            gridcolor='rgba(220, 220, 220, 0.4)',
            gridwidth=0.5,
            zeroline=False
        ),
        plot_bgcolor='#F8F8F8',  
        paper_bgcolor='white',
        width=1000,
        height=700,
        margin=dict(l=90, r=120, t=100, b=90),
        hovermode='closest'
    )

    return fig

if __name__ == "__main__":
    fig = create_bubble_chart()
    
    # Save as HTML
    # output_path = "graphs/bubble_chart_interactive.html"
    # fig.write_html(output_path)
    # print(f"Interactive bubble chart saved to: {output_path}")
    
    import pandas as _pd
    df_local = _pd.read_csv("data/processed/macao_demographics_1999_2024.csv")
    df_local.columns = df_local.columns.str.strip()
    # Recompute sizes using same logic to fetch the computed 'size_pixels'
    pop_raw = df_local['Total population']
    pop_min = pop_raw.min()
    pop_max = pop_raw.max()
    pop_norm = (pop_raw - pop_min) / (pop_max - pop_min)
    pop_norm_power = pop_norm ** 2.0
    min_diameter = 22
    desired_ratio = 1.6
    s1 = pop_norm_power.loc[df_local['Year'] == 1999.0].values
    s2 = pop_norm_power.loc[df_local['Year'] == 2024.0].values
    if len(s1) and len(s2):
        s1 = float(s1[0]); s2 = float(s2[0])
        denom = (s2 - desired_ratio * s1)
        if denom <= 1e-6:
            max_diameter = min_diameter * desired_ratio
            size_pixels_local = min_diameter + pop_norm_power * (max_diameter - min_diameter)
        else:
            A = (desired_ratio - 1.0) * min_diameter / denom
            if A <= 0 or A > 200:
                A = 66
            size_pixels_local = min_diameter + pop_norm_power * A
        s1999_px = float(size_pixels_local.loc[df_local['Year'] == 1999.0].values[0])
        s2024_px = float(size_pixels_local.loc[df_local['Year'] == 2024.0].values[0])
        print(f"Diameter 1999: {s1999_px:.2f}px, 2024: {s2024_px:.2f}px, ratio: {s2024_px/s1999_px:.3f}, A={A:.2f}")
    fig.show()
