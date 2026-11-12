"""Build the typical pond year from clean daily data and export it as JSON."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN_DATA_PATH = ROOT / "data" / "processed" / "clean_data.csv"
WATER_TEMP_PLOT_PATH = ROOT / "docs" / "plot_air_vs_water.png"
POND_YEAR_PATH = ROOT / "data" / "processed" / "pond_year.json"

WATER_SMOOTHING_ALPHA = 0.1  # daily fraction the pond moves toward air temp; 0.1 ≈ 10-day lag
WATER_TEMP_FLOOR = 35.0  # lowest water temp (°F) where koi overwinter; ice insulates the water below.
# Placeholder behavior constants
ACTIVITY_DORMANT_TEMP = 45  # water temp where activity is 0
ACTIVITY_FULL_TEMP = 72  # water temp where activity reaches 1
FEEDING_STOP_TEMP = 50  # below this water temp, koi aren’t fed
FEEDING_REGULAR_TEMP = 60  # light feeding below this, regular feeding at or above
FREEZING_TEMP = 32  # air temp at or below which a day counts as freezing
ICE_WINDOW_DAYS = 7  # number of recent days used to estimate ice cover
ALGAE_START_TEMP = 60  # water temp where algae starts to appear
ALGAE_PEAK_TEMP = 78  # water temp where algae reaches full strength

CONTRACT_FIELDS = ["day", "date", "airTemp", "waterTemp", "activity", "feeding", "ice", "algae"]
ZERO_TO_ONE_FIELDS = ["activity", "ice", "algae"]


def main() -> None:
    """Run the pipeline from clean daily data to the pond year JSON."""
    df = load_clean_data()
    df = build_typical_year(df)
    df = estimate_water_temp(df)
    plot_air_vs_water_temp(df)
    df = add_activity(df)
    df = add_feeding(df)
    df = add_ice(df)
    df = add_algae(df)
    df = to_contract(df)
    validate(df)
    save_json(df)


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


def estimate_water_temp(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate daily pond water temperature from air temperature.

    Applies exponential smoothing so water lags behind air, runs the
    year twice so January has December’s history, and clamps values
    at the winter floor.
    """
    year = df.copy()
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
    plt.title("Typical Year: Air vs. Estimated Pond Temperature")
    plt.xlabel("Month")
    plt.ylabel("Temperature in °F")
    plt.xticks(ticks=[1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335],
               labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.legend()
    plt.savefig(fname=WATER_TEMP_PLOT_PATH)
    plt.close()


def add_activity(df: pd.DataFrame) -> pd.DataFrame:
    """Add koi activity (0 to 1) from water temperature.

    Activity is 0 at or below the dormant temp, 1 at or above the
    full temp, and rises linearly in between.
    """
    year = df.copy()
    temp_range = ACTIVITY_FULL_TEMP - ACTIVITY_DORMANT_TEMP
    year["activity"] = ((year["water_temp"] - ACTIVITY_DORMANT_TEMP) / temp_range).clip(0, 1)
    return year


def add_feeding(df: pd.DataFrame) -> pd.DataFrame:
    """Add the feeding level (none, light, or regular) from water temperature.

    No feeding below the stop temp, light feeding up to the regular
    temp, and regular feeding at or above it.
    """
    year = df.copy()
    conditions = [
        year["water_temp"] < FEEDING_STOP_TEMP,
        year["water_temp"] < FEEDING_REGULAR_TEMP,
    ]
    outputs = [
        "none",
        "light",
    ]
    year["feeding"] = np.select(conditions, outputs, default="regular")
    return year


def add_ice(df: pd.DataFrame) -> pd.DataFrame:
    """Add ice cover (0 to 1) from recent air temperatures.

    Ice is the fraction of the last several days with air at or
    below freezing, so a full week of freezing days gives full cover.
    """
    year = df.copy()
    doubled_air = pd.concat([year["air_temp"], year["air_temp"]])
    freezing_days = doubled_air <= FREEZING_TEMP
    ice_cover = freezing_days.rolling(ICE_WINDOW_DAYS).mean()
    year["ice"] = ice_cover.iloc[-len(year):].to_numpy()
    return year


def add_algae(df: pd.DataFrame) -> pd.DataFrame:
    """Add algae level (0 to 1) from water temperature.

    Algae is 0 at or below the start temp, 1 at or above the peak
    temp, and rises linearly in between.
    """
    year = df.copy()
    temp_range = ALGAE_PEAK_TEMP - ALGAE_START_TEMP
    year["algae"] = ((year["water_temp"] - ALGAE_START_TEMP) / temp_range).clip(0, 1)
    return year


def to_contract(df: pd.DataFrame) -> pd.DataFrame:
    """Shape the year to match the data contract.

    Renames columns to camelCase, keeps only the contract fields in
    order, and rounds temperatures and 0-1 values.
    """
    year = df.copy()
    year = year.rename(columns={"air_temp": "airTemp", "water_temp": "waterTemp"})
    year = year[CONTRACT_FIELDS]
    year["waterTemp"] = year["waterTemp"].round(1)
    year["airTemp"] = year["airTemp"].round(1)
    for field in ZERO_TO_ONE_FIELDS:
        year[field] = year[field].round(2)

    return year


def validate(df: pd.DataFrame) -> None:
    """Check that the pond year follows the data contract.

    Rules: 365 rows, days 1 to 365 with no gaps or repeats, no missing
    values, 0 to 1 fields in range, and only allowed feeding values.

    Raises AssertionError if any rule fails.
    """
    assert len(df) == 365, "expected 365 rows"
    assert df.notna().all().all(), "missing data"
    assert df["day"].min() == 1, "expected day 1"
    assert df["day"].max() == 365, "expected day 365"
    assert not df["day"].duplicated().any(), "duplicate days present"
    for field in ZERO_TO_ONE_FIELDS:
        assert df[field].between(0, 1).all(), f"{field} expected value between 0 and 1"
    assert df["feeding"].isin(["none", "light", "regular"]).all(), "unexpected feeding value"
    assert df.columns.tolist() == CONTRACT_FIELDS, "columns do not match contract"


def save_json(df: pd.DataFrame) -> None:
    """Write the pond year to JSON as a list of daily records."""
    df.to_json(POND_YEAR_PATH, orient="records", indent=2)


if __name__ == "__main__":
    main()
