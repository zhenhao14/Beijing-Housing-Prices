"""Data cleaning for the Beijing housing dataset (BT2102 Assignment 3).

Pipeline position:
    raw Excel -> cleaning.py -> cleaned CSV -> featureengineering.py -> featured CSV -> EDA

Reads  : data/raw/BeijingHousingPrices.xlsx
Writes : data/processed/BeijingHousingPrices_cleaned.csv

Every rule below is declared once, at the top, so the team can review the decisions in one place.
In a notebook:  from cleaning import clean_dataframe, describe_clean
"""

from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Paths (this file is in src/, so the project root is one level up)
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "BeijingHousingPrices.xlsx"
OUTPUT_PATH = ROOT / "data" / "processed" / "BeijingHousingPrices_cleaned.csv"

# --------------------------------------------------------------------------- #
# DECLARATION: the intended type of every column
# --------------------------------------------------------------------------- #

# Dropped columns (if needed)
DROP_COLS = []

# Identifiers and free text: labels, never used in arithmetic
STRING_COLS = ["url", "id", "floor"]

# Dates
DATE_COLS = ["tradeTime"]

# Whole-number counts (>= 0). Fractions or negatives are invalid.
# NOTE: the appendix calls livingRoom "bedrooms" and drawingRoom "living rooms".
COUNT_COLS = ["followers", "livingRoom", "drawingRoom", "kitchen", "bathRoom"]

# Whole-number years with a plausible range (inclusive). The range is our assumption; adjust after EDA.
YEAR_COLS = {"constructionTime": (1906, 2016)}

# Categorical codes stored as integers. Anything outside the documented codes is invalid.
# These are labels, so a mean or standard deviation of them is meaningless.
CODE_COLS = {
    "buildingType": [1, 2, 3, 4],             # tower, bungalow, plate+tower, plate
    "renovationCondition": [1, 2, 3, 4],      # other, rough, simplicity, refined
    "buildingStructure": [1, 2, 3, 4, 5, 6],
    "elevator": [0, 1],
    "fiveYearsProperty": [0, 1],
    "subway": [0, 1],
    "district": list(range(1, 14)),           # 13 districts in the dataset
}

# Continuous measurements with a plausible range (inclusive; None = no bound)
FLOAT_COLS = {
    "Lng": (115.4, 117.6),                    # rough bounding box of Beijing
    "Lat": (39.4, 41.1),
    "totalPrice": (1, None),                  # in units of 10,000 CNY
    "price": (1, None),                       # CNY per sqm
    "square": (1, None),                      # sqm
    "ladderRatio": (0, None),
    "communityAverage": (0, None),            # looks like a price, not a head count: check in EDA
}

