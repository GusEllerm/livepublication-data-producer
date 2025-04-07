
# 🌱 LivePublication Data Producer

![Tests](https://github.com/GusEllerm/livepublication-data-producer/actions/workflows/test.yml/badge.svg) [![Coverage Report](https://img.shields.io/badge/Coverage-View_Report-blue)](https://gusellerm.github.io/livepublication-data-producer/)

The **Data Producer** is Layer 1 of the LivePublication system. It automates satellite data discovery and retrieval using the Sentinel Hub API, preparing Copernicus Sentinel-2 imagery for scientific publications with fully traceable provenance.

---

## 📡 Data Source and Bands

This tool is specifically configured to use **Sentinel-2 L2A** data from the **Copernicus Sentinel Hub**.

The following bands are requested per tile:

- `B02` (Blue)
- `B03` (Green)
- `B04` (Red)
- `B08` (NIR)
- `B11`, `B12` (SWIR)

These bands are used to compute NDVI and to render true-color composites. All requests use `Mosaicking.ORBIT` to ensure orbit-based provenance.

---

## 📦 Key Features

- **Orbit-based provenance**: Metadata includes all product IDs and tile sources per request using `Mosaicking.ORBIT`
- **Profile-based job IDs**: Each run generates a unique job ID from the profile, enabling reproducible, structured output
- **Smart tiling**: Automatically splits large requests into API-safe sub-tiles
- **Orbit selection**: Ranks and selects the best available orbit based on configurable strategy (e.g. least cloud)
- **Imagery stitching**: Merges `.npy` tiles into a full-scene array
- **GeoTIFF output**: Exports `.tif` images with full geospatial metadata
- **Archived result viewing**: View NDVI and true-color outputs from any previously archived run
- **Interactive visualisation tool with side-by-side NDVI / RGB view**
- **Timeseries job support**: Automatically splits profile into per-interval sub-jobs using `time_series_mode`
- **Full CLI workflow**: Reproducible data generation with Makefile commands

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

This will create a `.zip` file under `archive/veg_index_april5.zip`. It contains all outputs of the selected run and can be visualized interactively using:

```bash
make view archive=veg_index_april5
```

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
├── get_timeseries.py       # Generate data across a time series using sub-jobs
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
├── visualise_data.py       # NDVI / RGB visualisation with metadata panel
├── archive_data.py         # Archive outputs into a named or timestamped folder
├── clean_outputs.py        # Output folder cleanup
├── tests/
│   ├── file_io.py
│   └── image_utils_test.py
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

For timeseries jobs, outputs are structured like:

```
outputs/<parent_job_id>/
├── <sub_job_id_1>/
│   ├── raw_tiles/
│   ├── stitched/
│   ├── imagery/
│   └── metadata/
└── <sub_job_id_2>/
    └── ...
```

Archived results are saved in `archive/<label or timestamp>.zip`. These can be visualised without extraction using `make view`.

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
