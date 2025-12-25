import grp
import logging
import os
import pwd

from esrf_pathlib import ESRFPath as Path

from esrf_statusgui.file_utils.paths import describe, get_visitor_root, visitor_path

logger = logging.getLogger(__name__)


def _resolve_group(path: Path) -> str | None:
    """
    Best effort resolution of the unix group that should own ``path``.

    We prefer the proposal name derived from esrf_pathlib metadata; otherwise we fall
    back to the first segment under the visitor root.
    """
    info = describe(path)
    if info.proposal:
        return info.proposal

    try:
        relative = path.relative_to(info.data_root)
    except Exception:
        visitor_root = get_visitor_root()
        try:
            relative = path.relative_to(visitor_root)
        except Exception:
            return None
    return relative.parts[0] if relative.parts else None


def _maybe_change_group(path: str, group_info, change_group: bool) -> None:
    if not change_group or group_info is None:
        return
    try:
        os.chown(path, -1, group_info.gr_gid)
    except PermissionError as exc:
        logger.debug("Skipping chown for %s: %s", path, exc)


def set_permissions_recursive(
    path: Path, dir_mode: int = 0o2770, file_mode: int = 0o660
):
    """
    Recursively set permissions for a visitor folder.

    Params
    ------
    path:
        Target folder (any ESRFPath compatible path).
    dir_mode:
        Mode applied to directories (defaults to SGID + group rwx).
    file_mode:
        Mode applied to files (defaults to group read/write).
    """
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(
            f"Cannot set permissions, path does not exist: {target}"
        )

    group_name = _resolve_group(target)
    group_info = None
    change_group = False
    if group_name:
        try:
            group_info = grp.getgrnam(group_name)
            current_user = os.getenv("USER") or pwd.getpwuid(os.getuid()).pw_name
            change_group = (
                current_user in group_info.gr_mem or os.getgid() == group_info.gr_gid
            )
        except KeyError:
            logger.warning("Group %s not found on this system.", group_name)
        except Exception as exc:
            logger.debug(
                "Failed to resolve group information for %s: %s", group_name, exc
            )

    def _apply(path_str: str, mode: int) -> None:
        _maybe_change_group(path_str, group_info, change_group)
        try:
            os.chmod(path_str, mode)
        except PermissionError as exc:
            logger.debug("Skipping chmod for %s: %s", path_str, exc)

    # Apply to root folder and contents
    _apply(str(target), dir_mode)
    for root, dirs, files in os.walk(target):
        for dirname in dirs:
            _apply(os.path.join(root, dirname), dir_mode)
        for filename in files:
            _apply(os.path.join(root, filename), file_mode)


def newExperimentDate(folder: Path, download_code: bool = False):
    """Create a new experiment directory structure and optionally download code."""
    folder = Path(folder)
    processed_data = folder / "PROCESSED_DATA"
    scripts = folder / "SCRIPTS"

    # Create directories
    logger.info("Creating directory %s (parents=True, exist_ok=True)", processed_data)
    processed_data.mkdir(parents=True, exist_ok=True)
    logger.info("Creating directory %s (parents=True, exist_ok=True)", scripts)
    scripts.mkdir(parents=True, exist_ok=True)

    # set_permissions_recursive(folder)

    # if download_code:
    #     #TODO: Change import method. No need to import the codes now
    #     statusGUI.change_path(folder)
    #     statusGUI.setup_code_from_git()


if __name__ == "__main__":
    folder = visitor_path("ma6062", "id11", "2025_05_12")
    downloadCode = True
    newExperimentDate(folder, downloadCode)
