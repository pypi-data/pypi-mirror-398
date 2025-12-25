from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from os import PathLike

from esrf_pathlib import ESRFPath as Path
from esrf_pathlib.schemas._base import get_default_data_root

__all__ = [
    "VISITOR_ENV_VAR",
    "DEFAULT_VISITOR_ROOT",
    "get_visitor_root",
    "set_visitor_root",
    "visitor_path",
    "relative_to_visitor",
    "is_under_visitor",
    "as_esrf_path",
    "ESRFPathInfo",
    "describe",
    "clean_dir_name",
]

VISITOR_ENV_VAR = "ESRF_VISITOR_ROOT"
DEFAULT_VISITOR_ROOT = Path(get_default_data_root(None) or "/data/visitor")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ESRFPathInfo:
    """Normalized view of an ESRF path."""

    path: Path
    data_root: Path
    proposal: str | None
    beamline: str | None
    session_date: date | None

    @property
    def relative_to_root(self) -> Path:
        cleaned_path, _, _, _ = clean_dir_name(self.path)
        cleaned_data_root, _, _, _ = clean_dir_name(self.data_root)
        return cleaned_path.relative_to(cleaned_data_root)


def _to_pathlike(value: str | PathLike[str] | Path) -> str:
    if isinstance(value, Path):
        return str(value)
    return os.fspath(value)


def _safe_attr(path: Path, attr: str):
    if hasattr(path, attr):
        return getattr(path, attr)
    else:
        return None


def _strip_after_first_token(path_str: str, tokens: tuple[str, ...]) -> str:
    """Split ``path_str`` on the first matching token and return the tail."""
    for token in tokens:
        if token in path_str:
            # Split once; keep everything after the matched token
            return path_str.split(token, 1)[1] or "/"
    return path_str


def clean_dir_name(
    path: str | PathLike[str] | Path, interactive: str | bool = False
) -> tuple[Path, str, Path, str]:
    """
    Clean a filesystem path following the MATLAB ``gtCleanDirName`` logic.

    Steps:
    - Drop GPFS prefixes (``/gpfs/{easy,jazzy,ga,gb}``) or ``/mnt/storage``.
    - Replace ``.`` with ``p`` and ``-`` with ``_`` in every segment.
    - Return the cleaned path and its last component along with the originals.

    Parameters
    ----------
    path:
        Path to normalize.
    interactive:
        If a string, override the returned name. If truthy, allow interactive
        override via ``input()`` (best-effort; ignored on stdin errors).
    """

    orig_path = Path(_to_pathlike(path))
    working = orig_path.as_posix()

    if "/gpfs" in working:
        working = _strip_after_first_token(working, ("/easy", "/jazzy", "/ga", "/gb"))
    if "/mnt" in working:
        working = _strip_after_first_token(working, ("/storage",))

    orig_name = Path(working).name

    cleaned_str = working.replace(".", "p").replace("-", "_")
    clean_path = Path(cleaned_str)
    name = clean_path.name

    if isinstance(interactive, str):
        name = interactive
    elif interactive:
        try:
            user_path = input(f"directory path [{clean_path}]: ").strip()
            if user_path:
                clean_path = Path(user_path)
            user_name = input(f"scan name [{name}]: ").strip()
            if user_name:
                name = user_name
        except (EOFError, KeyboardInterrupt):
            # Fall back to the automatically cleaned values
            pass

    return clean_path, name, orig_path, orig_name


def as_esrf_path(
    value: str | PathLike[str] | Path, *, assume_root: bool = True
) -> Path:
    """
    Return value as an ESRFPath. Relative paths are resolved against the visitor root by default.
    """
    if isinstance(value, Path):
        esrf_path = value
    else:
        esrf_path = Path(_to_pathlike(value))

    if not esrf_path.is_absolute() and assume_root:
        esrf_path = get_visitor_root() / esrf_path
    return Path(str(esrf_path))


@lru_cache
def get_visitor_root() -> Path:
    """
    Return the configured ESRF visitor root, defaulting to ``/data/visitor``.

    The location can be overridden via the ``ESRF_VISITOR_ROOT`` environment variable.
    """
    candidate = os.environ.get(VISITOR_ENV_VAR)
    if candidate:
        try:
            return Path(candidate)
        except Exception as error:
            logger.warning(
                "Ignoring invalid visitor root override '%s': %s", candidate, error
            )
    return DEFAULT_VISITOR_ROOT


def set_visitor_root(new_root: str | PathLike[str] | None) -> None:
    """
    Override the visitor root for the current process.

    Clearing the override (calling with ``None`` or ``\"\"``) resets to the default path.
    """
    if not new_root:
        os.environ.pop(VISITOR_ENV_VAR, None)
    else:
        os.environ[VISITOR_ENV_VAR] = os.fspath(new_root)
    get_visitor_root.cache_clear()


def describe(path: str | PathLike[str] | Path) -> ESRFPathInfo:
    """
    Return structured information about an ESRF path using esrf_pathlib metadata.
    """
    cleaned_path, _, _, _ = clean_dir_name(path)
    esrf_path = as_esrf_path(cleaned_path)
    data_root = _safe_attr(esrf_path, "data_root") or str(get_visitor_root())
    proposal = _safe_attr(esrf_path, "proposal")
    beamline = _safe_attr(esrf_path, "beamline")
    session_date = _safe_attr(esrf_path, "session_date")
    return ESRFPathInfo(
        path=esrf_path,
        data_root=Path(data_root),
        proposal=proposal,
        beamline=beamline,
        session_date=session_date,
    )


def visitor_path(*parts: str | PathLike[str]) -> Path:
    """
    Build a path inside the visitor root.

    ``visitor_path(\"ma6062\", \"id11\")`` -> ``/data/visitor/ma6062/id11`` (using ESRFPath).
    """
    root = get_visitor_root()
    string_parts = [_to_pathlike(part) for part in parts]
    return Path(root.joinpath(*string_parts))


def relative_to_visitor(path: str | PathLike[str] | Path) -> Path:
    """Return ``path`` relative to the visitor root."""
    info = describe(path)
    return info.relative_to_root


def is_under_visitor(path: str | PathLike[str] | Path) -> bool:
    """Return True if ``path`` lives under the visitor root."""
    try:
        _relative_path = describe(path).relative_to_root
    except Exception:
        return False
    return bool(_relative_path)
