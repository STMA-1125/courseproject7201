import pandas as pd

def format_yoy_label(value, unit='', decimals=1, use_sign=False):
    """Return label like '↑0.2%' or 'Δ0.0 yrs' rounded to decimals.
    If value is None or NaN, return 'YoY change'"""
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
            # ensure no leading + sign for positive; arrow covers sign
            num = f"{abs(val):.{decimals}f}"
            return f"{arrow}{num}{unit}"
    except Exception:
        return "YoY change"

def get_yoy_style(value):
    """Return style dict for the YoY pill for MUI Typography"""
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
    """Compute total dependency ratio (0-14 & 65+) / 15-64 * 100"""
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
    """Approximate median age via interpolation over age groups.

    Age groups assumed:
    - Below Age 15: 0-14
    - Age 15-24: 15-24
    - Age 25-34: 25-34
    - Age 35-44: 35-44
    - Age 45-54: 45-54
    - Age 55-64: 55-64
    - Age 65 and above: 65-100 (upper-bound assumed 100)
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