# Rows are dropped if any of these are missing AFTER conversion.
# Based on EDA 1: the share of bad rows is small, so dropping should not bias the analysis.
REQUIRED_COLS = [
    "tradeTime", "price", "totalPrice", "square", "district", "Lng", "Lat",
    "livingRoom", "drawingRoom", "bathRoom", "buildingType", "constructionTime",
    "elevator", "fiveYearsProperty", "subway", "communityAverage",
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _numeric(s: pd.Series) -> pd.Series:
    """Convert to numbers; unparseable text becomes NaN."""
    return pd.to_numeric(s, errors="coerce")


def _is_fractional(num: pd.Series) -> pd.Series:
    return num.notna() & (num % 1 != 0)


# --------------------------------------------------------------------------- #
# Conversion
# --------------------------------------------------------------------------- #
def clean_dataframe(df: pd.DataFrame, drop_bad_rows: bool = True):
    """Convert each declared group to its intended type.

    Returns (cleaned_df, log). `log` has one row per column showing how many values
    were already missing and how many were invalid and set to NaN.
    """
    df = df.copy()
    n_start = len(df)
    log = []

    def record(col, kind, raw, cleaned):
        log.append({
            "column": col,
            "intended type": kind,
            "n_missing_before": int(raw.isna().sum()),
            "n_invalid_set_to_nan": int((raw.notna() & cleaned.isna()).sum()),
        })

    # 1. Drop unwanted columns
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

    # 2. Strings (IDs as text; a float ID would print as 1.01089e+11)
    for c in STRING_COLS:
        if c in df.columns:
            s = df[c]
            if pd.api.types.is_float_dtype(s):
                s = s.astype("Int64")
            df[c] = s.astype("string")

    # 3. Dates
    for c in DATE_COLS:
        raw = df[c]
        df[c] = pd.to_datetime(raw, errors="coerce")
        record(c, "datetime", raw, df[c])

    # 4. Counts: whole numbers, not negative
    for c in COUNT_COLS:
        raw = df[c]
        num = _numeric(raw)
        num = num.mask(_is_fractional(num) | (num < 0))
        df[c] = num.astype("Int64")
        record(c, "count (Int64)", raw, df[c])

    # 5. Years: whole numbers inside the plausible range
    for c, (lo, hi) in YEAR_COLS.items():
        raw = df[c]
        num = _numeric(raw)
        num = num.mask(_is_fractional(num) | (num < lo) | (num > hi))
        df[c] = num.astype("Int64")
        record(c, "year (Int64)", raw, df[c])

    # 6. Codes: only the documented values are valid (this also removes fractions)
    for c, valid in CODE_COLS.items():
        raw = df[c]
        num = _numeric(raw)
        num = num.mask(num.notna() & ~num.isin(valid))
        df[c] = num.astype("Int64")
        record(c, "code (Int64)", raw, df[c])

    # 7. Continuous values: numbers inside the plausible range
    for c, (lo, hi) in FLOAT_COLS.items():
        raw = df[c]
        num = _numeric(raw)
        if lo is not None:
            num = num.mask(num < lo)
        if hi is not None:
            num = num.mask(num > hi)
        df[c] = num.astype("float64")
        record(c, "float64", raw, df[c])

    log = pd.DataFrame(log).set_index("column")
    log["% affected"] = (
        (log["n_missing_before"] + log["n_invalid_set_to_nan"]) / n_start * 100
    ).round(3)

    # 8. Duplicates and rows with a problem in a required column
    dup = df["id"].duplicated(keep="first")
    bad = df[REQUIRED_COLS].isna().any(axis=1)
    print(f"Rows at start:                {n_start:,}")
    print(f"Duplicate IDs:                {dup.sum():,}")
    print(f"Rows with a required value NaN: {bad.sum():,} ({bad.mean() * 100:.2f}%)")

    if drop_bad_rows:
        df = df[~dup & ~bad].reset_index(drop=True)
        print(f"Rows kept:                    {len(df):,} ({len(df) / n_start * 100:.2f}%)")

    return df, log


# --------------------------------------------------------------------------- #
# Describe (after conversion)
# --------------------------------------------------------------------------- #
def describe_clean(df: pd.DataFrame):
    """Return (numeric summary, code value counts).

    Codes are excluded from describe(): the mean of a building-type label is meaningless.
    Their value counts show whether only the documented codes remain.
    """
    numeric_cols = [c for c in [*COUNT_COLS, *YEAR_COLS, *FLOAT_COLS] if c in df.columns]
    numeric_summary = df[numeric_cols].astype("float64").describe().T

    code_counts = {c: df[c].value_counts(dropna=False).sort_index() for c in CODE_COLS if c in df.columns}
    return numeric_summary, code_counts


# --------------------------------------------------------------------------- #
def main() -> None:
    raw = pd.read_excel(RAW_PATH)
    print(f"Loaded {len(raw):,} rows, {raw.shape[1]} columns from {RAW_PATH}\n")

    clean, log = clean_dataframe(raw)

    print("\nCleaning log")
    print(log.to_string())

    numeric_summary, code_counts = describe_clean(clean)
    print("\nNumeric summary")
    print(numeric_summary.round(2).to_string())
    print("\nCode columns (value counts)")
    for name, counts in code_counts.items():
        print(f"\n{name}\n{counts.to_string()}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(clean):,} rows, {clean.shape[1]} columns to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()