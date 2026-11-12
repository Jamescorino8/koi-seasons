"""Clean raw NOAA daily data for the Montgomery station and save as CSV."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = ROOT / "data" / "raw" / "noaa_daily.csv"
CLEAN_DATA_PATH = ROOT / "data" / "processed" / "clean_data.csv"

STATION_ID = "USW00004789"

TEMP_COLUMNS = ["TMIN", "TMAX", "TAVG"]


def main() -> None:
    """Run the cleaning pipeline from raw data to the processed CSV."""
    df = load_raw_data()
    df = filter_rows(df)
    df = remove_duplicates(df)
    df = handle_missing(df)
    validate(df)
    save_clean_data(df)


def load_raw_data() -> pd.DataFrame:
    """Load the raw NOAA CSV with the DATE column parsed as dates."""
    df = pd.read_csv(RAW_DATA_PATH, parse_dates=["DATE"])
    assert isinstance(df, pd.DataFrame), "The object is not a pandas DataFrame"
    return df


def filter_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the rows and columns needed for the typical year.

    Filters to the Montgomery station, drops unused columns, removes
    February 29 so every year has 365 days, and sorts by date.
    """
    daily = df.copy()
    daily = daily[daily["STATION"] == STATION_ID]
    daily = daily.drop(columns=["NAME", "LATITUDE", "LONGITUDE", "ELEVATION"])
    daily = daily[~((daily["DATE"].dt.month == 2) & (daily["DATE"].dt.day == 29))]
    daily = daily.sort_values(by="DATE")
    return daily


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop repeated dates, keeping the first row for each."""
    return df.drop_duplicates(subset=["DATE"])


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing temperatures and reset the index.

    TMAX and TMIN are interpolated first, so missing TAVG values can
    be filled with their midpoint.
    """
    daily = df.copy()
    daily[["TMAX", "TMIN"]] = daily[["TMAX", "TMIN"]].interpolate()
    daily["TAVG"] = daily["TAVG"].fillna((daily["TMAX"] + daily["TMIN"]) / 2)
    daily = daily.reset_index(drop=True)
    return daily


def validate(df: pd.DataFrame) -> None:
    """Check that the cleaned data follows the data contract.

    Rules: one station, no missing temperatures, no February 29,
    no duplicate dates, and TMAX never below TMIN.

    Raises AssertionError if any rule fails.
    """
    assert df["STATION"].nunique() == 1, "more than one station"
    for col in TEMP_COLUMNS:
        assert df[col].notna().all(), f"missing value in {col}"
    is_leap_day = (df["DATE"].dt.month == 2) & (df["DATE"].dt.day == 29)
    assert not is_leap_day.any(), "February 29th is present"
    assert not df["DATE"].duplicated().any(), "duplicate dates present"
    assert (df["TMAX"] >= df["TMIN"]).all(), "TMAX has value below TMIN"


def save_clean_data(df: pd.DataFrame) -> None:
    """Write the cleaned daily data to the processed CSV."""
    df.to_csv(CLEAN_DATA_PATH, index=False)


if __name__ == "__main__":
    main()
