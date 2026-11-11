from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "clean_data.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "pond_year.json"

WATER_SMOOTHING_ALPHA = 0.1  # daily fraction the pond moves toward air temp; 0.1 ≈ 10-day lag TODO plot against air temp and check for smoothed curve
WATER_TEMP_FLOOR = 35.0  # lowest water temp (°F) where koi overwinter; ice insulates water below the surface


def main() -> None:
    """Run the build year pipeline from clean data to the processed pond year JSON file."""
    df = load_clean_data()
    df = build_typical_year(df)


def load_clean_data() -> pd.DataFrame:
    """Load the processed NOAA CSV with the DATE column parsed as dates."""
    df = pd.read_csv(INPUT_PATH, parse_dates=["DATE"])
    assert isinstance(df, pd.DataFrame), "The object is not a pandas DataFrame"
    return df


def build_typical_year(df: pd.DataFrame) -> pd.DataFrame:
    """Average air temperature for each calendar day across all years.

    Returns one row per day (365 rows) with month, day of month,
    day of year, an MM-DD date label, and the average air temp.
    """
    month_key = df["DATE"].dt.month.rename("month")
    day_key = df["DATE"].dt.day.rename("day_of_month")
    typical_year = df.groupby([month_key, day_key])["TAVG"].mean().rename("air_temp")

    typical_year = typical_year.reset_index()
    typical_year["day"] = typical_year.index + 1

    month_str = typical_year["month"].astype(str).str.zfill(2)
    day_str = typical_year["day_of_month"].astype(str).str.zfill(2)
    typical_year["date"] = month_str + "-" + day_str
    return typical_year


# def estimate_water_temp(df: pd.DataFrame) -> pd.DataFrame:

# def add_activity():
#
# def add_feeding():
#
# def add_ice():
#
# def add_algae():
#
# def to_contract(df: pd.DataFrame) -> pd.DataFrame:
#
# def validate(df: pd.DataFrame) -> None:
#
# def save_json(df: pd.DataFrame) -> None:

if __name__ == "__main__":
    main()
