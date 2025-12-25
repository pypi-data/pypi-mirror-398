from __future__ import annotations

import logging
import os

from esrf_pathlib import ESRFPath as Path

logger = logging.getLogger(__name__)

PathLike = str | Path
RAW_DIR: str = "RAW_DATA"
PROC_DIR: str = "PROCESSED_DATA"


class FileNode:
    """
    Represents a node in a file tree structure, allowing for navigation
    and manipulation of the file system.

    Methods include searching by name/path, listing files/dirs, and add/remove.
    """

    def __init__(
        self,
        path: PathLike,
        cache_children: bool = False,
        is_sample: bool = False,
        is_dataset: bool = False,
        **kwargs,
    ):
        # Backward-compat for previous misspelled kwarg: cache_childen
        if "cache_childen" in kwargs:
            cache_children = bool(kwargs.pop("cache_childen"))

        p = Path(path)
        self.name: str = p.name
        self.path: str = str(p)
        self.is_sample: bool = is_sample
        self.is_dataset: bool = is_dataset
        self.is_file: bool = p.is_file()

        # Directories have a children list; files have None
        self.children: list[FileNode] | None = [] if p.is_dir() else None
        self.children_cached: bool = cache_children

        if cache_children and self.children is not None:
            self.update_children()

    # ---------- Tree building ----------

    def update_children(self) -> None:
        """Populate children with both subdirectories and files (skips hidden)."""
        if self.children is None:  # files cannot have children
            return
        try:
            with os.scandir(self.path) as it:
                for entry in it:
                    if entry.name.startswith("."):
                        continue
                    try:
                        ep = Path(entry.path)
                        is_sample = False
                        is_dataset = False
                        if self.name in (RAW_DIR, PROC_DIR):
                            # Under RAW_DATA or PROCESSED_DATA, mark dirs as samples
                            is_sample = True
                        elif self.is_sample:
                            is_dataset = True
                        # Build child as same class as self to preserve subclass behavior
                        child = type(self)(
                            ep,
                            cache_children=False,
                            is_sample=is_sample,
                            is_dataset=is_dataset,  # dataset if parent is a sample
                        )
                        self.add_child(child)
                    except Exception as e:  # noqa: BLE001
                        logger.debug("Skipping %s due to error: %s", entry.path, e)
        except (PermissionError, FileNotFoundError) as e:
            logger.warning("Cannot scan %s: %s", self.path, e)

    def add_child(self, child: FileNode) -> None:
        if self.children is None:
            logger.debug("Ignoring add_child on file node: %s", self.path)
            return
        # Skip hidden just in case
        if Path(child.path).name.startswith("."):
            return
        self.children.append(child)
        self.children.sort(key=lambda x: x.name.lower())

    # ---------- Find & list ----------

    def find_by_name(self, name: str) -> list[FileNode]:
        result: list[FileNode] = []
        if self.name == name:
            result.append(self)
        if self.children:
            for child in self.children:
                result.extend(child.find_by_name(name))
        return result

    def find_file_path(self, filename: str) -> Path | None:
        """Return the ESRFPath of the first file with given name."""
        if self.name == filename:
            return Path(self.path)
        if self.children:
            for child in self.children:
                result = child.find_file_path(filename)
                if result is not None:
                    return result
        return None

    def find_by_path(self, path: PathLike) -> FileNode | None:
        target = str(Path(path))
        if self.path == target:
            return self
        if self.children:
            for child in self.children:
                result = child.find_by_path(target)
                if result is not None:
                    return result
        return None

    def find_files_by_extension(
        self,
        extension: str | tuple[str, ...],
        keyword: str | None = "_dct",
    ) -> list[FileNode]:
        """
        Recursively find files with given extension(s) and optional keyword in the name.
        `extension` may be ".h5" or (".h5", ".nx") etc.
        """
        if isinstance(extension, str):
            exts = (extension if extension.startswith(".") else f".{extension}",)
        else:
            exts = tuple(e if e.startswith(".") else f".{e}" for e in extension)

        result: list[FileNode] = []
        name_ok = True if keyword is None else (keyword in self.name)
        if self.is_file and any(self.path.endswith(e) for e in exts) and name_ok:
            result.append(self)
        if self.children:
            for child in self.children:
                result.extend(child.find_files_by_extension(exts, keyword))
        return result

    def find_directories(self) -> list[FileNode]:
        result: list[FileNode] = []
        if not self.is_file:
            result.append(self)
        if self.children:
            for child in self.children:
                result.extend(child.find_directories())
        return result

    def list_all_files(self) -> list[FileNode]:
        result: list[FileNode] = []
        if self.is_file:
            result.append(self)
        if self.children:
            for child in self.children:
                result.extend(child.list_all_files())
        return result

    def list_all_directories(self) -> list[FileNode]:
        result: list[FileNode] = []
        if not self.is_file:
            result.append(self)
        if self.children:
            for child in self.children:
                result.extend(child.list_all_directories())
        return result

    # ---------- Mutations ----------

    def add_node(self, new_node: FileNode, parent_path: PathLike) -> None:
        parent_node = self.find_by_path(parent_path)
        if parent_node and not parent_node.is_file and parent_node.children is not None:
            parent_node.add_child(new_node)
        else:
            logger.warning(
                "Parent path '%s' not found or is not a directory", parent_path
            )

    def remove_node(self, target_path: PathLike) -> bool:
        target = str(Path(target_path))
        if self.path == target:
            logger.warning("Cannot remove the root node")
            return False
        if self.children:
            for i, child in enumerate(self.children):
                if child.path == target:
                    self.children.pop(i)
                    return True
                if child.remove_node(target):
                    return True
        return False

    # ---------- Repr ----------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FileNode(name={self.name!r}, path={self.path!r}, is_file={self.is_file}, "
            f"is_sample={self.is_sample}, is_dataset={self.is_dataset}, "
            f"children={len(self.children) if isinstance(self.children, list) else None})"
        )


class DCTNode(FileNode):
    def __init__(self, path: PathLike, **kwargs):
        p = Path(path)
        super().__init__(p, **kwargs)
        self.has_dct_h5: bool = (
            self.is_file
            and (p.suffix.lower() == ".h5")
            and ("dct" in self.name.lower())
        )

    def add_child(self, child: FileNode) -> None:
        super().add_child(child)
        self.has_dct_h5 |= bool(getattr(child, "has_dct_h5", False))

    def update_has_dct_h5_recursively(self) -> None:
        if self.children:
            for child in self.children:
                updater = getattr(child, "update_has_dct_h5_recursively", None)
                if callable(updater):
                    updater()
                self.has_dct_h5 |= bool(getattr(child, "has_dct_h5", False))


class ParameterNode(FileNode):
    def __init__(self, path: PathLike, **kwargs):
        p = Path(path)
        super().__init__(p, **kwargs)
        self.has_param_h5: bool = self.is_file and (p.name == "parameter.h5")

    def add_child(self, child: FileNode) -> None:
        super().add_child(child)
        self.has_param_h5 |= bool(getattr(child, "has_param_h5", False))

    def update_has_param_h5_recursively(self) -> None:
        if self.children:
            for child in self.children:
                updater = getattr(child, "update_has_param_h5_recursively", None)
                if callable(updater):
                    updater()
                self.has_param_h5 |= bool(getattr(child, "has_param_h5", False))
