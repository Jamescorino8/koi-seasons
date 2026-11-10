import pandas as pd
import numpy as np

# create data frame from csv
df = pd.DataFrame(pd.read_csv("../../data/raw/noaa_daily.csv", parse_dates=["DATE"]))
# filter to only Montgomery Station
df = df[df["STATION"] == "USW00004789"]

# Interpolate missing TMAX and TMIN values
df[["TMAX", "TMIN"]] = df[["TMAX", "TMIN"]].interpolate()

# Fill in TAVG NaN values with neighboring TMAX and TMIN
df["TAVG"] = df["TAVG"].fillna((df["TMAX"] + df["TMIN"]) / 2)
#
# # filter out February 29th
df = df[~((df["DATE"].dt.month == 2) & (df["DATE"].dt.day == 29))]

# reset index and drop filtered values
df = df.reset_index(drop=True)

# investigate
df.info()
print(df.describe())
print(df[["DATE", "TAVG", "TMAX", "TMIN"]].head())
print(df[["DATE", "TAVG", "TMAX", "TMIN"]].tail())

# calc single average across each month/day pair and place in derived column TAVG_calc
typical = df.groupby([df["DATE"].dt.month, df["DATE"].dt.day])["TAVG"].mean()

# investigate
print(len(typical))
print(typical.head())
print(typical.tail())

# export to .json
typical.to_json("../../data/processed/typical_year.json")
