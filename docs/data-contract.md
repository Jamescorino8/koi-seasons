# Data Contract

Defines the daily data shared between the data pipeline (`python/data/`)
and the visuals (`python/render/`, `web/`).

## File

- **Path:** `data/processed/pond_year.json`
- **Format** JSON array, one object per day
- **Produced by:** `python/data/build_year.py`
- **Used by:** the NumPy renderer and the web page

## Fields

| Field       | Type   |     Range or Values      | Meaning                          |
|:------------|:-------|:------------------------:|:---------------------------------| 
| `day`       | int    |          1-365           | Day of year                      |
| `date`      | string |         `MM-DD`          | Label for the slider             |
| `airTemp`   | float  |            ºF            | Typial daily air temp            |
| `waterTemp` | float  |            ºF            | Estimated pond temp              |
| `activity`  | float  |           0-1            | Swim speed and spread of the koi |
| `feeding`   | string | `none`,`light`,`regular` | Feeding level                    |
| `ice`       | float  |            ºF            | Ice cover on the surface         |
| `algae`     | float  |            ºF            | Green tint of the water          |

## Rules

- Exactly 365 entries, sorted by `day`, no gaps.
- No missing or null values.
- All 0-1 fields are clamped to that range.
- Visuals never compute these values themselves; they only read them.

## Example

```json
{
  "day": 15,
  "date": "01-15",
  "airTemp": 25.0,
  "waterTemp": 36.0,
  "activity": 0.1,
  "feeding": "none",
  "ice": 0.8,
  "algae": 0.0
}
```

Sample days for testing: `data/processed/sample_days.json`

## Changelog

- **v1** (Nov 2026): initial fields
