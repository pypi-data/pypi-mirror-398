from __future__ import annotations

import importlib.util
import logging
import os
import shutil
from collections.abc import Iterable, Sized
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

import ipywidgets as widgets
from esrf_pathlib import ESRFPath as Path
from IPython.display import display

from esrf_statusgui.brain.source_experiment import gtMoveData
from esrf_statusgui.data_managment.dct_parameter import dct_parameter
from esrf_statusgui.exp_methods.dct_status import dct_status
from esrf_statusgui.exp_methods.ff_status import ff_status
from esrf_statusgui.exp_methods.s3DXRD_status import s3DXRD_status
from esrf_statusgui.exp_methods.tomography_status import tomography_status
from esrf_statusgui.file_utils.createProcessingNotebook import (
    create_processing_nb_DCT,
    create_processing_nb_FF,
    create_processing_nb_SFF,
)
from esrf_statusgui.file_utils.file_utils import create_DCT_directories, is_date
from esrf_statusgui.file_utils.fileNode import FileNode
from esrf_statusgui.file_utils.FolderPermissionChecker import FolderPermissionChecker
from esrf_statusgui.file_utils.newExperimentDate import newExperimentDate
from esrf_statusgui.file_utils.paths import get_visitor_root

# ---- External deps from StatusGUI ----
from esrf_statusgui.visualization.DCT.pySetupH5 import pySetupH5

logger = logging.getLogger(__name__)


# ---------------------------- helpers & types ---------------------------- #
def _safe_len(obj: Sized | None) -> int:
    if obj is None:
        return 0
    try:
        return len(obj)
    except Exception:
        return 0


def _html(msg: str, kind: str = "info") -> widgets.HTML:
    """Small styled HTML message for the output cell."""
    palette = {
        "info": "#0b6efd",
        "warn": "#f59e0b",
        "error": "#dc2626",
        "ok": "#059669",
        "muted": "#6b7280",
    }
    color = palette.get(kind, "#0b6efd")
    return widgets.HTML(f'<div style="color:{color};font-family:monospace">{msg}</div>')


def _try_import_from_path(
    py_path: Path, module_attr_path: str, *, log_prefix: str
) -> Any | None:
    """
    Try to import a module from an explicit file path and then resolve an attribute path from it.
    module_attr_path: e.g. "imageD11.get_code_path"
    """
    try:
        spec = importlib.util.spec_from_file_location(py_path.stem, str(py_path))
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        loader = spec.loader
        if loader is None:
            return None
        loader.exec_module(module)
        obj: Any = module
        for part in module_attr_path.split("."):
            obj = getattr(obj, part)
        return obj
    except Exception as exc:
        logger.debug("%s: import from path failed (%s)", log_prefix, exc, exc_info=True)
        return None


def _first_parent_with_name(path: Path, name: str) -> Path | None:
    for p in (path, *path.parents):
        if p.name == name:
            return p
    return None


def _closest_parent_date_dir(path: Path) -> Path | None:
    """Return the nearest ancestor whose name is a YYYYMMDD date folder."""
    for p in (path, *path.parents):
        is_candidate = False
        try:
            is_candidate = is_date(p.name)
        except Exception:
            logger.debug("Failed to evaluate date folder for %s", p, exc_info=True)
        if is_candidate:
            return p
    return None


