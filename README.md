# 🌱 LivePublication Data Producer

- **Unique product metadata indexing**: Automatically discovers and saves detailed metadata for each unique Sentinel-2 product contributing to the final composite using the Copernicus Catalog API

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
- **Accurate orbit geometry filtering**: Orbit selection now uses true Sentinel-2 data geometry, not bounding boxes, for accurate tile coverage comparison
- **Provenance tracking of Data Products:** Discovers and saves metadata for unique data products used to create the final composite image
- **Profile-based job IDs**: Each run generates a unique job ID from the profile, enabling reproducible, structured output
- **Configurable output location**: All outputs can be redirected to a custom directory using the `output_base_dir` attribute in each profile
- **Smart tiling**: Automatically splits large requests into API-safe sub-tiles
- **Orbit selection**: Ranks and selects the best available orbit based on configurable strategy (e.g. least cloud)
- **Imagery stitching**: Merges `.npy` tiles into a full-scene array
- **GeoTIFF output**: Exports `.tif` images with full geospatial metadata
- **Archived result viewing**: View NDVI and true-color outputs from any previously archived run
- **Interactive visualisation tool with side-by-side NDVI / RGB view**
- **Timeseries job support**: Automatically splits profile into per-interval sub-jobs using `time_series_mode`

---

## 🚀 Quick Start

### 🔐 Sentinel Hub Authentication

Before running any workflows, create a `secrets.json` file inside the `Scripts/` directory with your Sentinel Hub credentials:

```json
{
  "sh_client_id": "your_client_id",
  "sh_client_secret": "your_client_secret",
  "sh_base_url": "https://sh.dataspace.copernicus.eu",
  "sh_token_url": "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
}
```

You can generate an OAuth client by following the instructions here:
👉 [Copernicus Dataspace Authentication Guide](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Overview/Authentication.html)

> 💡 Tip: Use `logging.basicConfig(level=logging.DEBUG)` to enable verbose HTTP logging for Sentinel Hub API debugging.

---

### 🛠️ Installation

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

---

## 📑 Profiles and Configuration

Profiles define the **area of interest**, **timeframe**, **output location**, and other parameters for data retrieval. Each profile is a Python object (typically a `dataclass`) defined in `Scripts/profiles.py`. Profiles are passed to workflows like `get_data.py` or `get_timeseries.py`.

1. 🧾 Example Profile

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DataAcquisitionConfig:
    job_name: str
    bbox: list[float]                # Bounding box [minLon, minLat, maxLon, maxLat]
    timeframe: tuple[str, str]      # ISO-format start/end dates
    output_base_dir: str            # Local output directory (relative or absolute)
    max_cloud_cover: Optional[float] = 100.0  # Optional orbit cloud cover threshold
    time_series_mode: bool = False            # If True, runs a time series job

# Example instance
daily_ndvi_canterbury = DataAcquisitionConfig(
    job_name="daily_ndvi_canterbury",
    bbox=[172.4, -43.6, 172.8, -43.4],
    timeframe=("2024-01-01", "2024-01-31"),
    output_base_dir="outputs",  # Can also be "results/", "../data/output/", etc.
)
```

### 📦 Output Directory

Each job creates an isolated directory inside `output_base_dir`, which includes subfolders like:

```
outputs/daily_ndvi_canterbury/
├── raw_tiles/
├── stitched/
├── imagery/
└── metadata/
```

You can override this with a different directory per job, or configure all profiles in a shared location for integration with CWL workflows or other pipeline systems.

## 🗃️ Archive Example

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

> ⚙️ Behind the scenes, orbit selection computes the actual intersection between the requested tile and the Sentinel-2 orbit’s real data footprint, not just bounding boxes. This ensures only valid orbits are selected.

---

## 📂 Directory Overview

```
livepublication_data_producer/
├── __init__.py          
├── get_data.py             # Run once for current profile (single orbit)
├── get_timeseries.py       # Generate data across a time series using sub-jobs
├── profiles.py             # AOIs and config definitions
├── utils/
│   ├── __init__.py
│   ├── tile_utils.py       # Tiling and tile downloading
│   ├── image_utils.py      # NDVI + true-color stitching and processing
│   ├── metadata_utils.py   # Orbit metadata and selection (detailed product info)
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

For each run, outputs are saved to the location specified by the `output_base_dir` attribute in your profile:

```
<output_base_dir>/<job_id>/
├── raw_tiles/       # Downloaded tile `.npy` files
├── stitched/        # Stitched `.npy` bands
├── imagery/         # NDVI / RGB `.tif` and `.png`
└── metadata/        # Orbit metadata JSON
```

For timeseries jobs, outputs are structured like:

```
<output_base_dir>/<parent_job_id>/
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

The `product_metadata.json` file provides a job-wide index of all unique Sentinel-2 products used to generate the composite, including acquisition time, tile ID, and platform metadata.

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
