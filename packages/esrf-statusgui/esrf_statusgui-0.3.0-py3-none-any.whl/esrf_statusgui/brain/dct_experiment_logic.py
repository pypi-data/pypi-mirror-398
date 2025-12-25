from __future__ import annotations

import logging
import os
from collections.abc import Iterable

from esrf_pathlib import ESRFPath as Path

logger = logging.getLogger(__name__)


class DCTExperimentSelectionLogic:
    """
    Provides filesystem-backed helpers for listing experiments, beamlines,
    and experiment dates for the DCT workflow.
    """

    def __init__(self, base_path: Path | str) -> None:
        self.base_path: Path = Path(base_path)

    # ------------------------------------------------------------------ #
    # Listing helpers
    # ------------------------------------------------------------------ #
    def list_experiments(self, seed: Iterable[str] | None = None) -> list[str]:
        experiments = set(seed or [])
        if not os.path.isdir(self.base_path):
            return sorted(experiments)

        try:
            with os.scandir(self.base_path) as entries:
                for entry in entries:
                    if entry.is_dir() and not entry.name.startswith("."):
                        experiments.add(entry.name)
        except OSError as exc:
            logger.warning("Cannot list experiments in %s: %s", self.base_path, exc)
        return sorted(experiments)

    def list_beamlines(self, experiment: str) -> list[str]:
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
            logger.warning("Cannot list beamlines in %s: %s", path, exc)
            raise

    def list_dates(self, experiment: str, beamline: str) -> list[str]:
        path = self.base_path / experiment / beamline
        if not os.path.isdir(path):
            msg = f"Beamline folder not found: {path}"
            logger.debug(msg)
            raise FileNotFoundError(msg)

        valid_dates: list[str] = []
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if not entry.is_dir() or entry.name.startswith("."):
                        continue
                    if self._contains_raw_data(entry.path):
                        valid_dates.append(entry.name)
        except OSError as exc:
            logger.warning("Cannot list dates in %s: %s", path, exc)
            raise

        valid_dates.sort()
        return valid_dates

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _contains_raw_data(date_folder: Path | str) -> bool:
        try:
            with os.scandir(date_folder) as entries:
                return any(
                    child.is_dir() and "RAW_DATA" in child.name for child in entries
                )
        except OSError:
            return False
