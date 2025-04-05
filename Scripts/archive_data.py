import os
import shutil
import argparse
from datetime import datetime

# Files to archive
files_to_archive = ["ndvi.tif", "ndvi.png", "true_color.tif", "true_color.png"]

# Argument parser
parser = argparse.ArgumentParser(description="Archive current output files.")
parser.add_argument("--label", type=str, help="Optional label for archive folder")
parser.add_argument("--from-dir", type=str, default=".", help="Directory containing the files to archive")
args = parser.parse_args()

# Determine archive name
archive_base = "archive"
os.makedirs(archive_base, exist_ok=True)

if args.label:
    archive_name = args.label
else:
    archive_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

archive_path = os.path.join(archive_base, archive_name)

try:
    os.makedirs(archive_path, exist_ok=False)
    print(f"✅ Created archive folder: {archive_path}")
except FileExistsError:
    print(f"❌ Archive folder '{archive_name}' already exists. Use a different name.")
    exit(1)

# Copy each file if it exists
for fname in files_to_archive:
    src_path = os.path.join(args.from_dir, fname)
    if os.path.exists(src_path):
        shutil.copy(src_path, archive_path)
        print(f"✓ Archived {src_path}")
    else:
        print(f"⚠️  Warning: {src_path} not found, skipping.")

print(f"\n📦 Archive complete: {archive_path}")
