"""Feature engineering for the Beijing housing prices dataset (BT2102 Assignment 3).

Reads  : data/raw/BeijingHousingPrices.xlsx
Writes : data/raw/processed/BeijingHousingPrices_featured.csv

Run from anywhere:  python src/data/featureengineering.py
Requires: pandas, numpy, openpyxl
"""

from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Paths (this file lives in src/data/, so the project root is two levels up)
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "BeijingHousingPrices.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "BeijingHousingPrices_featured.csv"

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DISTRICT_MAP = {
    1: "Dongcheng",
    2: "Fengtai",
    3: "Tongzhou",
    4: "Daxing",
    5: "Fangshan",
    6: "Changping",
    7: "Chaoyang",
    8: "Haidian",
    9: "Shijingshan",
    10: "Xicheng",
    11: "Pinggu",
    12: "Mentougou",
    13: "Shunyi",
}

DISTRICT_ZONE_MAP = {
    "Dongcheng": "Core",
    "Xicheng": "Core",
    "Chaoyang": "Inner suburb",
    "Haidian": "Inner suburb",
    "Fengtai": "Inner suburb",
    "Shijingshan": "Inner suburb",
    "Tongzhou": "Outer",
    "Daxing": "Outer",
    "Fangshan": "Outer",
    "Changping": "Outer",
    "Pinggu": "Outer",
    "Mentougou": "Outer",
    "Shunyi": "Outer",
}

# Approximate location of Tiananmen Square, used as the city centre
CENTER_LAT, CENTER_LNG = 39.9087, 116.3975

# Columns that should be numeric but may contain stray text in the raw file
NUMERIC_COLS = [
    "DOM", "followers", "totalPrice", "price", "square",
    "livingRoom", "drawingRoom", "kitchen", "bathroom",
    "constructionTime", "renovationCondition", "elevator",
    "subway", "fiveYearsProperty", "district", "Lng", "Lat",
]


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_data(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load the raw Excel file and coerce numeric columns."""
    df = pd.read_excel(path)

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["tradeTime"] = pd.to_datetime(df["tradeTime"], errors="coerce")
    return df


# --------------------------------------------------------------------------- #
# Feature groups
# --------------------------------------------------------------------------- #
def add_floor_features(df: pd.DataFrame) -> pd.DataFrame:
    """story_type / story from `floor`, plus a high-rise flag."""
    df[["story_type", "story"]] = df["floor"].str.split(" ", n=1, expand=True)
    df["story"] = pd.to_numeric(df["story"], errors="coerce")
    df["is_high_rise"] = (df["story"] >= 20).astype("Int8")
    df.loc[df["story"].isna(), "is_high_rise"] = pd.NA
    return df


def add_district_features(df: pd.DataFrame) -> pd.DataFrame:
    """district_name and a coarser district_zone."""
    df["district_name"] = df["district"].map(DISTRICT_MAP)
    df["district_zone"] = df["district_name"].map(DISTRICT_ZONE_MAP)
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Year, month, quarter and a year-month period from `tradeTime`."""
    df["trade_year"] = df["tradeTime"].dt.year
    df["trade_month"] = df["tradeTime"].dt.month
    df["trade_quarter"] = df["tradeTime"].dt.quarter
    df["year_month"] = df["tradeTime"].dt.to_period("M").astype(str)
    return df


def add_age_features(df: pd.DataFrame) -> pd.DataFrame:
    """Building age at the time of sale, an age bucket and a new-build flag."""
    age = df["trade_year"] - df["constructionTime"]
    # Negative ages (sold before completion) or absurd ages are treated as invalid
    df["building_age"] = age.where((age >= 0) & (age <= 100))

    df["age_bucket"] = pd.cut(
        df["building_age"],
        bins=[-0.1, 5, 15, 30, np.inf],
        labels=["0-5", "6-15", "16-30", "30+"],
    )
    df["is_new_build"] = (df["building_age"] <= 5).astype("Int8")
    df.loc[df["building_age"].isna(), "is_new_build"] = pd.NA
    return df


def add_size_features(df: pd.DataFrame) -> pd.DataFrame:
    """Room counts, space per bedroom and a size category."""
    df["total_rooms"] = (
        df["livingRoom"] + df["drawingRoom"] + df["kitchen"] + df["bathRoom"]
    )
    # Avoid division by zero for studios (0 bedrooms)
    df["area_per_room"] = df["square"] / df["livingRoom"].replace(0, np.nan)

    df["size_category"] = pd.cut(
        df["square"],
        bins=[0, 50, 90, 140, np.inf],
        labels=["<50", "50-90", "90-140", "140+"],
    )
    return df


def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """Price checks, log transforms and price relative to the district."""
    # Sanity check: does `price` match totalPrice (10k yuan) / square?
    df["price_per_sqm_calc"] = df["totalPrice"] * 10_000 / df["square"]
    df["price_diff_pct"] = (df["price"] - df["price_per_sqm_calc"]) / df["price_per_sqm_calc"]

    df["log_total_price"] = np.log(df["totalPrice"].where(df["totalPrice"] > 0))
    df["log_price_per_sqm"] = np.log(df["price"].where(df["price"] > 0))

    # Median price per sqm for the same district and year, and the ratio to it.
    # NOTE: if you later train a model, compute these on the training split only
    # to avoid leaking information from the test set.
    df["district_median_price"] = df.groupby(["district_name", "trade_year"])["price"].transform("median")
    df["price_vs_district"] = df["price"] / df["district_median_price"]
    return df


def add_liquidity_features(df: pd.DataFrame) -> pd.DataFrame:
    """Interest per day on market and a fast-sale flag."""
    df["followers_per_day"] = df["followers"] / df["DOM"].replace(0, np.nan)

    median_dom = df["DOM"].median()
    df["is_fast_sale"] = (df["DOM"] <= median_dom).astype("Int8")
    df.loc[df["DOM"].isna(), "is_fast_sale"] = pd.NA
    return df


def add_amenity_features(df: pd.DataFrame) -> pd.DataFrame:
    """Simple count of premium features and a high-floor-with-elevator flag."""
    df["amenity_score"] = (
        df["subway"].fillna(0)
        + df["elevator"].fillna(0)
        + (df["renovationCondition"] == 4).astype(int)
    )
    df["high_floor_with_elevator"] = (
        (df["story_type"] == "High") & (df["elevator"] == 1)
    ).astype("Int8")
    return df


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in km (vectorised)."""
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2
    )
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def add_location_features(df: pd.DataFrame) -> pd.DataFrame:
    """Distance from the city centre in km."""
    df["distance_to_center_km"] = haversine_km(
        df["Lat"], df["Lng"], CENTER_LAT, CENTER_LNG
    )
    return df


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature groups. Order matters: later steps use earlier columns."""
    df = df.copy()
    df = add_floor_features(df)
    df = add_district_features(df)
    df = add_time_features(df)
    df = add_age_features(df)          # needs trade_year
    df = add_size_features(df)
    df = add_price_features(df)        # needs district_name, trade_year
    df = add_liquidity_features(df)
    df = add_amenity_features(df)      # needs story_type
    df = add_location_features(df)
    return df


def main() -> None:
    df = load_data()
    print(f"Loaded {len(df):,} rows, {df.shape[1]} columns from {RAW_PATH}")

    df = engineer_features(df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(df):,} rows, {df.shape[1]} columns to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()