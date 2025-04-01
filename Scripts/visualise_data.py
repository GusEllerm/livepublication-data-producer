import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import reshape_as_image
import numpy as np

# Load NDVI
with rasterio.open("tiles_canterbury/ndvi.tif") as ndvi_src:
    ndvi = ndvi_src.read(1)

# Load true color (and normalize if needed)
with rasterio.open("tiles_canterbury/true_color.tif") as rgb_src:
    rgb = reshape_as_image(rgb_src.read()).astype(np.float32)
    rgb /= np.max(rgb)  # normalize to [0, 1] if needed

# Set up the plot
fig, ax = plt.subplots()
ndvi_im = ax.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
rgb_im = ax.imshow(rgb)
rgb_im.set_visible(False)  # Start with NDVI

plt.title("Press 't' to toggle NDVI / True Color")
plt.axis('off')

# Keyboard event to toggle
def toggle(event):
    if event.key == 't':
        ndvi_im.set_visible(not ndvi_im.get_visible())
        rgb_im.set_visible(not rgb_im.get_visible())
        fig.canvas.draw()

fig.canvas.mpl_connect('key_press_event', toggle)
plt.show()