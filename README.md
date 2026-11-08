# Koi Seasons

A procedurally rendered koi pond that changes through the year, driven by real weather data. Drag
a slider through the seasons: koi slow down and sink deep in winter, ice forms on the surface, and summer brings faster
swimming and an algae tint.

**Status:** In progress, Phase 0 (project setup)

## Planned Stack

- **Data:** Python, pandas
- **Prototyping visuals:** NumPy, Matplotlib, Pillow
- **Browser rendering:** GLSL shaders, three.js
- **Interface and charts:** JavaScript, D3.js, HTML/CSS

## Project Structure

```
data/        raw NOAA data and processed daily JSON
python/      data pipeline and NumPy render prototypes
web/         browser version (shaders, slider, charts)
docs/        data contract, images, GIFs
```

## Data Contract

Daily values shared between the data pipeline and the visuals are defined
in [docs/data-contract.md](docs/data-contract.md).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## License

MIT
