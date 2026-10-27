from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[2]  # .../Assignment 3
INPUT_PATH = ROOT / "data" / "processed" / "BeijingHousingPrices_featured.csv"
OUTPUT_PATH = Path(__file__).resolve().parent / "risk_stability.csv"

DISTRICTS = ["Tongzhou", "Shunyi", "Xicheng"]
START_YEAR, END_YEAR = 2012, 2017
MIN_N = 30        # min trades for a quarter (or end year) median to count
MIN_CHANGES = 8   # min usable quarter-on-quarter changes for a cell to be kept


# --------------------------------------------------------------------------- #
# Load and filter (data rules from the notebook)
# --------------------------------------------------------------------------- #
df = pd.read_csv(INPUT_PATH)

print("District names in file:", sorted(df["district_name"].dropna().unique()))
missing = [d for d in DISTRICTS if d not in set(df["district_name"])]
assert not missing, f"These districts are not spelled the same way in the file: {missing}"

df = df[df["trade_year"].between(START_YEAR, END_YEAR)]
df = df[df["ladderRatio"] <= 1]                      # ladder ratio > 1 = errors
df = df[df["district_name"].isin(DISTRICTS)].copy()

df["period"] = df["trade_year"].astype(str) + "Q" + df["trade_quarter"].astype(str)
ALL_PERIODS = sorted(df["period"].unique())          # lets gaps show up as NaN


# --------------------------------------------------------------------------- #
# Buckets: one column per characteristic
# --------------------------------------------------------------------------- #
df["Overall"] = "All trades"

# rank(method="first") avoids qcut failing on tied values
df["Ladder ratio"] = pd.qcut(
    df["ladderRatio"].rank(method="first"), 3, labels=["Low", "Mid", "High"]
)
df["Subway"] = df["subway"].map({1: "Near", 0: "Not near"})
df["Elevator"] = df["elevator"].map({1: "With", 0: "Without"})

# Terciles WITHIN each district, otherwise distance just re-labels the district
df["Distance to centre"] = (
    df.groupby("district_name")["distance_to_center_km"]
    .transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=["Closer", "Middle", "Further"]))
    .astype(str)
)

CHARACTERISTICS = ["Overall", "Ladder ratio", "Subway", "Elevator", "Distance to centre"]


# --------------------------------------------------------------------------- #
# Metrics for one cell (district x characteristic bucket)
# --------------------------------------------------------------------------- #
def cell_metrics(g: pd.DataFrame):
    # Median price per quarter, keeping only quarters with enough trades
    q = g.groupby("period")["price"].agg(["median", "size"])
    q = q[q["size"] >= MIN_N]["median"].reindex(ALL_PERIODS)

    # Quarter-on-quarter change; a skipped quarter gives NaN, not a 2-quarter jump
    change = (q / q.shift(1) - 1).dropna()
    if len(change) < MIN_CHANGES:
        return None

    # CAGR between yearly medians, only if both end years have enough trades
    yearly = g.groupby("trade_year")["price"].agg(["median", "size"])
    cagr = np.nan
    if (
        START_YEAR in yearly.index and END_YEAR in yearly.index
        and yearly.loc[START_YEAR, "size"] >= MIN_N
        and yearly.loc[END_YEAR, "size"] >= MIN_N
    ):
        ratio = yearly.loc[END_YEAR, "median"] / yearly.loc[START_YEAR, "median"]
        cagr = (ratio ** (1 / (END_YEAR - START_YEAR)) - 1) * 100

    return {
        "volatility_pp": change.std() * 100,
        "pct_quarters_down": (change < 0).mean() * 100,
        "cagr_pct": cagr,
        "n_trades": len(g),
        "n_changes": len(change),
    }


# --------------------------------------------------------------------------- #
# Build the tidy table
# --------------------------------------------------------------------------- #
rows, dropped = [], []
for char in CHARACTERISTICS:
    for (dist, bucket), g in df.groupby(["district_name", char], observed=True):
        m = cell_metrics(g)
        if m is None:
            dropped.append((dist, char, bucket, len(g)))
            continue
        rows.append({"district": dist, "characteristic": char, "bucket": bucket, **m})

out = pd.DataFrame(rows)

# Benchmark = average volatility of the three districts' overall trades
benchmark = out.loc[out["characteristic"] == "Overall", "volatility_pp"].mean()
out["vol_vs_avg"] = out["volatility_pp"] - benchmark

out = out.round(2).sort_values(["characteristic", "bucket", "district"])
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUTPUT_PATH, index=False)


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #
print(f"\nBenchmark (avg of 3 districts' overall volatility): {benchmark:.2f} pp")
print(f"Cells kept: {len(out)} | cells dropped (too few usable quarters): {len(dropped)}")
for d in dropped:
    print("  dropped:", d)
print(f"\nSaved to {OUTPUT_PATH}\n")
print(out.to_string(index=False))