# 🌱 LivePublication Data Producer

This repository contains the **Data Producer** (Layer 1) for a LivePublication instance. It automates satellite data acquisition and preparation from Copernicus Sentinel-2 imagery using the Sentinel Hub API.

The output is designed to support dynamic scientific publications that integrate computation and visualization, particularly for monitoring vegetative health in regions like New Zealand.

---

## 📦 Features

- **Profile-based configuration**: Easily swap out AOIs, date ranges, and resolution presets via `profiles.py`
- **Tile-safe downloader**: Automatically generates tiles that stay within SentinelHub request limits
- **In-house stitching**: Merges downloaded `.npy` tiles into a full image array
- **Postprocessing**: Computes NDVI and True Color rasters from raw bands
- **GeoTIFF export**: Outputs `.tif` files with proper georeferencing for use in GIS
- **Interactive viewer**: Toggle between NDVI and RGB in a Python viewer via `test_geo.py`
- **Graceful error handling**: Skips failed tiles and validates downloaded data
- **Testing suite**: `pytest`-powered unit tests with temp data support

---

## 🚀 Quick Start

Install dependencies (use a virtual environment):

```bash
pip install -r requirements.txt
```

Then run:

```bash
make run      # Executes get_data.py using current profile
make view     # Launches the interactive NDVI/true-color viewer
make clean    # Cleans up all output tiles and figures
make test     # Runs unit tests in Scripts/tests
```

---

## 🗺 Directory Structure

```
Scripts/
├── get_data.py           # Main entry point for the data pipeline
├── test_geo.py           # Interactive toggle viewer
├── profiles.py           # Preset configurations (AOI, dates, etc.)
├── utils.py              # Core processing functions (tiling, stitching, NDVI, saving)
├── clean_outputs.py      # Optional cleaner script for output dir
├── tests/
│   └── utils_test.py     # Unit tests for NDVI, stitching, etc.
```

---

## ✅ Outputs

- `stitched_raw_bands.npy` — raw stacked bands
- `ndvi.npy` / `ndvi.tif` / `ndvi.png` — vegetation index
- `true_color.tif` / `.png` — natural color visual
- All outputs saved with proper CRS and bounding box metadata

---

## 🧪 Testing

Run with:

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
