# BT2102 Assignment 3: Beijing Housing Prices

Group project for BT2102 Data Management and Visualisation (NUS).
We analyse Beijing housing transactions (Lianjia, 2002-2018) to answer:

> **What is the best investment strategy to maximise returns in Beijing properties?**

The deliverable is a 10-minute data storytelling presentation. This repo holds the data preparation
and exploratory analysis behind it.

## Project structure

```
Beijing-Housing-Prices/
├── data/
│   ├── raw/                 # original dataset (NOT committed, see Step 2)
│   └── processed/           # cleaned and featured CSVs (NOT committed)
├── src/
│   ├── cleaning.py          # raw Excel -> cleaned CSV
│   ├── featureengineering.py  # cleaned CSV -> featured CSV
│   └── data/
│       ├── EDA.ipynb
│       └── eda_2.ipynb
│       └── eda_3.ipynb
├── eda_3.ipynb
├── requirements.txt
└── README.md
```
## Setup

These steps assume Python 3.10 or newer and git are installed.

### 1. Clone the repo

```bash
git clone https://github.com/zhenhao14/Beijing-Housing-Prices.git
cd Beijing-Housing-Prices
```

If the path to your folder contains spaces, wrap it in quotes in every command.

### 2. Download the dataset

The dataset is not stored in this repo because of its size.

1. Log in to Canvas and open **Assignments → Assignment 3**.
2. Download `BeijingHousingPrices.xlsx` from the Assignment 3 folder.
3. Place it at:

```
data/raw/BeijingHousingPrices.xlsx
```

Create the `data/raw/` folders if they don't exist. **The file name must match exactly**, because
the script looks for this name. If your download is named differently (for example
`BeijingHousePrices.xlsx`), rename it.

### 3. Create and activate a virtual environment

From the project root:

```bash
python3 -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Your terminal prompt should now start with `(.venv)`. You need to activate the environment
again every time you open a new terminal window. Setup is only done once.

### 4. Install the dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the feature engineering script

```bash
python src/featureengineering.py
```

This reads `data/raw/BeijingHousingPrices.xlsx`, adds the engineered features, and writes:

```
data/processed/BeijingHousingPrices_featured.csv
```

The script prints the row and column counts when it finishes. Loading the Excel file can take
a minute.

### 5. Clean the data

python src/cleaning.py

This reads `data/raw/BeijingHousingPrices.xlsx` (loading takes a minute), fixes column types,
removes invalid values, drops duplicates and incomplete rows, and drops the `DOM` column
(nearly half its values are missing). It writes `data/processed/BeijingHousingPrices_cleaned.csv`
and prints a cleaning log.

### 6. Engineer features

python src/featureengineering.py

This reads the cleaned CSV, adds the features listed below, and writes
`data/processed/BeijingHousingPrices_featured.csv`.

## Data cleaning

| Step | Outcome |
|---|---|
| Rows in raw file | 318,851 |
| Rows after cleaning | 297,490 (93.3%) |
| `DOM` dropped | Nearly half of values missing |
| Invalid values | Text in numeric columns, fractional or undocumented codes set to missing, then incomplete rows dropped |

## Engineered features

| Feature | Description |
|---|---|
| `story_type`, `story` | Floor level (High / Middle / Low) and building height, split from `floor` |
| `district_name`, `district_zone` | District label and Core / Inner suburb / Outer grouping |
| `trade_year`, `trade_month`, `trade_quarter`, `year_month` | Date parts from `tradeTime` |
| `building_age`, `age_bucket`, `is_new_build` | Age at time of sale |
| `is_high_rise` | 20 or more floors |
| `total_rooms`, `area_per_room`, `size_category` | Layout and size |
| `price_per_sqm_calc`, `price_diff_pct` | Check that `price` matches `totalPrice` and `square` |
| `log_total_price`, `log_price_per_sqm` | Log transforms for modelling |
| `district_median_price`, `price_vs_district` | Price relative to the same district and year |
| `followers_per_day`, `is_fast_sale` | Liquidity measures |
| `amenity_score`, `high_floor_with_elevator` | Premium features |
| `distance_to_center_km` | Distance to Tiananmen Square |

## Troubleshooting

| Problem | Fix |
|---|---|
| `can't open file '/Users/.../NUS'` | The path has spaces. Wrap it in quotes, or run `python src/featureengineering.py` from the project root. |
| `FileNotFoundError ... BeijingHousingPrices.xlsx` | The dataset is missing or misnamed. Check Step 2. |
| `ModuleNotFoundError` | The virtual environment is not active, or Step 4 was skipped. |
| `KeyError: '<column>'` | A column name in the data differs from the script (names are case-sensitive). Print `df.columns.tolist()` and compare. |
| `git push` fails with HTTP 400 | Run `git config http.postBuffer 524288000` and retry. |
| FileNotFoundError ... _cleaned.csv| Run python src/cleaning.py before featureengineering.py.|

## Team workflow

- Run `git pull` before starting work and `git push` when you finish.
- Each person owns their own notebook, since `.ipynb` merge conflicts are hard to resolve.
- Do not commit the dataset or `.venv/` (both are in `.gitignore`).
- Don't edit `cleaning.py` or `featureengineering.py` without telling the team. Changing either changes every notebook's input. If you change `cleaning.py`, rerun both scripts in order.

## Submission

Zip the PowerPoint as `Team_XX_A3.zip` and have **each member** upload a copy to Canvas.