@dataclass
class _DatasetView:
    """Lightweight, defensive view of the dataset object."""

    method: str
    dataset: FileNode | str
    sample_raw_root: Path
    processing_state: list[Any]

    @classmethod
    def from_obj(cls, dataset: FileNode | str) -> _DatasetView:
        # method
        method = getattr(dataset, "method", None)
        if not isinstance(method, str):
            raise ValueError("dataset.method must be a string")

        # dataset name
        dset_name = getattr(dataset, "dataset", None)
        if not isinstance(dset_name, str) or not dset_name:
            raise ValueError("dataset.dataset must be a non-empty string")

        # raw path root
        sample = getattr(dataset, "sample", None)
        if sample is None:
            raise ValueError("dataset.sample is missing")
        raw_path = getattr(sample, "raw_path", None)
        if not raw_path or not isinstance(raw_path, (list, tuple)):
            raise ValueError("dataset.sample.raw_path must be a non-empty list")
        try:
            raw_root = Path(raw_path[0]).resolve()
        except Exception as exc:
            raise ValueError(f"raw_path[0] is not a valid path: {exc}") from exc

        # processing_state (normalize to list)
        ps = getattr(dataset, "processing_state", None)
        ps_list: list[Any] = []
        if ps is None:
            ps_list = []
        elif isinstance(ps, list):
            ps_list = ps
        else:
            # Some callers use tuple/other iterables
            try:
                ps_list = list(cast(Iterable[Any], ps))
            except Exception:
                ps_list = []

        return cls(
            method=method,
            dataset=dset_name,
            sample_raw_root=raw_root,
            processing_state=ps_list,
        )


# ----------------------------- main widget ------------------------------ #


