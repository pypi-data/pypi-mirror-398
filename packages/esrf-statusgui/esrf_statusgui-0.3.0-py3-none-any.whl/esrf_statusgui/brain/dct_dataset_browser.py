from __future__ import annotations

import logging
import os
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path
try:
    from esrf_loadFile import loadFile
except ImportError:
    from esrf_statusgui.data_managment.loadFile import loadFile

from esrf_statusgui.file_utils.file_utils import path_is_root_of
from esrf_statusgui.file_utils.fileNode import DCTNode

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DirectoryInfo:
    """Light-weight representation of a directory in the DCT browser tree."""

    name: str
    path: Path
    has_dct_h5: bool


@dataclass(frozen=True)
class FileInfo:
    """Represents a file entry exposed to the DCT browser UI."""

    name: str
    path: Path

    @property
    def suffix(self) -> str:
        return self.path.suffix


class DCTDatasetBrowserLogic:
    """
    Encapsulates filesystem traversal and caching for the DCT dataset browser UI.

    The logic keeps a cached tree of the currently explored RAW_DATA folder while
    exposing directory listings, file listings, and lightweight helpers to fetch
    file previews.
    """

    def __init__(self, initial_folder: Path | str | None) -> None:
        self.current_folder: Path | None = (
            Path(initial_folder) if initial_folder else None
        )
        self.cache: DCTNode | None = None
        self.cache_folder: Path | None = None

        if self.current_folder and self.current_folder.is_file():
            self.current_folder = self.current_folder.parent

    # ------------------------------------------------------------------ #
    # Cache management
    # ------------------------------------------------------------------ #
    def set_current_folder(self, folder: Path | str | None) -> None:
        """Update the folder being browsed."""
        if folder is None:
            self.current_folder = None
        else:
            self.current_folder = Path(folder)
            if self.current_folder.is_file():
                self.current_folder = self.current_folder.parent

    def ensure_cache(self) -> DCTNode | None:
        """
        Ensure that the cache matches the current folder.
        Returns the cached root node or None if no folder is selected.
        """
        if self.current_folder is None:
            return None

        if (
            self.cache is None
            or self.cache_folder is None
            or not path_is_root_of(self.cache_folder, self.current_folder)
        ):
            return self.build_and_cache_structure()
        return self.cache

    def build_and_cache_structure(self) -> DCTNode | None:
        """(Re)build the cached tree starting from the current folder."""
        if self.current_folder is None:
            self.cache = None
            self.cache_folder = None
            return None

        self.cache_folder = self.current_folder
        self.cache = self._build_structure(self.cache_folder)
        return self.cache

    def refresh(self) -> DCTNode | None:
        """
        Force a rebuild of the cache for the current folder and return the node
        associated with the refreshed folder.
        """
        if self.current_folder is None:
            return None

        self.build_and_cache_structure()
        return self.get_node(self.current_folder)

    def _build_structure(self, root_path: Path) -> DCTNode:
        """
        Breadth-first traversal that caches all subdirectories and DCT H5 files
        beneath `root_path`.
        """
        root_node = DCTNode(root_path)
        queue: deque[DCTNode] = deque([root_node])

        while queue:
            current_node = queue.popleft()
            try:
                with os.scandir(current_node.path) as entries:
                    for entry in entries:
                        if entry.name.startswith("."):
                            continue
                        entry_path = Path(entry.path)
                        if entry.is_dir():
                            child_node = DCTNode(entry_path)
                            current_node.add_child(child_node)
                            queue.append(child_node)
                        elif entry.is_file() and self._is_dct_h5(entry.name):
                            current_node.add_child(DCTNode(entry_path))
            except PermissionError:
                logger.warning("Permission denied: %s", current_node.path)
            except FileNotFoundError:
                logger.warning("Folder removed while scanning: %s", current_node.path)

        root_node.update_has_dct_h5_recursively()
        return root_node

    # ------------------------------------------------------------------ #
    # Listings
    # ------------------------------------------------------------------ #
    def get_node(self, folder: Path | str | None) -> DCTNode | None:
        """
        Return the cached node for the given folder (defaults to current folder).
        """
        target: Path | None
        if folder is None:
            target = self.current_folder
        else:
            target = Path(folder)

        if target is None:
            return None

        cache = self.ensure_cache()
        if cache is None:
            return None
        return cache.find_by_path(str(target))

    def list_directories(self, folder: Path | str | None = None) -> list[DirectoryInfo]:
        """Return child directories for `folder` (current folder by default)."""
        node = self.get_node(folder)
        if not node or not node.children:
            return []

        directories: list[DirectoryInfo] = []
        for child in node.children:
            if getattr(child, "is_file", False):
                continue
            directories.append(
                DirectoryInfo(
                    name=child.name,
                    path=Path(child.path),
                    has_dct_h5=bool(getattr(child, "has_dct_h5", False)),
                )
            )
        return directories

    def list_dct_h5_files(self, folder: Path | str | None = None) -> list[FileInfo]:
        """Return DCT H5 files located directly in `folder`."""
        node = self.get_node(folder)
        if not node or not node.children:
            return []

        files: list[FileInfo] = []

        def collect_dct_files(current) -> None:
            if getattr(current, "is_file", False) and self._is_dct_h5(current.name):
                files.append(FileInfo(name=current.name, path=Path(current.path)))
                return
            if getattr(current, "children", None):
                for child in current.children:
                    collect_dct_files(child)

        collect_dct_files(node)
        files.sort(key=lambda info: info.name.lower())
        return files

    def list_other_files(self, folder: Path | str | None = None) -> list[FileInfo]:
        """
        Return non-DCT files in the given folder (current folder by default).
        """
        folder_path = Path(folder) if folder else self.current_folder
        if folder_path is None or not os.path.isdir(folder_path):
            return []

        other_files: list[FileInfo] = []
        try:
            with os.scandir(folder_path) as entries:
                for entry in entries:
                    if not entry.is_file():
                        continue
                    if self._is_dct_h5(entry.name):
                        continue
                    other_files.append(FileInfo(name=entry.name, path=Path(entry.path)))
        except PermissionError:
            logger.warning("Permission denied: %s", folder_path)
        except FileNotFoundError:
            logger.warning("Folder removed while listing files: %s", folder_path)

        other_files.sort(key=lambda info: info.name.lower())
        return other_files

    # ------------------------------------------------------------------ #
    # File helpers
    # ------------------------------------------------------------------ #
    def load_file_struct(self, file_path: Path | str | None) -> str | None:
        """
        Load a file using `loadFile` and return its structural representation.
        """
        if not file_path:
            return None
        try:
            content = loadFile(Path(file_path))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load %s: %s", file_path, exc)
            return None
        return content.display_struct()

    # ------------------------------------------------------------------ #
    # Small helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_dct_h5(name: str) -> bool:
        lowered = name.lower()
        return lowered.endswith(".h5") and ("dct" in lowered or "_dataset" in lowered)


def unique_suffixes(files: Sequence[FileInfo]) -> list[str]:
    """Return sorted unique suffixes from a sequence of FileInfo objects."""
    suffixes = {file.suffix for file in files if file.suffix}
    return sorted(suffixes)
