
# 🌱 LivePublication Data Producer

![Tests](https://github.com/GusEllerm/livepublication-data-producer/actions/workflows/test.yml/badge.svg) [![Coverage Report](https://img.shields.io/badge/Coverage-View_Report-blue)](https://gusellerm.github.io/livepublication-data-producer/)

The **Data Producer** is Layer 1 of the LivePublication system. It automates satellite data discovery and retrieval using the Sentinel Hub API, preparing Copernicus Sentinel-2 imagery for scientific publications with fully traceable provenance.

---

## 📦 Key Features

- **Orbit-based provenance**: Metadata includes all product IDs and tile sources per request using `Mosaicking.ORBIT`
- **Modular profiles**: Define AOIs, date ranges, and selection strategies in `profiles.py`
- **Profile-based job IDs**: Each run generates a unique job ID from the profile, enabling reproducible, structured output
- **Structured outputs**: All intermediate and final files are saved into a job-specific folder inside `outputs/`
- **Smart tiling**: Automatically splits large requests into API-safe sub-tiles
- **Orbit selection**: Ranks and selects the best available orbit based on configurable strategy (e.g. least cloud)
- **Imagery stitching**: Merges `.npy` tiles into a full-scene array
- **Postprocessing**: Computes NDVI and renders true-color composites
- **GeoTIFF output**: Exports `.tif` images with full geospatial metadata
- **Archived result viewing**: View NDVI and true-color outputs from any previously archived run
- **Interactive visualisation tool with side-by-side NDVI / RGB view**
- **Full CLI workflow**: Reproducible data generation with Makefile commands
- **Unit tests**: Lightweight test suite for all core utilities

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
```

Then run:

```bash
make run                        # Process current profile (get_data.py)
make timeseries                 # Process profile over time (get_timeseries.py)
make view                       # View NDVI/true-color result interactively
make view archive=<foldername> # View outputs from a previous archived run
make archive                    # Archive latest outputs with a timestamp
make archive from-dir=<path> label=<name>  # Archive outputs from a specific directory with custom label
make clean                      # Remove all generated outputs
make test                       # Run unit tests
```

### 🗃️ Archive Example

```bash
make archive from-dir=tiles_canterbury label=veg_index_april5
```

This will create a new folder under `archive/veg_index_april5/` containing:

- `ndvi.tif`
- `ndvi.png`
- `true_color.tif`
- `true_color.png`

These outputs can then be viewed using:

```bash
make view archive=veg_index_april5
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
├── utils/
│   ├── __init__.py
│   ├── tile_utils.py       # Tiling and tile downloading
│   ├── image_utils.py      # NDVI + true-color stitching and processing
│   ├── metadata_utils.py   # Orbit metadata and selection
│   ├── file_io.py          # GeoTIFF saving and output cleaning
│   ├── job_utils.py        # Job ID creation and path helpers
│   ├── plotting.py         # Plot rendering helpers
│   └── time_interval_utils.py  # Time interval generation and formatting
├── visualise_data.py       # Side-by-side NDVI / RGB viewer with metadata overlay and interaction
├── visualise_timeseries.py # Scrollable time series viewer
├── archive_data.py         # Archive outputs into a named or timestamped folder
├── clean_outputs.py        # Output folder cleanup
├── tests/
│   └── file_io.py          # Unit tests for I/O utilities
```

---

## 📤 Output Files

For each run, outputs are saved to:

```
outputs/<job_id>/
├── raw_tiles/       # Downloaded tile `.npy` files
├── stitched/        # Stitched `.npy` bands
├── imagery/         # NDVI / RGB `.tif` and `.png`
└── metadata/        # Orbit metadata JSON
```

Archived results are saved in `archive/<label or timestamp>/`.

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
