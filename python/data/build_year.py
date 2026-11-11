"""Build the typical pond year from clean daily data and export it as JSON."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN_DATA_PATH = ROOT / "data" / "processed" / "clean_data.csv"
WATER_TEMP_PLOT_PATH = ROOT / "docs" / "plot_air_vs_water.png"
POND_YEAR_PATH = ROOT / "data" / "processed" / "pond_year.json"

WATER_SMOOTHING_ALPHA = 0.1  # daily fraction the pond moves toward air temp; 0.1 ≈ 10-day lag
WATER_TEMP_FLOOR = 35.0  # Lowest water temp (°F) where koi overwinter; ice insulates the water below.


def main() -> None:
    """Run the pipeline from clean daily data to the pond year JSON."""
    df = load_clean_data()
    df = build_typical_year(df)
    df = estimate_water_temp(df)
    plot_air_vs_water_temp(df)


def load_clean_data() -> pd.DataFrame:
    """Load the processed NOAA CSV with the DATE column parsed as dates."""
    clean_data = pd.read_csv(CLEAN_DATA_PATH, parse_dates=["DATE"])
    assert isinstance(clean_data, pd.DataFrame), "The object is not a pandas DataFrame"
    return clean_data


def build_typical_year(clean_data: pd.DataFrame) -> pd.DataFrame:
    """Average air temperature for each calendar day across all years.

    Returns one row per day (365 rows) with month, day of month,
    day of year, an MM-DD date label, and the average air temp.
    """
    month_key = clean_data["DATE"].dt.month.rename("month")
    day_key = clean_data["DATE"].dt.day.rename("day_of_month")
    typical_year = clean_data.groupby([month_key, day_key])["TAVG"].mean().rename("air_temp")

    typical_year = typical_year.reset_index()
    typical_year["day"] = typical_year.index + 1

    month_str = typical_year["month"].astype(str).str.zfill(2)
    day_str = typical_year["day_of_month"].astype(str).str.zfill(2)
    typical_year["date"] = month_str + "-" + day_str
    return typical_year


def estimate_water_temp(typical_year: pd.DataFrame) -> pd.DataFrame:
    """Estimate daily pond water temperature from air temperature.

    Applies exponential smoothing so water lags behind air, runs the
    year twice so January has December’s history, and clamps values
    at the winter floor.
    """
    year = typical_year.copy()
    doubled_air = pd.concat([year["air_temp"], year["air_temp"]])
    smoothed = doubled_air.ewm(alpha=WATER_SMOOTHING_ALPHA, adjust=False).mean()
    smoothed = smoothed.clip(lower=WATER_TEMP_FLOOR)
    year["water_temp"] = smoothed.iloc[-len(year):].to_numpy()

    return year


def plot_air_vs_water_temp(year: pd.DataFrame) -> None:
    """Plot air vs. estimated water temperature and save it to docs."""
    plt.plot(year["day"], year["air_temp"], label="Air Temp", color="orange")
    plt.plot(year["day"], year["water_temp"], label="Water Temp", color="blue")
    plt.axhline(WATER_TEMP_FLOOR, color="red", linestyle="--", linewidth=1.5, label="Water Temp Floor")
    plt.title("Typical Year: Air vs. Estimated Pond Temperature.")
    plt.xlabel("Month")
    plt.ylabel("Temperature in °F")
    plt.xticks(ticks=[1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335],
               labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.legend()
    plt.savefig(fname=WATER_TEMP_PLOT_PATH)
    plt.close()


# def add_activity():
# def add_feeding():
# def add_ice():
# def add_algae():
# def to_contract(df: pd.DataFrame) -> pd.DataFrame:
# def validate(df: pd.DataFrame) -> None:
# def save_json(df: pd.DataFrame) -> None:

if __name__ == "__main__":
    main()
