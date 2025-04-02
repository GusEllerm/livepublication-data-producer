# 🌱 LivePublication Data Producer

![Tests](https://github.com/GusEllerm/livepublication-data-producer/actions/workflows/test.yml/badge.svg) [![Coverage Report](https://img.shields.io/badge/Coverage-View_Report-blue)](https://gusellerm.github.io/livepublication-data-producer/)

This repository contains the **Data Producer** (Layer 1) for a LivePublication instance. It automates satellite data acquisition and preparation from Copernicus Sentinel-2 imagery using the Sentinel Hub API.

The output is designed to support dynamic scientific publications that integrate computation and visualization, particularly for monitoring vegetative health in regions like New Zealand.

---

## 📦 Features

- **Profile-based configuration**: Easily swap out AOIs, date ranges, and resolution presets via `profiles.py`
- **Time series support**: Generate and analyze data across monthly or custom intervals
- **Tile-safe downloader**: Automatically generates tiles that stay within SentinelHub request limits
- **In-house stitching**: Merges downloaded `.npy` tiles into a full image array
- **Postprocessing**: Computes NDVI and True Color rasters from raw bands
- **GeoTIFF export**: Outputs `.tif` files with proper georeferencing for use in GIS
- **Interactive viewers**: Toggle NDVI vs RGB for a single run or scroll through time series
- **Graceful error handling**: Skips failed tiles and validates downloaded data
- **Testing suite**: `pytest`-powered unit tests with temp data support
- **Graceful cleanup**: Remove all generated tiles, images, and intermediate outputs with `make clean`

---

## 🚀 Quick Start

Install dependencies (use a virtual environment):

```bash
pip install -r requirements.txt
```

Then run:

```bash
make run             # Executes get_data.py using current profile
make view            # Launches the NDVI/true-color viewer for static output
make timeseries      # Runs get_timeseries.py using a time-series profile
make view_timeseries # Interactive viewer to scroll through time-based outputs
make clean           # Removes all tiles_*/ folders and generated .npy/.tif/.png outputs
make test            # Runs unit tests in Scripts/tests
```

---

💡 **Acquisition Strategies**

Acquisition strategies define how to select the best tiles from a series of satellite observations based on certain criteria, such as cloud cover or acquisition date. The available strategies are:

1. **leastCC (Least Cloud Cover):**
   - Selects the tile with the least amount of cloud cover within a specified time interval.
2. **mostRecent (Most Recent):**
   - Selects the most recent observation for each time interval.
3. **same_day_all_tiles (Same Day All Tiles):**
   - Ensures that all tiles for the region are acquired on the same day, while minimizing cloud cover.
4. **best_per_tile (Best Tile Per Region):**
   - Selects the best tile for each region, considering cloud cover and other quality factors.


## 🗺 Directory Structure

```
Scripts/
├── get_data.py             # Main entry point for single-run data generation
├── get_timeseries.py       # Loop-based runner for time series data extraction
├── visualise_data.py       # Interactive toggle viewer for single NDVI/true color set
├── visualise_timeseries.py # Interactive scrollable time series comparison tool
├── profiles.py             # Preset configurations (AOI, dates, resolution, etc.)
├── utils.py                # Core processing functions (tiling, stitching, NDVI, saving)
├── clean_outputs.py        # Optional cleaner script for output dir
├── tests/
│   └── utils_test.py       # Unit tests for NDVI, stitching, etc.
```

---

## ✅ Outputs

- `stitched_raw_bands.npy` — raw stacked bands
- `ndvi.npy` / `ndvi.tif` / `ndvi.png` — vegetation index
- `true_color.tif` / `.png` — natural color visual
- For time series: subdirectories for each interval with the above outputs
- All outputs saved with proper CRS and bounding box metadata

---

## 🧪 Testing

Run:

```bash
make test
```

Tests include:

- Band math (`NDVI`, `True Color`)
- Tiling logic
- Stitching and alignment
- GeoTIFF saving + reloading

---

## 📖 License

[MIT License](LICENSE)
