import logging
import os
import shutil
from collections.abc import Mapping

import ipywidgets as widgets
from esrf_pathlib import ESRFPath as Path
from IPython.display import display

logger = logging.getLogger(__name__)

MODE_LINK = "Rs"
MODE_COPY = "R"
VALID_MODES = {MODE_LINK, MODE_COPY}

DEFAULT_DIRECTORY_MODES: dict[str, str] = {
    "0_rawdata": MODE_LINK,
    "1_preprocessing": MODE_LINK,
    "2_difspot": MODE_LINK,
    "2_difblob": MODE_LINK,
    "3_pairmatching": MODE_COPY,
    "4_grains": MODE_COPY,
    "5_reconstruction": MODE_COPY,
    "6_rendering": MODE_COPY,
    "7_fed": MODE_COPY,
    "8_analysis": MODE_COPY,
    "9_forwardrecon": MODE_COPY,
    "temp": MODE_LINK,
}

DIRECTORY_ORDER: tuple[str, ...] = tuple(DEFAULT_DIRECTORY_MODES.keys())


def _safe_remove(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
        return
    if not path.exists():
        return
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _clone_symlink(src: Path, dest: Path) -> None:
    link_target = os.readlink(str(src))
    _safe_remove(dest)
    os.symlink(link_target, str(dest))


def _copy_file(src: Path, dest: Path) -> None:
    _safe_remove(dest)
    shutil.copy2(src, dest)


def _link_directory_contents(src: Path, dest: Path) -> None:
    _safe_remove(dest)
    logger.info("Creating directory %s (parents=True, exist_ok=True)", dest)
    dest.mkdir(parents=True, exist_ok=True)

    try:
        with os.scandir(src) as entries:
            for entry in entries:
                link_path = dest / entry.name
                _safe_remove(link_path)
                link_path.symlink_to(entry.path, target_is_directory=entry.is_dir())
    except OSError as exc:
        logging.warning("Failed to link contents from %s: %s", src, exc)


def _copy_directory(src: Path, dest: Path) -> None:
    _safe_remove(dest)
    shutil.copytree(src, dest, symlinks=True)


def _build_directory_modes(overrides: Mapping[str, str]) -> dict[str, str]:
    modes = DEFAULT_DIRECTORY_MODES.copy()
    for key, value in overrides.items():
        if key not in modes:
            logging.warning("Ignoring unknown directory override '%s'.", key)
            continue
        if value not in VALID_MODES:
            logging.warning(
                "Ignoring unsupported mode '%s' for '%s'. Expected one of %s.",
                value,
                key,
                ", ".join(sorted(VALID_MODES)),
            )
            continue
        modes[key] = value
    return modes


def gtMoveData(olddir: str, newdir: str, output: widgets.Output, **kwargs: str) -> None:
    """
    Link ('cp -Rs') or copy ('cp -R') data from a restored, read-only analysis session into
    a new session where results can be re-analysed.

    Parameters
    ----------
    olddir : str
        Path to the original (restored) analysis directory.
    newdir : str
        Path to the target analysis directory that will host the links or copies.
    output : widgets.Output
        Output widget used to display progress bars in the notebook UI.
    **kwargs : str
        Optional per-directory overrides. Accepts keys matching the known directory names and
        values of 'Rs' (link contents) or 'R' (copy contents).
    """
    directory_modes = _build_directory_modes(kwargs)

    old_path = Path(olddir).resolve()
    if not old_path.exists():
        raise FileNotFoundError(f"Source directory '{old_path}' does not exist.")

    new_path = Path(newdir)
    logger.info("Creating directory %s (parents=True, exist_ok=True)", new_path)
    new_path.mkdir(parents=True, exist_ok=True)

    try:
        with os.scandir(old_path) as entries:
            items = [Path(entry.path) for entry in entries]
    except OSError as exc:
        raise FileNotFoundError(
            f"Cannot list source directory '{old_path}': {exc}"
        ) from exc
    file_progress = widgets.IntProgress(
        value=0,
        min=0,
        max=len(items),
        description="Copying files:",
        bar_style="info",
        style={"bar_color": "green"},
        orientation="horizontal",
    )
    with output:
        display(file_progress)

    for index, item in enumerate(items, start=1):
        dest_item = new_path / item.name
        if item.is_symlink():
            _clone_symlink(item, dest_item)
        elif item.is_file():
            _copy_file(item, dest_item)
        file_progress.value = index

    dir_progress = widgets.IntProgress(
        value=0,
        min=0,
        max=len(DIRECTORY_ORDER),
        description="Copying directories:",
        bar_style="info",
        style={"bar_color": "green"},
        orientation="horizontal",
    )
    with output:
        display(dir_progress)

    for index, dir_name in enumerate(DIRECTORY_ORDER, start=1):
        src = old_path / dir_name
        dest = new_path / dir_name

        if not src.exists():
            dir_progress.value = index
            continue

        mode = directory_modes[dir_name]
        if mode == MODE_LINK:
            _link_directory_contents(src, dest)
        else:
            _copy_directory(src, dest)

        dir_progress.value = index
