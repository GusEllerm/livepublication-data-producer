import argparse
from utils.job_utils import archive_job_outputs

parser = argparse.ArgumentParser(description="Archive current output files.")
parser.add_argument("--label", type=str, help="Optional label for archive folder")
parser.add_argument("--from-dir", type=str, default=".", help="Directory containing the files to archive")
args = parser.parse_args()

archive_job_outputs(src_dir=args.from_dir, label=args.label)
