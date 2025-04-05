import os

def generate_job_id(config: "DataAcquisitionConfig") -> str:
    """
    Generate a human-readable job ID from a DataAcquisitionConfig object.

    Args:
        config (DataAcquisitionConfig): The configuration object for a data acquisition job.

    Returns:
        str: A standardized job ID string.
    """
    start = config.time_interval[0].strftime('%Y%m%d')
    end = config.time_interval[1].strftime('%Y%m%d')
    region = config.region.lower().replace(" ", "_")
    index = config.index_type.lower()
    return f"{region}__{index}__{start}_{end}"


def get_job_output_paths(config: "DataAcquisitionConfig") -> dict:
    """
    Return a dictionary of standardized output paths based on the job ID.

    Args:
        config (DataAcquisitionConfig): The configuration object for a data acquisition job.

    Returns:
        dict: A dictionary of output paths keyed by content type.
    """
    base = os.path.join("outputs", config.job_id)
    return {
        "base": base,
        "raw_tiles": os.path.join(base, "raw_tiles"),
        "imagery": os.path.join(base, "imagery"),
        "metadata": os.path.join(base, "metadata"),
        "stitched": os.path.join(base, "stitched"),
    }

def prepare_job_output_dirs(config: "DataAcquisitionConfig") -> dict:
    paths = get_job_output_paths(config)
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    return paths