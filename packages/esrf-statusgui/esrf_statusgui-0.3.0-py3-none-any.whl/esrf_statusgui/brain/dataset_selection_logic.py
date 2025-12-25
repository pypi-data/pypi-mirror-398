from __future__ import annotations

import logging
import os
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path as SystemPath
from typing import Any

from esrf_pathlib import ESRFPath as Path

from esrf_statusgui.brain.structure import Dataset, SampleManager
from esrf_statusgui.file_utils.file_utils import path_is_root_of
from esrf_statusgui.file_utils.fileNode import FileNode

logger = logging.getLogger(__name__)

RAW_DIR: str = "RAW_DATA"
PROC_DIR: str = "PROCESSED_DATA"


def is_date(string: str, date_format: str = "%Y%m%d") -> datetime | None:
    """
    Return a datetime if the given string matches `date_format`, else None.
    """
    try:
        return datetime.strptime(string, date_format)
    except ValueError:
        return None


class DatasetSelectionLogic:
    """
    Encapsulates filesystem and status-retrieval logic for the DatasetSelectionTab UI.
    """

    def __init__(
        self,
        base_path: Path | str,
        method_factories: Mapping[str, Callable[[Path], Any]],
    ) -> None:
        self.base_path: Path = Path(base_path)
        self.method_factories: dict[str, Callable[[Path], Any]] = {
            name: factory for name, factory in method_factories.items()
        }

        self.samples: SampleManager = SampleManager()
        self.cache: FileNode | None = None
        self.cache_folder: Path | None = None
        self.expe_folder: Path | None = None
        self.root_folder: Path | None = None

    def set_base_path(self, base_path: Path | str) -> Path:
        """
        Update the root under which experiments are discovered.

        Clears cached state so the caller can rebuild the UI with the new root.
        """
        new_base = Path(os.path.expanduser(str(base_path)))
        if not new_base.exists():
            raise FileNotFoundError(f"Base path not found: {new_base}")
        if not new_base.is_dir():
            raise NotADirectoryError(f"Base path is not a directory: {new_base}")

        self.base_path = new_base.resolve()
        self.cache = None
        self.cache_folder = None
        self.expe_folder = None
        self.root_folder = None
        self.samples = SampleManager()
        return self.base_path

    # ------------------------------------------------------------------ #
    # Discovery helpers
    # ------------------------------------------------------------------ #
    def list_experiments(self) -> list[str]:
        if not os.path.isdir(self.base_path):
            return []

        try:
            with os.scandir(self.base_path) as entries:
                return sorted(
                    [
                        entry.name
                        for entry in entries
                        if entry.is_dir() and not entry.name.startswith(".")
                    ]
                )
        except OSError as exc:
            logger.warning("Cannot list experiments in %s: %s", self.base_path, exc)
            return []

    def list_beamlines(self, experiment: str) -> list[str]:
        experiment = experiment.strip()
        if not experiment:
            return []

        path = self.base_path / experiment
        if not os.path.isdir(path):
            msg = f"Experiment folder not found: {path}"
            logger.debug(msg)
            raise FileNotFoundError(msg)

        try:
            with os.scandir(path) as entries:
                return sorted(
                    [
                        entry.name
                        for entry in entries
                        if entry.is_dir() and not entry.name.startswith(".")
                    ]
                )
        except OSError as exc:
            msg = f"Cannot list beamlines in {path}: {exc}"
            logger.warning(msg)
            raise

    # ------------------------------------------------------------------ #
    # Experiment selection and tree building
    # ------------------------------------------------------------------ #
    def select_experiment(self, experiment: str, beamline: str) -> Path:
        experiment = experiment.strip()
        beamline = beamline.strip()
        if not experiment or not beamline:
            raise ValueError("Experiment and beamline must be provided.")

        folder = self.base_path / experiment / beamline
        if not os.path.isdir(folder):
            msg = f"Beamline folder not found: {folder}"
            logger.debug(msg)
            raise FileNotFoundError(msg)

        self.expe_folder = folder
        self.root_folder = self._resolve_default_root(folder)
        if self.root_folder is None:
            raise ValueError(f"No valid date folder in {folder}")

        self.build_structure()
        return self.root_folder

    def _resolve_default_root(self, expe_folder: Path) -> Path | None:
        try:
            with os.scandir(expe_folder) as entries:
                date_folders = [
                    entry.name
                    for entry in entries
                    if entry.is_dir() and not entry.name.startswith(".")
                ]
        except OSError as exc:
            logger.warning("Cannot list dates in %s: %s", expe_folder, exc)
            return None

        dates = [dt for name in date_folders for dt in [is_date(name)] if dt]
        if not dates:
            return None

        return Path(expe_folder) / min(dates).strftime("%Y%m%d") / RAW_DIR

    def _find_section_root(self, start: Path | str) -> Path | None:
        """
        Walk upwards from ``start`` until a folder containing RAW/PROC sections is found.
        """
        current = SystemPath(os.fspath(start))
        while True:
            if (current / RAW_DIR).exists() or (current / PROC_DIR).exists():
                return Path(current)
            if current.parent == current:
                return None
            current = current.parent

    def select_manual_root(self, manual_root: Path | str) -> Path:
        """
        Use a user-provided path as the navigation root, skipping experiment/beamline selection.

        The path must live under a folder that contains RAW_DATA or PROCESSED_DATA.
        """
        target = Path(manual_root).expanduser()
        target_fs = os.fspath(target)
        if not os.path.exists(target_fs):
            raise FileNotFoundError(f"Manual root not found: {target}")
        if not os.path.isdir(target_fs):
            raise NotADirectoryError(f"Manual root is not a directory: {target}")

        section_root = self._find_section_root(target)
        if section_root is None:
            raise ValueError(
                f"Cannot find {RAW_DIR} or {PROC_DIR} above {target}. "
                "Enter a path inside a visit that contains RAW_DATA/PROCESSED_DATA."
            )

        self.expe_folder = section_root
        self.root_folder = target
        self.samples = SampleManager()
        self.build_structure()
        return self.root_folder

    def build_structure(self) -> FileNode:
        if self.expe_folder is None:
            raise ValueError("Experiment folder not selected.")

        self.cache = FileNode(self.expe_folder, True)
        self.cache_folder = self.expe_folder
        self.samples = SampleManager()

        if self.cache.children:
            for child in self.cache.children:
                child.children_cached = True
                child.update_children()

        for section in (RAW_DIR, PROC_DIR):
            nodes: list[FileNode] | None = (
                self.cache.find_by_name(section) if self.cache else None
            )
            if not nodes:
                continue
            for dpath in nodes:
                dpath.children_cached = True
                for entry in os.scandir(dpath.path):
                    if entry.name.startswith(".") or not entry.is_dir():
                        continue
                    if not any(
                        child.name == entry.name for child in dpath.children or []
                    ):
                        dpath.add_child(FileNode(entry.path, True, True))
                    else:
                        sample = dpath.find_by_name(entry.name)
                        if len(sample) == 1:
                            sample[0].children_cached = True
                            sample[0].update_children()
                        else:
                            logger.warning(
                                "Multiple sample nodes found for %s under %s",
                                entry.name,
                                dpath.path,
                            )
                            continue
                    sample = self.samples.create_sample(entry.name, entry.path, section)
                    node = self.cache.find_by_path(entry.path)
                    if node:
                        for child in node.children or []:
                            sample.add_dataset(child.name)
                    else:
                        logger.warning(
                            "Cache node missing for sample %s at %s",
                            entry.name,
                            entry.path,
                        )

        for method_name, method_factory in self.method_factories.items():
            for dataset in self.samples.get_datasets_by_method(method_name):
                if dataset.method is None or dataset.sample.processed_path is None:
                    continue

                if dataset.processing_state is None:
                    dataset.processing_state = []

                for processed_path in dataset.sample.processed_path or []:
                    dataset_folder = Path(processed_path) / dataset.dataset
                    if not dataset_folder.exists():
                        continue
                    status_obj = method_factory(dataset_folder)
                    try:
                        if hasattr(status_obj, "loadStatusFiles"):
                            status_obj.loadStatusFiles()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "loadStatusFiles failed for %s: %s", dataset_folder, exc
                        )
                    dataset.processing_state.append(status_obj)

        return self.cache

    # ------------------------------------------------------------------ #
    # Navigation helpers
    # ------------------------------------------------------------------ #
    def ensure_node(self, path: Path | str) -> FileNode | None:
        if self.cache is None:
            return None

        target = Path(path)
        node = self.cache.find_by_path(target)
        if node:
            if node.children is not None and not node.children_cached:
                node.update_children()
            return node

        current_path = target
        while current_path != current_path.parent:
            parent = self.cache.find_by_path(current_path.parent)
            if parent and parent.children is not None:
                parent.update_children()
                node = self.cache.find_by_path(target)
                if node:
                    if node.children is not None and not node.children_cached:
                        node.update_children()
                    return node
            current_path = current_path.parent

        return self.cache.find_by_path(target)

    def datasets_by_path(self, path: Path | str) -> dict[str, list[Dataset]]:
        folder = Path(path)
        datasets = self.samples.get_datasets_by_path(folder)
        grouped: dict[str, list[Dataset]] = {name: [] for name in self.method_factories}
        for dataset in datasets:
            if isinstance(dataset.method, str) and dataset.method in grouped:
                grouped[dataset.method].append(dataset)
        return grouped

    # ------------------------------------------------------------------ #
    # Mutation helpers
    # ------------------------------------------------------------------ #
    def refresh(self, target_folder: Path | str | None = None) -> FileNode | None:
        if target_folder is not None:
            self.root_folder = Path(target_folder)

        if self.root_folder is None:
            return None

        if self.root_folder.is_file():
            self.root_folder = self.root_folder.parent

        rebuild = False
        if self.cache is None or self.cache_folder is None:
            rebuild = True
        elif not path_is_root_of(self.cache_folder, self.root_folder):
            rebuild = True

        if rebuild:
            self.build_structure()

        return self.ensure_node(self.root_folder)

    def refresh_dataset(
        self,
        dataset: Dataset,
        method_factory: Callable[[Path], Any] | None = None,
    ) -> None:
        if method_factory is None:
            method_name = getattr(dataset, "method", None)
            if isinstance(method_name, str):
                method_factory = self.method_factories.get(method_name)

        dataset.processing_state = []

        if (
            method_factory is None
            or getattr(dataset, "sample", None) is None
            or getattr(dataset.sample, "processed_path", None) is None
        ):
            return

        for processed_path in dataset.sample.processed_path or []:
            dataset_folder = Path(processed_path) / dataset.dataset
            if not dataset_folder.exists():
                continue
            status_obj = method_factory(dataset_folder)
            try:
                if hasattr(status_obj, "loadStatusFiles"):
                    status_obj.loadStatusFiles()
                if hasattr(status_obj, "loadStatusDetailed"):
                    status_obj.loadStatusDetailed()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Status load failed for %s: %s", dataset_folder, exc)
            dataset.processing_state.append(status_obj)
