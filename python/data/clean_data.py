"""Clean raw NOAA daily data for the Montgomery station and save as CSV."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "raw" / "noaa_daily.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "clean_data.csv"

STATION_ID = "USW00004789"


def main() -> None:
    """Run the cleaning pipeline from raw data to the processed CSV."""
    df = load_data()
    df = filter_rows(df)
    df = remove_duplicates(df)
    df = handle_missing(df)
    validate(df)
    save_data(df)


def load_data() -> pd.DataFrame:
    """Load the raw NOAA CSV with the DATE column parsed as dates."""
    df = pd.read_csv(INPUT_PATH, parse_dates=["DATE"])
    assert isinstance(df, pd.DataFrame), "The object is not a pandas DataFrame"
    return df


def filter_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the rows and columns needed for the typical year.

    Filters to the Montgomery station, drops unused columns, removes
    February 29 so every year has 365 days, and sorts by date.
    """
    df = df[df["STATION"] == STATION_ID]
    df = df.drop(columns=["NAME", "LATITUDE", "LONGITUDE", "ELEVATION"])
    df = df[~((df["DATE"].dt.month == 2) & (df["DATE"].dt.day == 29))]
    df = df.sort_values(by="DATE")
    return df.copy()


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop repeated dates, keeping the first row for each."""
    df = df.drop_duplicates(subset=["DATE"])
    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing temperatures and reset the index.

    TMAX and TMIN are interpolated first, so missing TAVG values can
    be filled with their midpoint.
    """
    df[["TMAX", "TMIN"]] = df[["TMAX", "TMIN"]].interpolate()
    df["TAVG"] = df["TAVG"].fillna((df["TMAX"] + df["TMIN"]) / 2)
    # reset index back to default
    df = df.reset_index(drop=True)
    return df


def validate(df: pd.DataFrame) -> None:
    """Check that the cleaned data follows the data contract.

    Rules: one station, no missing temperatures, no February 29,
    no duplicate dates, and TMAX never below TMIN.

    Raises AssertionError if any rule fails.
    """
    assert df["STATION"].nunique() == 1, "more than one station"
    assert df["TMIN"].notna().all(), "missing value in TMIN"
    assert df["TMAX"].notna().all(), "missing value in TMAX"
    assert df["TAVG"].notna().all(), "missing value in TAVG"
    is_leap_day = (df["DATE"].dt.month == 2) & (df["DATE"].dt.day == 29)
    assert not (is_leap_day.any()), "February 29th is present"
    assert not (df["DATE"].duplicated().any()), "duplicate dates present"
    assert (df["TMAX"] >= df["TMIN"]).all(), "TMAX has value below TMIN"


def save_data(df: pd.DataFrame) -> None:
    """Write the cleaned daily data to the processed CSV."""
    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