class Post_process:
    """
    Refactored & hardened ipywidgets entry point to kick off post-processing flows
    from the Status GUI.
    """

    def __init__(self, dataset: FileNode) -> None:
        self._dataset_raw: FileNode = dataset
        self.ds = _DatasetView.from_obj(dataset)

        # h5 path for DCT selection widget
        self.path: Path = (
            self.ds.sample_raw_root / self.ds.dataset / f"{self.ds.dataset}.h5"
        )

        # UI state
        self.widget_loaded: bool = False
        self.fresh_restart: bool = (
            True  # True -> start from scratch; False -> reuse latest
        )
        self.widget: list[widgets.Widget] = []
        self.processed_output = widgets.Output()
        self.processed_button = widgets.Button(description="New post-treatment")
        self._confirmation_dialog: widgets.VBox | None = None

        self.create_widget()

    # --------------------------- widget surface --------------------------- #

    def create_widget(self) -> None:
        """(Re)build the visible panel and hook up events."""
        self.widget_loaded = True

        message = (
            "Create new processing based on an old one."
            if _safe_len(self.ds.processing_state) > 0
            else "Dataset not present in the PROCESSED_DATA folder."
        )

        panel = widgets.VBox(
            children=[
                widgets.HBox(children=[widgets.HTML(message), self.processed_button]),
                self.processed_output,
            ]
        )
        self.widget = [panel]
        self.processed_button.on_click(self.on_button_clicked)

    def export_widget(self) -> list[widgets.Widget]:
        if not self.widget_loaded:
            self.create_widget()
        return self.widget

    # ---------------------------- event logic ---------------------------- #

    def on_button_clicked(self, _btn: widgets.Button) -> None:
        """Main entry point from the button."""
        self.processed_button.disabled = True
        with self.processed_output:
            self.processed_output.clear_output()

        try:
            method = (self.ds.method or "").strip()
            if method == "DCT":
                if _safe_len(self.ds.processing_state) > 0:
                    self.show_confirmation_dialog()
                else:
                    self.post_DCT()
                if "/data/visitor" in str(self.path):
                    st = dct_status(self._get_latest_date_path(self.path))
                else:
                    st = dct_status(
                        str(self.ds.sample_raw_root).replace(
                            "RAW_DATA", "PROCESSED_DATA"
                        )
                    )

            elif method == "PCT":
                with self.processed_output:
                    display(
                        _html(
                            "Follow the tutorial: "
                            "https://confluence.esrf.fr/display/ID11KB/Reconstruction+using+Nabu+and+tomwer",
                            kind="muted",
                        )
                    )
                if "/data/visitor" in str(self.path):
                    st = tomography_status(self._get_latest_date_path(self.path))
                else:
                    st = tomography_status(
                        str(self.ds.sample_raw_root).replace(
                            "RAW_DATA", "PROCESSED_DATA"
                        )
                    )
            elif method == "FF":
                self.post_FF()
                if "/data/visitor" in str(self.path):
                    st = ff_status(self._get_latest_date_path(self.path))
                else:
                    st = ff_status(
                        str(self.ds.sample_raw_root).replace(
                            "RAW_DATA", "PROCESSED_DATA"
                        )
                    )
            elif method == "s3DXRD":
                self.post_SFF()
                if "/data/visitor" in str(self.path):
                    st = s3DXRD_status(self._get_latest_date_path(self.path))
                else:
                    st = s3DXRD_status(
                        str(self.ds.sample_raw_root).replace(
                            "RAW_DATA", "PROCESSED_DATA"
                        )
                    )
            else:
                with self.processed_output:
                    display(_html(f"Unsupported method: {method!r}", kind="error"))
                logger.warning("Unsupported dataset.method=%s", method)
                st = None

            if st is not None:
                if _safe_len(getattr(st, "components", None)) > 0:
                    st.loadStatusFiles()
                    self._dataset_raw.processing_state.append(st)

        finally:
            self.processed_button.disabled = False

    # -------------------------- processing flows ------------------------- #

    def post_DCT(self) -> None:
        """
        DCT flow.
        - If fresh_restart is True: show the pySetupH5 widget preconfigured.
        - Else: clone/move data from latest day into a new processed directory and
            prepare notebooks/parameters.
        """
        if self.fresh_restart:
            self._start_dct_from_scratch()
            return

        # Reuse latest processing base
        try:
            # Find raw_dir from first processing state item if present
            raw_dir: Path
            if _safe_len(self.ds.processing_state) > 0 and hasattr(
                self.ds.processing_state[0], "main_path"
            ):
                raw_dir = Path(self.ds.processing_state[0].main_path).resolve()
            else:
                # Fallback: derive from dataset.h5 parent
                raw_dir = self.path.parent.resolve()

            acquisition_dir = self._get_latest_date_path(raw_dir=raw_dir)
            create_DCT_directories(acquisition_dir, acquisition_dir.name)

            with self.processed_output:
                display(
                    _html(f"Copy/link latest data into: {acquisition_dir}", kind="info")
                )
            gtMoveData(raw_dir, acquisition_dir, self.processed_output)

            # Update parameters if legacy MAT exists; else ensure parameters.h5 path
            if (acquisition_dir / "parameters.mat").exists():
                with self.processed_output:
                    display(
                        _html(
                            "Modifying parameters.mat in the new date folder…",
                            kind="muted",
                        )
                    )
                self._update_mat_parameters(raw_dir, acquisition_dir)
                try:
                    parameters = dct_parameter(acquisition_dir / "parameters.h5")
                    create_processing_nb_DCT(
                        parameters.acq.dir(), parameters.acq.name()
                    )
                except Exception as exc:
                    logger.error("Failed creating DCT notebook: %s", exc, exc_info=True)
                    with self.processed_output:
                        display(_html("Failed to create DCT notebook.", kind="error"))
            else:
                logger.info(
                    "Dataset too old for automatic migration (no parameters.mat). Cleaning up."
                )
                with self.processed_output:
                    display(
                        _html(
                            "Dataset too old for auto-migration; starting from scratch is recommended.",
                            kind="warn",
                        )
                    )
                try:
                    if acquisition_dir.exists() and acquisition_dir.is_dir():
                        shutil.rmtree(acquisition_dir)
                except Exception:
                    logger.debug("Cleanup of %s failed", acquisition_dir, exc_info=True)

            # Final user message
            with self.processed_output:
                self.processed_output.clear_output(wait=True)
                display(
                    _html(
                        "Processing folder created. Check the notebook in the dataset folder.",
                        kind="ok",
                    )
                )

        except Exception as exc:
            logger.error("post_DCT failed: %s", exc, exc_info=True)
            with self.processed_output:
                display(_html(f"DCT flow failed: {exc}", kind="error"))

    def _start_dct_from_scratch(self) -> None:
        """Show/setup pySetupH5 with sensible defaults and hide unrelated tabs."""
        try:
            widget = pySetupH5()
        except Exception as exc:
            logger.error("pySetupH5 init failed: %s", exc, exc_info=True)
            with self.processed_output:
                display(_html(f"Could not initialize pySetupH5: {exc}", kind="error"))
            return

        with self.processed_output:
            self.processed_output.clear_output(wait=True)
            display(widget.display())

        # Preselect h5 file
        try:
            if self.path.exists():
                widget.dataset_selection_tab.selected_file = self.path
                widget.dataset_selection_tab.selected_file_path.value = (
                    f"The selected file is: {self.path}"
                )
        except Exception:
            logger.debug("Could not set selected_file to %s", self.path, exc_info=True)

        # If path includes visitor root, prefill experiment; otherwise prime manual RAW path
        manual_root_required = False
        raw_root_exists = self.ds.sample_raw_root.exists()
        if "/data/visitor" in str(get_visitor_root()):
            widget.parameters.internal.experiment = self.path.proposal
        else:
            manual_root_required = True
            if raw_root_exists:
                self._prefill_pysetup_manual_root(widget)
            else:
                with self.processed_output:
                    display(
                        _html(
                            f"RAW_DATA root not found: {self.ds.sample_raw_root}. "
                            "Use the Welcome tab to set it manually.",
                            kind="warn",
                        )
                    )
                manual_root_required = True

        # Show only the parameters/run tabs
        try:
            widget.tabs.selected_index = 2
            if len(widget.tabs.children) >= 2 and not manual_root_required:
                widget.tabs.children[0].layout.display = "none"
                widget.tabs.children[1].layout.display = "none"
            widget.parameters_tab.refresh()
        except Exception:
            logger.debug("pySetupH5 cosmetic adjustments failed", exc_info=True)

    def _prefill_pysetup_manual_root(self, widget: pySetupH5) -> bool:
        """Prefill pySetupH5 with a manual RAW_DATA root when visitor root is unavailable."""
        raw_root = self.ds.sample_raw_root
        try:
            if not raw_root.exists():
                with self.processed_output:
                    display(
                        _html(
                            f"RAW_DATA root not found: {raw_root}. Please set it manually.",
                            kind="warn",
                        )
                    )
                return False
        except Exception:
            logger.debug(
                "Could not verify RAW_DATA root at %s", raw_root, exc_info=True
            )
            return False

        try:
            widget.welcome_tab.manual_root_input.value = str(raw_root)
            widget.welcome_tab.on_manual_root_submit()
            widget.on_manual_root_chosen()
            if self.path.exists():
                widget.dataset_selection_tab.selected_file = self.path
                widget.dataset_selection_tab.selected_file_path.value = (
                    f"The selected file is: {self.path}"
                )
            return True
        except Exception:
            logger.debug("Could not prefill manual path for pySetupH5", exc_info=True)
            return False

    def post_FF(self) -> None:
        """Fast-Fourier (FF) flow."""
        try:
            processed_path = self._get_latest_date_path()

            create_processing_nb_FF(
                self.ds.sample_raw_root.parent,
                processed_path,
                getattr(self._dataset_raw.sample, "sample", self.ds.dataset),
                self.ds.dataset,
            )

            with self.processed_output:
                display(_html(f"FF notebooks created in: {processed_path}", kind="ok"))

        except Exception as exc:
            logger.error("post_FF failed: %s", exc, exc_info=True)
            with self.processed_output:
                display(_html(f"FF flow failed: {exc}", kind="error"))

    def post_SFF(self) -> None:
        """Sparse 3DXRD (SFF) flow."""
        try:
            processed_path = self._get_latest_date_path()

            create_processing_nb_SFF(
                self.ds.sample_raw_root.parent,
                processed_path,
                getattr(self._dataset_raw.sample, "sample", self.ds.dataset),
                self.ds.dataset,
            )
            with self.processed_output:
                display(_html(f"SFF notebooks created in: {processed_path}", kind="ok"))

        except Exception as exc:
            logger.error("post_SFF failed: %s", exc, exc_info=True)
            with self.processed_output:
                display(_html(f"SFF flow failed: {exc}", kind="error"))

    # --------------------------- date/path logic -------------------------- #
    def _get_latest_date_path(self, raw_dir: Path | None = None) -> Path:
        """
        Determine a safe target PROCESSED_DATA directory for the dataset using esrf-pathlib fields.

        Strategy:
            - Identify the nearest date folder (YYYYMMDD) above the raw_dir (or dataset path).
            - Among sibling date folders at the same level, choose the latest date.
            - If the chosen PROCESSED_DATA/<dataset_rel> is not writable OR already has
                parameters.h5, pick today's date; if it collides, choose next day.
            - Ensure the date skeleton exists (newExperimentDate) and return the final path.
        """
        raw_dir = (raw_dir or self.path.parent).resolve()
        if raw_dir.suffix == ".h5":
            raw_dir = raw_dir.parent

        # Locate anchor date dir and RAW_DATA root to build dataset-relative path
        date_dir = _closest_parent_date_dir(raw_dir)
        if date_dir is None:
            # Fallback: use today's date under the closest parent we can write into
            today = datetime.now().strftime("%Y%m%d")
            base = raw_dir.parents[0] if len(raw_dir.parents) else raw_dir
            target = base / today / "PROCESSED_DATA" / raw_dir.name
            return self._ensure_acquisition_dir(target)

        # Prefer RAW_DATA as anchor if present under the date dir
        raw_root = _first_parent_with_name(raw_dir, "RAW_DATA")
        base_anchor = (
            raw_root if raw_root and date_dir in raw_root.parents else date_dir
        )

        # Compute dataset relative path under anchor
        try:
            dataset_rel = raw_dir.relative_to(base_anchor)
        except Exception:
            # Best effort fallback: relative to date_dir, drop the first segment (RAW_DATA)
            try:
                tmp_rel = raw_dir.relative_to(date_dir)
                parts = tmp_rel.parts[1:] if len(tmp_rel.parts) >= 1 else tmp_rel.parts
                dataset_rel = Path(*parts) if parts else Path(raw_dir.name)
            except Exception:
                dataset_rel = Path(raw_dir.name)

        # Consider latest sibling date at the same level as date_dir
        parent = date_dir.parent
        dates: list[datetime] = []
        try:
            with os.scandir(parent) as entries:
                for child in entries:
                    if child.is_dir():
                        dt = is_date(child.name)
                        if dt:
                            dates.append(dt)
        except Exception:
            logger.debug("Listing sibling dates failed for %s", parent, exc_info=True)

        chosen_date_str = (max(dates).strftime("%Y%m%d")) if dates else date_dir.name
        acquisition_dir = parent / chosen_date_str / "PROCESSED_DATA" / dataset_rel

        # Permission/occupied checks
        try:
            pd_root = parent / chosen_date_str / "PROCESSED_DATA"
            writable = FolderPermissionChecker(pd_root).checkWritePermission()
        except Exception:
            writable = os.access(
                pd_root if "pd_root" in locals() else acquisition_dir.parent, os.W_OK
            )

        occupied = (acquisition_dir / "parameters.h5").exists()

        if not writable or occupied:
            # Try today; if today == chosen_date_str, move to next day after latest date.
            today_str = datetime.now().strftime("%Y%m%d")
            if today_str == chosen_date_str:
                next_day = (
                    (max(dates) + timedelta(days=1)).strftime("%Y%m%d")
                    if dates
                    else today_str
                )
                target = parent / next_day / "PROCESSED_DATA" / dataset_rel
            else:
                target = parent / today_str / "PROCESSED_DATA" / dataset_rel
            return self._ensure_acquisition_dir(target)

        # Normal path
        return self._ensure_acquisition_dir(acquisition_dir)

    def _ensure_acquisition_dir(self, acquisition_dir: Path) -> Path:
        """Ensure the date skeleton exists; fallback to RAW->PROCESSED mirror if needed."""
        try:
            date_root = acquisition_dir.parents[
                2
            ]  # .../<YYYYMMDD>/PROCESSED_DATA/<dataset_rel>
            if not date_root.exists():
                # Create the date skeleton (beamline-friendly)
                newExperimentDate(date_root, True)
            logger.info(
                "Creating directory %s (parents=True, exist_ok=True)", acquisition_dir
            )
            acquisition_dir.mkdir(parents=True, exist_ok=True)
            return acquisition_dir
        except Exception as exc:
            logger.debug(
                "Creating acquisition_dir %s failed (%s). Trying RAW->PROCESSED mirror.",
                acquisition_dir,
                exc,
                exc_info=True,
            )
            # Fallback: mirror RAW_DATA -> PROCESSED_DATA path if present
            try:
                alt = Path(str(acquisition_dir).replace("RAW_DATA", "PROCESSED_DATA"))
                logger.info("Creating directory %s (parents=True, exist_ok=True)", alt)
                alt.mkdir(parents=True, exist_ok=True)
                return alt
            except Exception:
                # Last resort: parent of raw root
                parent = self.ds.sample_raw_root.parent
                final = parent / "PROCESSED_DATA" / self.ds.dataset
                logger.info(
                    "Creating directory %s (parents=True, exist_ok=True)", final
                )
                final.mkdir(parents=True, exist_ok=True)
                return final

    # --------------------------- external tools --------------------------- #

    def _update_mat_parameters(self, raw_dir: Path, acquisition_dir: Path) -> None:
        """
        Call dct_launch to update parameters when parameters.mat is present.
        Safe if dct module is not available.
        """
        try:
            import dct.dct_launch as dct_launch
        except Exception as exc:
            logger.warning(
                "dct_launch not available; skipping MAT->H5 update (%s).", exc
            )
            with self.processed_output:
                display(
                    _html(
                        "dct_launch not available; parameters.mat not updated.",
                        kind="warn",
                    )
                )
            return

        # Build MATLAB command
        try:
            cmd = [
                os.path.abspath(dct_launch.__file__),
                "matlab_script",
                "skip_functions_check",
                "--script",
                (
                    f"cd('{raw_dir.as_posix()}');"
                    f"p=gtLoadParameters;"
                    f"p.acq.dir='{acquisition_dir.as_posix()}';"
                    f"parameters.acq.name.value='{acquisition_dir.name}';"
                    f"parameters.acq.collection_dir.value='{(acquisition_dir / '0_rawdata/Orig').as_posix()}';"
                    f"gtSaveParameters(p);exit"
                ),
            ]
            launcher = dct_launch.DCTLauncher(cmd)
            launcher.run()
        except Exception as exc:
            logger.error(
                "Failed to update parameters via dct_launch: %s", exc, exc_info=True
            )
            with self.processed_output:
                display(
                    _html(
                        "Parameters update failed; you may need to adjust manually.",
                        kind="warn",
                    )
                )

    # --------------------------- confirmation UI -------------------------- #

    def show_confirmation_dialog(self) -> None:
        """Ask user whether to start from scratch or reuse the most recent experiment."""
        self.processed_output.clear_output()

        yes_btn = widgets.Button(description="Yes", button_style="success")
        no_btn = widgets.Button(description="No", button_style="danger")
        label = widgets.Label(
            "Do you want to start from scratch this pre-processing? "
            "(No will copy/link the most recent experiment)"
        )

        def on_yes(_btn: widgets.Button) -> None:
            self.fresh_restart = True
            self.post_DCT()

        def on_no(_btn: widgets.Button) -> None:
            self.fresh_restart = False
            self.post_DCT()

        yes_btn.on_click(on_yes)
        no_btn.on_click(on_no)

        self._confirmation_dialog = widgets.VBox(
            [label, widgets.HBox([yes_btn, no_btn])]
        )
        with self.processed_output:
            display(self._confirmation_dialog)
