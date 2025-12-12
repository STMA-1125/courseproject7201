"""Calculation utilities for demographic metrics.

Provides functions for computing dependency ratios, median ages,
and formatting display values.
"""
import pandas as pd
import numpy as np
import logging

# Configure logging
logger = logging.getLogger(__name__)

def format_yoy_label(value, unit='', decimals=1, use_sign=False):
    """Format a year-on-year delta value for UI display.

    Args:
        value: Delta value (percent or absolute) or None/NaN.
        unit: Unit suffix to append (e.g., '%').
        decimals: Number of decimal places.
        use_sign: If True, use +/- prefix and Δ for zero. If False, use arrows.

    Returns:
        A short string label such as '+1.2%', '↓0.8', or 'YoY change'.
    """
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "YoY change"
        val = round(float(value), decimals)
        if use_sign:
            # If zero, show delta sign (Δ0.0). For positive/negative show +/− as requested.
            num = f"{abs(val):.{decimals}f}"
            if float(val) == 0.0:
                return f"Δ{num}{unit}"
            sign = '+' if val > 0 else '-'
            return f"{sign}{num}{unit}"
        else:
            arrow = 'Δ' if val == 0 else ('↑' if val > 0 else '↓')
            num = f"{abs(val):.{decimals}f}"
            return f"{arrow}{num}{unit}"
    except Exception:
        return "YoY change"

def get_yoy_style(value):
    """Return the style dictionary for a YoY pill (Streamlit Elements / MUI).

    Args:
        value: Numeric delta value or None/NaN.

    Returns:
        Dict of CSS-like styles for MUI Typography.
    """
    base = {"fontWeight": "700", "fontSize": "0.95rem", "padding": "4px 10px", "borderRadius": "18px", "display": "inline-block"}
    if value is None or (isinstance(value, float) and pd.isna(value)):
        base.update({"background": "rgba(240,240,240,0.4)", "color": "#555"})
    elif value > 0:
        base.update({"background": "rgba(46,204,113,0.12)", "color": "#27ae60"})
    elif value < 0:
        base.update({"background": "rgba(231,76,60,0.08)", "color": "#e74c3c"})
    else:
        base.update({"background": "rgba(240,240,240,0.4)", "color": "#555"})
    return base

def compute_dependency_ratio(row):
    """Compute total dependency ratio for one row.

    Dependency ratio is defined as:
        $\frac{\text{(0–14) + (65+)}}{\text{(15–64)}} \times 100$

    Args:
        row: A mapping-like row (e.g., pandas Series).

    Returns:
        Dependency ratio as a float, or None when not computable.
    """
    try:
        young = row.get('Below Age 15', 0) or 0
        old = row.get('Age 65 and above', 0) or 0
        working = 0
        for band in ['Age 15-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-64']:
            working += row.get(band, 0) or 0
        if working <= 0:
            return None
        return ((young + old) / working) * 100
    except Exception:
        return None

def compute_median_age(row):
    """Approximate median age from aggregated age bands.

    Uses linear interpolation within the age band containing the median.

    Args:
        row: A mapping-like row (e.g., pandas Series) with age-band counts.

    Returns:
        Median age estimate (years), rounded to 1 decimal, or None.
    """
    try:
        bands = [
            (0, 14, row.get('Below Age 15', 0) or 0),
            (15, 24, row.get('Age 15-24', 0) or 0),
            (25, 34, row.get('Age 25-34', 0) or 0),
            (35, 44, row.get('Age 35-44', 0) or 0),
            (45, 54, row.get('Age 45-54', 0) or 0),
            (55, 64, row.get('Age 55-64', 0) or 0),
            (65, 100, row.get('Age 65 and above', 0) or 0),
        ]
        total = sum([b[2] for b in bands])
        if total <= 0:
            return None
        median_pos = total / 2.0
        cum = 0.0
        for lower, upper, count in bands:
            if count == 0:
                continue
            if cum + count >= median_pos:
                # Interpolate within this band
                within = median_pos - cum
                frac = within / count
                age = lower + frac * (upper - lower)
                return round(age, 1)
            cum += count
        # If we reach here, median is in last bucket; return its midpoint
        last = bands[-1]
        return round((last[0] + last[1]) / 2.0, 1)
    except Exception:
        return None

def compute_dependency_ratio_vectorized(df):
    """Vectorized dependency ratio computation for a demographics dataframe.

    Args:
        df: Dataframe containing age-band columns.

    Returns:
        A pandas Series of dependency ratios.
    """
    try:
        young = df['Below Age 15'].fillna(0)
        old = df['Age 65 and above'].fillna(0)
        
        # Sum working age population (15-64)
        working_cols = ['Age 15-24', 'Age 25-34', 'Age 35-44', 'Age 45-54', 'Age 55-64']
        working = df[working_cols].fillna(0).sum(axis=1)
        
        # Avoid division by zero
        ratio = ((young + old) / working.replace(0, np.nan)) * 100
        return ratio
    except Exception as e:
        # Fallback to row-wise computation if vectorization fails
        return df.apply(compute_dependency_ratio, axis=1)

def compute_median_age_vectorized(df):
    """Row-wise median age estimate for a demographics dataframe.

    Note:
        This implementation iterates rows because the interpolation step is
        band-dependent. It is wrapped in a try/except with a row-wise fallback
        for robustness.

    Args:
        df: Dataframe containing age-band columns.

    Returns:
        A pandas Series of median age estimates.
    """
    try:
        bands = [
            (0, 14, 'Below Age 15'),
            (15, 24, 'Age 15-24'),
            (25, 34, 'Age 25-34'),
            (35, 44, 'Age 35-44'),
            (45, 54, 'Age 45-54'),
            (55, 64, 'Age 55-64'),
            (65, 100, 'Age 65 and above'),
        ]
        
        median_ages = []
        for idx, row in df.iterrows():
            band_data = [(lower, upper, row.get(col, 0) or 0) for lower, upper, col in bands]
            total = sum([b[2] for b in band_data])
            
            if total <= 0:
                median_ages.append(None)
                continue
                
            median_pos = total / 2.0
            cum = 0.0
            found = False
            
            for lower, upper, count in band_data:
                if count == 0:
                    continue
                if cum + count >= median_pos:
                    within = median_pos - cum
                    frac = within / count
                    age = lower + frac * (upper - lower)
                    median_ages.append(round(age, 1))
                    found = True
                    break
                cum += count
            
            if not found:
                last = band_data[-1]
                median_ages.append(round((last[0] + last[1]) / 2.0, 1))
        
        return pd.Series(median_ages, index=df.index)
    except Exception as e:
        # Fallback to row-wise computation
        return df.apply(compute_median_age, axis=1)
