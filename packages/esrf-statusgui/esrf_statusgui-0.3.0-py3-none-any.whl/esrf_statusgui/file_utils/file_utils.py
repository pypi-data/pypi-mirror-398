import logging
import os
from datetime import datetime

from esrf_pathlib import ESRFPath as Path

from esrf_statusgui.file_utils.newExperimentDate import set_permissions_recursive

logger = logging.getLogger(__name__)


def path_is_root_of(root_path: Path, child_path: Path):
    try:
        # Check if child_path is relative to root_path
        Path(child_path).relative_to(root_path)
        return True
    except ValueError:
        # If ValueError is raised, child_path is not under root_path
        return False


def is_date(string: str, date_format="%Y%m%d"):
    try:
        return datetime.strptime(string, date_format)
    except ValueError:
        return False


def create_DCT_directories(base_dir: Path, name: str):
    required_dirs = [
        "0_rawdata",
        "0_rawdata/Orig",
        "1_preprocessing",
        "1_preprocessing/full",
        "1_preprocessing/abs",
        "1_preprocessing/ext",
        "2_difspot",
        "2_difblob",
        "3_pairmatching",
        "4_grains",
        "4_grains/phase_01",
        "5_reconstruction",
        "6_rendering",
        "7_fed",
        "8_analysis",
        "8_analysis/figures",
        "OAR_log",
        f"0_rawdata/{name}",
    ]
    for dir_suffix in required_dirs:
        logger.info(
            "Creating directory %s (parents=True, exist_ok=True)",
            base_dir / dir_suffix,
        )
        os.makedirs(base_dir / dir_suffix, exist_ok=True)
    set_permissions_recursive(base_dir)
