import argparse
import atexit
import glob
import json
import os
import shutil
import zipfile

import matplotlib.gridspec as gridspec
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

# === Load parser and arguments ===
parser = argparse.ArgumentParser()
parser.add_argument("--archive", type=str, default=None, help="Optional archive folder name")
args = parser.parse_args()

temp_extract_dir = None

def extract_archive_if_needed(archive_name):
    global temp_extract_dir
    if archive_name:
        archive_path = os.path.join("archive", archive_name)
        if os.path.isfile(archive_path) and archive_path.endswith(".zip"):
            # Create a temporary extraction directory within archive/
            temp_extract_dir = os.path.join("archive", archive_name.replace(".zip", ""))
            os.makedirs(temp_extract_dir, exist_ok=True)

            print(archive_path)
            # Extract the zip file to the temporary directory
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
                print(f"✓ Extracted {archive_path} to {temp_extract_dir}")

            print(f"📦 Extracted archive '{archive_name}' to temporary location for viewing.")

            def cleanup_temp_dir():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            atexit.register(cleanup_temp_dir)
            return temp_extract_dir
        else:
            return archive_path
    return None

base_path = extract_archive_if_needed(args.archive)

if base_path is None:
    output_dirs = sorted(glob.glob("outputs/*/"), key=os.path.getmtime, reverse=True)
    if not output_dirs:
        raise FileNotFoundError("No output directories found in 'outputs/'.")
    base_path = output_dirs[0].rstrip("/")

def format_metadata_summary(selected_orbits):
    metadata_summary = ""
    if selected_orbits:
        product_entries = {}
        strategies = set()
        orbit_dates = set()

        for f in selected_orbits:
            with open(f) as meta_file:
                data = json.load(meta_file)
                strategies.add(data.get("strategy", ""))
                orbit_dates.add(data.get("orbit_date", ""))
                for pid in data.get("product_ids", []):
                    if pid not in product_entries:
                        product_entries[pid] = data.get("cloud_coverage", 0.0)

        meta_lines = [
            f"Strategy: {', '.join(strategies)}",
            f"Orbit Dates: {', '.join(sorted(orbit_dates))}",
            f"Products:"
        ]
        for i, (pid, cc) in enumerate(product_entries.items()):
            meta_lines.append(f"  {i+1}. Product ID: {pid}")
            meta_lines.append(f"     Cloud Cover: {cc:.2f}%")

        avg_cloud = sum(product_entries.values()) / len(product_entries) if product_entries else 0.0
        meta_lines.append(f"\nAverage Cloud Cover: {avg_cloud:.2f}%")
        metadata_summary = "\n".join(meta_lines)
    return metadata_summary

def load_timeseries_frames(base_path):
    timeseries_frames = []
    subdirs = sorted([
        os.path.join(base_path, d) for d in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, d))
    ])
    for subdir in subdirs:
        ndvi_path = os.path.join(subdir, "imagery", "ndvi.png")
        rgb_path = os.path.join(subdir, "imagery", "true_color.png")
        metadata_dir = os.path.join(subdir, "metadata")
        selected_orbits = glob.glob(os.path.join(metadata_dir, "*_selected_orbit.json"))

        if os.path.exists(ndvi_path) and os.path.exists(rgb_path):
            ndvi = mpimg.imread(ndvi_path)
            rgb = mpimg.imread(rgb_path)
            meta_summary = format_metadata_summary(selected_orbits)
            label = os.path.basename(subdir)
            timeseries_frames.append({
                "ndvi": ndvi,
                "rgb": rgb,
                "metadata": meta_summary,
                "label": label
            })
    return timeseries_frames

def load_single_frame(base_path):
    ndvi_path = os.path.join(base_path, "imagery", "ndvi.png")
    rgb_path = os.path.join(base_path, "imagery", "true_color.png")
    metadata_dir = os.path.join(base_path, "metadata")
    selected_orbits = glob.glob(os.path.join(metadata_dir, "*_selected_orbit.json"))

    ndvi = mpimg.imread(ndvi_path)
    rgb = mpimg.imread(rgb_path)
    metadata_summary = format_metadata_summary(selected_orbits)
    
    return ndvi, rgb, metadata_summary

# Determine if this is a timeseries job (has sub-job folders)
is_timeseries = any(
    os.path.isdir(os.path.join(base_path, name)) and 
    os.path.isdir(os.path.join(base_path, name, "imagery"))
    for name in os.listdir(base_path)
)

# Load data
timeseries_frames = load_timeseries_frames(base_path) if is_timeseries else []
ndvi, rgb, metadata_summary = load_single_frame(base_path) if not is_timeseries else (None, None, None)

def setup_figure():
    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(2, 2, height_ratios=[3, 1])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax_text = fig.add_subplot(gs[1, :])
    ax_text.axis("off")
    return fig, ax1, ax2, ax_text

fig, ax1, ax2, ax_text = setup_figure()
frame_idx = [0]

def draw_frame(idx):
    ax1.clear()
    ax2.clear()
    ax_text.clear()
    ax_text.axis("off")
    ax1.axis("off")
    ax2.axis("off")

    if is_timeseries:
        frame = timeseries_frames[idx]
        ax1.imshow(frame["ndvi"], cmap='RdYlGn', vmin=-1, vmax=1)
        ax2.imshow(frame["rgb"])
        ax_text.text(0, 1, frame["metadata"], fontsize=9, color='black',
                     verticalalignment='top', family='monospace')
        fig.suptitle(f"Frame {idx+1}/{len(timeseries_frames)} — {frame['label']}")
    else:
        ax1.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
        ax2.imshow(rgb)
        ax_text.text(0, 1, metadata_summary, fontsize=9, color='black',
                     verticalalignment='top', family='monospace')

    fig.canvas.draw_idle()

def on_key(event):
    if not is_timeseries:
        return
    if event.key == 'right':
        frame_idx[0] = min(frame_idx[0] + 1, len(timeseries_frames) - 1)
        draw_frame(frame_idx[0])
    elif event.key == 'left':
        frame_idx[0] = max(frame_idx[0] - 1, 0)
        draw_frame(frame_idx[0])

def on_scroll(event):
    base_scale = 1.2
    if event.inaxes not in [ax1, ax2]:
        return

    ax = event.inaxes
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()
    xdata = event.xdata
    ydata = event.ydata

    scale_factor = 1 / base_scale if event.button == 'up' else base_scale

    new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
    new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
    relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
    rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

    for ax in [ax1, ax2]:
        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

    fig.canvas.draw_idle()

fig.canvas.mpl_connect('key_press_event', on_key)
fig.canvas.mpl_connect('scroll_event', on_scroll)
draw_frame(0)
plt.show()