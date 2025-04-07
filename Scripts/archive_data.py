import argparse
from utils.job_utils import archive_job_outputs

parser = argparse.ArgumentParser(
    description="Compress the current output directory into a ZIP archive stored in archive/."
)
parser.add_argument("--from-dir", type=str, default=None)
parser.add_argument("--label", type=str, default=None)
args = parser.parse_args()

archive_job_outputs(output_dir=args.from_dir, label=args.label)
