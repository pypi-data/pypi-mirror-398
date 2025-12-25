import os
from datetime import datetime

from tqdm import tqdm

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path
try:
    from esrf_loadFile import loadFile
except ImportError:
    from esrf_statusgui.data_managment.loadFile import loadFile


def readSlurmLog(file_path="slurm.log"):
    """Reads the slurm.log file and extracts function names and dates."""
    if Path(file_path).is_dir():
        file_path = str(Path(file_path) / "slurm.log")
    try:
        with open(file_path) as f:
            content = f.readlines()
    except FileNotFoundError:
        print("slurm.log file not found!")
        return [], []

    fcnames = []
    dates = []

    for line in content:
        parts = line.split()
        fcnames.append(parts[1])
        dates.append(parts[3])

    return fcnames, dates


def get_last_simulation_date(fcnames, dates, target_function="gtForwardSimulate_v2"):
    """Finds the most recent date when the target function was run."""
    dates_fsim = [
        dates[i]
        for i, fname in enumerate(fcnames)
        if fname.lower() == target_function.lower()
    ]
    if dates_fsim:
        return max(datetime.fromisoformat(date) for date in dates_fsim)
    return None


def is_file_up_to_date(file_path, reference_date):
    """Checks if a file is up-to-date compared to the reference date."""
    file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
    return file_date >= reference_date


def load_index_data(phase_num, path):
    """Loads the grain data from index.mat."""
    index_path = Path(path) / "4_grains" / f"phase_{phase_num:02d}" / "index.mat"
    index_data = loadFile(index_path)
    return index_data.get_value("grain", [])


def check_grain_existence(grain_dir, num_grains):
    """Checks if grain_####.mat files exist for each grain."""
    is_grain = []
    for ii in range(1, num_grains + 1):
        grain_path = os.path.join(grain_dir, f"grain_{ii:04d}.mat")
        exists = os.path.exists(grain_path)
        if not exists:
            print(f"grain # {ii} does not exist.")
        is_grain.append(exists)
    return is_grain


def check_ids_in_grain_files(grain_dir, grain_files):
    """Checks if IDs in grain_####.mat files match their filenames."""
    discrepancies = []
    for kk in range(1, len(grain_files) + 1):
        grain_path = os.path.join(grain_dir, f"grain_{kk:04d}.mat")
        if os.path.exists(grain_path):
            grain_data = loadFile(grain_path)
            id_val = grain_data.get_value("id")
            if id_val is not None and kk != id_val:
                discrepancies.append([kk, id_val])
    return discrepancies


def check_ids_in_index(grain_data):
    """Checks if IDs in the grain data match their indices."""
    discrepancies = []
    for ii, g in enumerate(tqdm(grain_data), start=1):
        if hasattr(g, "get_value"):
            if ii != g.get_value("id"):
                discrepancies.append([ii, g.get_value("id")])
    return discrepancies


def gtFsimCheckMissingGrains(phase_num, path):
    """
    Main function to check for missing grains and discrepancies in forward simulation data.
    """
    # Read oar.log and find the last simulation date
    fcnames, dates = readSlurmLog(path)
    last_sim_date = get_last_simulation_date(fcnames, dates)

    if not last_sim_date:
        print("Forward simulation has not been run yet!")
        return {"ind": [], "old": [], "checkFsim": [], "checkIndexter": []}

    # Load grain data from index.mat
    grain_data = load_index_data(phase_num, path)
    num_grains = len(grain_data)

    # Check if grain_####.mat files are up-to-date
    grain_dir = str(Path(path) / "4_grains" / f"phase_{phase_num:02d}")
    grain_files = [
        f
        for f in os.listdir(grain_dir)
        if f.startswith("grain_details_") and f.endswith(".mat")
    ]
    is_uptodate = [
        is_file_up_to_date(os.path.join(grain_dir, file), last_sim_date)
        for file in grain_files
    ]

    # Check existence of grain_####.mat files
    is_grain = check_grain_existence(grain_dir, num_grains)

    # Compile results
    missing = {
        "ind": [i + 1 for i, val in enumerate(is_grain) if not val],
        "is_grain": is_grain,
        "old": [i + 1 for i, val in enumerate(is_uptodate) if not val],
        "is_uptodate": is_uptodate,
        "checkFsim": check_ids_in_grain_files(grain_dir, grain_files),
        "checkIndexter": check_ids_in_index(grain_data),
    }

    return missing


# Example usage:
# phase_number = 1
# result = gt_fsim_check_missing_grains(phase_number, MatFileHandler)
# print(result)
