
# 🌱 LivePublication Data Producer

![Tests](https://github.com/GusEllerm/livepublication-data-producer/actions/workflows/test.yml/badge.svg) [![Coverage Report](https://img.shields.io/badge/Coverage-View_Report-blue)](https://gusellerm.github.io/livepublication-data-producer/)

The **Data Producer** is Layer 1 of the LivePublication system. It automates satellite data discovery and retrieval using the Sentinel Hub API, preparing Copernicus Sentinel-2 imagery for scientific publications with fully traceable provenance.

---

## 📦 Key Features

- **Orbit-based provenance**: Metadata includes all product IDs and tile sources per request using `Mosaicking.ORBIT`
- **Modular profiles**: Define AOIs, date ranges, and selection strategies in `profiles.py`
- **Smart tiling**: Automatically splits large requests into API-safe sub-tiles
- **Orbit selection**: Ranks and selects the best available orbit based on configurable strategy (e.g. least cloud)
- **Imagery stitching**: Merges `.npy` tiles into a full-scene array
- **Postprocessing**: Computes NDVI and renders true-color composites
- **GeoTIFF output**: Exports `.tif` images with full geospatial metadata
- **Full CLI workflow**: Reproducible data generation with Makefile commands
- **Unit tests**: Lightweight test suite for all core utilities

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
```

Then run:

```bash
make run             # Process current profile (get_data.py)
make timeseries      # Process profile over time (get_timeseries.py)
make view            # View NDVI/true-color result interactively
make view_timeseries # Scroll through time series frames
make clean           # Remove all generated outputs
make test            # Run unit tests
```

> ⚠️ **Note:** The `get_timeseries.py` workflow has **not yet been updated** to use the new ORBIT-based system. It currently uses the legacy acquisition method and may not generate detailed provenance metadata.

---

## 🧠 Orbit Selection Strategies

Orbit selection determines which Sentinel-2 orbit is used to fulfill a request:

| Strategy          | Description                                                      |
| ----------------- | ---------------------------------------------------------------- |
| `least_cloud`   | Selects the orbit with the lowest average cloud coverage         |
| `most_recent`   | Chooses the most recently available orbit                        |
| `same_day_all`  | Uses orbits where all required tiles share the same sensing date |
| `best_per_tile` | Selects the best tile for each region individually (WIP)         |

Unimplemented strategies will fail gracefully.

---

## 📂 Directory Overview

```
Scripts/
├── get_data.py             # Run once for current profile (single orbit)
├── get_timeseries.py       # Run over time intervals (legacy logic)
├── profiles.py             # AOIs and config definitions
├── utils.py                # Tiling, stitching, download, metadata handling
├── visualise_data.py       # NDVI / RGB toggle viewer
├── visualise_timeseries.py # Scrollable time series viewer
├── clean_outputs.py        # Output folder cleanup
├── tests/
│   └── utils_test.py       # Core tests
```

---

## 📤 Output Files

For each run:

- `*_orbit_metadata.json` — All orbits that intersect the request bbox
- `*_selected_orbit.json` — The chosen orbit and its tile/product metadata
- `.npy` tiles — Raw band arrays per tile
- `stitched_raw_bands.npy` — Combined raw imagery
- `ndvi.tif` / `ndvi.png` — NDVI output
- `true_color.tif` / `.png` — Natural color imagery

All GeoTIFFs include proper CRS and bounding box metadata.

---

## 🧪 Testing

```bash
make test
```

Covers:

- NDVI & true-color raster generation
- Tiling & stitching accuracy
- Metadata parsing
- GeoTIFF save/load consistency

---

## 📖 License

MIT — use, share, and cite freely.
_Developed as part of the LivePublication Framework._
