import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import matplotlib.gridspec as gridspec

# === Load parser and arguments ===
parser = argparse.ArgumentParser()
parser.add_argument("--archive", type=str, default=None, help="Optional archive folder name")
args = parser.parse_args()

# Determine input directory
import glob
if args.archive:
    base_path = os.path.join("archive", args.archive)
else:
    output_dirs = sorted(glob.glob("outputs/*/"), key=os.path.getmtime, reverse=True)
    if not output_dirs:
        raise FileNotFoundError("No output directories found in 'outputs/'.")
    base_path = output_dirs[0].rstrip("/")

# Get the paths for NDVI and RGB images
import matplotlib.image as mpimg

if args.archive:
    ndvi_path = os.path.join(base_path, "ndvi.png")
    rgb_path = os.path.join(base_path, "true_color.png")
else:
    ndvi_path = os.path.join(base_path, "imagery", "ndvi.png")
    rgb_path = os.path.join(base_path, "imagery", "true_color.png")

ndvi = mpimg.imread(ndvi_path)
rgb = mpimg.imread(rgb_path)

# Set up the plot
fig = plt.figure(figsize=(12, 8))
gs = gridspec.GridSpec(2, 2, height_ratios=[3, 1])

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])

syncing = {"flag": False}  # Use dict to maintain mutability across scope

def on_axis_change(event_ax):
    if syncing["flag"]:
        return
    syncing["flag"] = True
    try:
        xlim = event_ax.get_xlim()
        ylim = event_ax.get_ylim()
        for ax in (ax1, ax2):
            if ax != event_ax:
                ax.set_xlim(xlim)
                ax.set_ylim(ylim)
    finally:
        syncing["flag"] = False

ax1.callbacks.connect('xlim_changed', lambda ax: on_axis_change(ax1))
ax1.callbacks.connect('ylim_changed', lambda ax: on_axis_change(ax1))
ax2.callbacks.connect('xlim_changed', lambda ax: on_axis_change(ax2))
ax2.callbacks.connect('ylim_changed', lambda ax: on_axis_change(ax2))

ax_text = fig.add_subplot(gs[1, :])

ndvi_im = ax1.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
rgb_im = ax2.imshow(rgb)

plt.title("Press 't' to toggle NDVI / True Color")
ax1.axis('off')
ax2.axis('off')

# --- If outputs structure, try loading orbit metadata
if not args.archive:
    import json
    import glob

    metadata_dir = os.path.join(base_path, "metadata")
    selected_orbits = glob.glob(os.path.join(metadata_dir, "*_selected_orbit.json"))

    if selected_orbits:
        product_entries = {}  # key: product_id, value: cloud_coverage
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

        meta_summary = "\n".join(meta_lines)

        ax_text.axis("off")
        ax_text.text(0, 1, meta_summary, fontsize=9, color='black',
                     verticalalignment='top', family='monospace')

# Keyboard event to toggle
def toggle(event):
    if event.key == 't':
        ndvi_im.set_visible(not ndvi_im.get_visible())
        rgb_im.set_visible(not rgb_im.get_visible())
        fig.canvas.draw()

def on_scroll(event):
    base_scale = 1.2
    if event.inaxes not in [ax1, ax2]:
        return

    ax = event.inaxes
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()
    xdata = event.xdata
    ydata = event.ydata

    if event.button == 'up':
        scale_factor = 1 / base_scale
    elif event.button == 'down':
        scale_factor = base_scale
    else:
        scale_factor = 1

    new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
    new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

    relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
    rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

    for ax in [ax1, ax2]:
        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

    fig.canvas.draw_idle()

fig.canvas.mpl_connect('key_press_event', toggle)
fig.canvas.mpl_connect('scroll_event', on_scroll)
plt.show()