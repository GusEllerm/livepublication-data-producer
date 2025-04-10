from __future__ import annotations

import calendar
import json
import os
import shutil
from datetime import date, datetime, timedelta
from typing import Any

import cv2
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from dateutil.relativedelta import relativedelta
from profiles import DataAcquisitionConfig
from rasterio.transform import from_bounds
from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    MimeType,
    SentinelHubRequest,
    bbox_to_dimensions,
)
