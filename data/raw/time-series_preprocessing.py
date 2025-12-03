import re
import os
import pandas as pd
import numpy as np

# Paths
HERE = os.path.dirname(__file__)
INFILE = os.path.join(HERE, 'dsec_dataset.csv')
OUTDIR = os.path.join(os.path.dirname(HERE), 'processed')
OUTFILE = os.path.join(OUTDIR, 'macao_demographics_1999_2024.csv')

# Column names inferred from the dataset / image
original_columns = [
    'Year',
    'Total population',          # '000
    'Male',                      # '000
    'Female',                    # '000
    'Total population (dup)',    # duplicate — will be dropped
    'Below Age 15',              # '000
    'Age 15-24',
    'Age 25-34',
    'Age 35-44',
    'Age 45-54',
    'Age 55-64',
    'Age 65 and above',          # '000
    'Annual growth rate',        # %
    'Non-resident workers total',# No.
    'Chinese mainland',          # No.
    'Philippines',
    'Vietnam',
    'Construction',              # No.
    'Hotels, Restaurants & Similar Activities',
    'Recreational, Cultural, Gaming & Other Services',
    'New arrivals from Chinese mainland with one-way permit',  # No.
    'Crude birth rate',          # o/oo
    'Crude mortality rate',
    'Rate of natural increase',
    'Population density',        # '000/km²
    'Macao Peninsula a',         # '000/km²
    'Taipa a',
    'Coloane a',
    'Note'                       # annotation column (e.g., ~, 0#)
]

# Helper functions

def find_data_start_row(filepath):
    """Find the first row index (0-based) where the first column looks like a 4-digit year."""
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            # strip leading/trailing whitespace and potential starting commas
            first_cell = line.split(',')[0].strip().strip('"')
            if re.match(r'^\d{4}$', first_cell):
                return i
    return None


def clean_value(x):
    """Clean a string value: remove thousands separators, trim quotes, map ~ or 0# to NaN."""
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s == '~' or s == '0#' or s == '':
        return np.nan
    # Remove enclosing quotes if present
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    # Remove commas used as thousands separators
    s = s.replace(',', '')
    # Convert dashes or other annotation-only values to NaN
    if re.match(r'^[^0-9.+-]+$', s):
        return np.nan
    return s


if __name__ == '__main__':
    if not os.path.exists(INFILE):
        raise FileNotFoundError(f"Input file not found: {INFILE}")

    start_row = find_data_start_row(INFILE)
    if start_row is None:
        raise RuntimeError('Could not find the data start row by year detection')

    # Read the data starting from the detected row
    # Use engine='python' to be permissive about inconsistent columns
    df = pd.read_csv(INFILE, skiprows=start_row, header=None, encoding='utf-8', engine='python')

    # Trim or extend df columns to match the expected header length
    ncols_needed = len(original_columns)
    if df.shape[1] < ncols_needed:
        # pad with extra unnamed columns
        for c in range(df.shape[1], ncols_needed):
            df[c] = np.nan
    elif df.shape[1] > ncols_needed:
        df = df.iloc[:, :ncols_needed]

    df.columns = original_columns[: df.shape[1]]

    # Drop duplicate/annotation columns we don't want, if present
    df = df.drop(columns=['Total population (dup)', 'Note'], errors='ignore')

    # Clean values across the frame
    df = df.applymap(clean_value)

    # Convert Year to numeric
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

    # Cast numeric columns to numeric types where possible
    for col in df.columns:
        if col == 'Year':
            continue
        # Attempt numeric conversion
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Replace missing Annual growth rate values with 0.05 (user-specified)
    if 'Annual growth rate' in df.columns:
        df['Annual growth rate'] = df['Annual growth rate'].fillna(0.05)

    # Optional: filter for 1999–2024 as in the prospectus / image
    df = df[(df['Year'] >= 1999) & (df['Year'] <= 2024)].copy()

    # Ensure output directory exists
    os.makedirs(OUTDIR, exist_ok=True)

    # Save cleaned CSV
    df.to_csv(OUTFILE, index=False)
    print(f"Cleaned file written to: {OUTFILE}")
