from __future__ import annotations

import datetime as dt
import logging
import re
import time
from collections.abc import Iterable, Mapping, Sequence
from functools import partial
from typing import Any

import ipywidgets as widgets
import numpy as np
from IPython.display import display

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path
try:
    from esrf_loadFile import loadFile
except ImportError:
    from esrf_statusgui.data_managment.loadFile import loadFile

from esrf_statusgui.brain.dataset_selection_logic import DatasetSelectionLogic
from esrf_statusgui.brain.dataset_selection_logic import (
    is_date as _logic_is_date,
)
from esrf_statusgui.brain.post_process import Post_process, _safe_len
from esrf_statusgui.exp_methods.dct_status import dct_status
from esrf_statusgui.exp_methods.ff_status import ff_status
from esrf_statusgui.exp_methods.s3DXRD_status import s3DXRD_status
from esrf_statusgui.exp_methods.tomography_status import tomography_status
from esrf_statusgui.file_utils.fileNode import FileNode
from esrf_statusgui.file_utils.paths import (
    _safe_attr,
    get_visitor_root,
    set_visitor_root,
)
from esrf_statusgui.visualization.HDF5ImageViewer import HDF5ImageViewer

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
COLOR_NOT_PROCESSED: str = "red"
COLOR_BEING_PROCESSED: str = "orange"
COLOR_PROCESSED: str = "green"

LAYOUT_WIDTH_WINDOW: int = 100  # (%)

TraitChange = Mapping[str, Any]  # ipywidgets/traitlets change event payload


def _nkey(x: str) -> list[Any]:
    """
    Natural sort key: 'sam_2' < 'sam_10' by splitting digits and strings.
    """
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(x))]


def _as_children(
    items: Iterable[widgets.Widget] | widgets.Widget | None,
) -> tuple[widgets.Widget, ...]:
    """
    Normalize to a tuple[Widget, ...] suitable for `.children`. Also flattens
    a single level of nested lists/tuples that may come from external UIs.
    """
    if items is None:
        return tuple()
    if isinstance(items, widgets.Widget):
        return (items,)

    out: list[widgets.Widget] = []
    for it in items:
        if isinstance(it, widgets.Widget):
            out.append(it)
        elif isinstance(it, (list, tuple)):
            for inner in it:
                if isinstance(inner, widgets.Widget):
                    out.append(inner)
                else:
                    logger.warning(
                        "Ignoring non-widget in nested list: %r", type(inner)
                    )
        else:
            logger.warning("Ignoring non-widget in children: %r", type(it))
    return tuple(out)


def _safe_reobserve(
    widget: widgets.Widget,
    handler: Any,
    names: str | Iterable[str] | None,
) -> None:
    """
    Ensure `handler` observes the given trait names exactly once.

    ipywidgets 7/8 store observers in slightly different structures; we normalise
    things so tests relying on `_trait_notifiers` continue to work while still
    using the official `.observe()` API for actual notifications.
    """

    def _iter_names(value: str | Iterable[str] | None) -> tuple[str | None, ...]:
        if value is None:
            return (None,)
        if isinstance(value, str):
            return (value,)
        try:
            return tuple(value)
        except TypeError:
            return (value,)

    def _ensure_notifier(trait_name: str | None) -> None:
        key = "change" if trait_name is None else f"change:{trait_name}"
        dispatcher = widget._trait_notifiers.get(key)
        if dispatcher is None:
            try:
                from traitlets.traitlets import CallbackDispatcher
            except Exception:  # pragma: no cover - traitlets always available in tests
                widget._trait_notifiers[key] = [handler]
                return
            dispatcher = CallbackDispatcher()
            dispatcher.register_callback(handler)
            widget._trait_notifiers[key] = dispatcher
            return
        register = getattr(dispatcher, "register_callback", None)
        if callable(register):
            register(handler)
            return
        try:
            callbacks = dispatcher  # type: ignore[assignment]
            if handler not in callbacks:
                callbacks.append(handler)
        except Exception:
            widget._trait_notifiers[key] = [handler]

    for trait_name in _iter_names(names):
        kwargs = {} if trait_name is None else {"names": trait_name}
        try:
            widget.unobserve(handler, **kwargs)
        except Exception:
            logger.debug(
                "Failed to detach handler %s for %s", handler, trait_name, exc_info=True
            )
        widget.observe(handler, **kwargs)
        _ensure_notifier(trait_name)


def is_date(string: str, date_format: str = "%Y%m%d") -> dt.datetime | None:
    """
    Backwards-compatibility shim that re-exports the logic-layer helper.
    """
    return _logic_is_date(string, date_format=date_format)


# ------------------------------------------------------------------------------
# UI classes (public API unchanged)
# ------------------------------------------------------------------------------
class ExperimentColumn(widgets.VBox):
    """
    Represents a column in the UI for a specific experiment method.

    Attributes
    ----------
    name : str
        Name of the method (e.g. 'DCT', 'PCT', 'FF', 's3DXRD').
    method : Any
        Factory/class used to build a status object for a dataset path
        (e.g. dct_status(Path), tomography_status(Path), ...).
    checker : Any | None
        Placeholder for future validation/checking hooks.
    tree : list[Any] | None
        Datasets belonging to this method, at the current folder level.
    """

    def __init__(self, name: str, method: Any) -> None:
        super().__init__()
        self.name: str = name
        self.method: Any = method
        self.checker: Any | None = None
        self.tree: list[Any] | None = None


class ProcessedPathAccordeon(widgets.VBox):
    """
    Manages the UI components for displaying processed paths and their statuses.

    The constructor builds inner accordions based on the dataset's processing state.
    """

    def __init__(
        self,
        dataset: FileNode,
        controller: DatasetSelectionTab | None = None,
        method: Any | None = None,
    ) -> None:
        super().__init__()
        self.dataset: FileNode = dataset
        self.controller: DatasetSelectionTab | None = (
            controller  # NEW: to call refresh_dataset
        )
        self.method: Any | None = method  # NEW: factory for this dataset
        # Build once; children must be a tuple of Widgets (no lists inside)
        self.children = _as_children(self._build_accordion_datasets())

    # ---- public-ish helpers used during construction ----
    def post_process(self) -> widgets.Widget | Sequence[widgets.Widget]:
        """
        Return the post-process UI exported by Post_process(dataset).

        Notes
        -----
        - Post_process(...).export_widget() may return a Widget or a list/tuple of Widgets.
        - We wrap it with a small toolbar exposing a dataset-only refresh.
        """
        if getattr(self.dataset, "sample", None) and getattr(
            self.dataset.sample, "raw_path", None
        ):
            if getattr(self.dataset, "dataset", None):
                ui = Post_process(
                    self.dataset
                ).export_widget()  # Widget or list[Widget,...]

                # If we have a controller, add a one-click dataset refresh
                if self.controller is not None:
                    btn = widgets.Button(
                        description="Refresh dataset",
                        tooltip="Re-read status and refresh only this dataset",
                        button_style="",  # neutral
                    )

                    def _do_refresh(_=None):
                        try:
                            self.controller.refresh_dataset(self.dataset, self.method)
                            # Rebuild our inner accordions so latest status is displayed
                            self.children = _as_children(
                                self._build_accordion_datasets()
                            )
                        except Exception as e:
                            logger.warning("Dataset refresh failed: %s", e)

                    btn.on_click(_do_refresh)
                    bar = widgets.HBox([btn])
                    return widgets.VBox([bar, *_as_children(ui)])

                return ui
        return None

    @staticmethod
    def _get_iso_date(x) -> str:
        if isinstance(x, dt.datetime):
            return x.strftime("%Y%m%d")
        if isinstance(x, dt.date):
            return x.strftime("%Y%m%d")
        if isinstance(x, str):
            return x
        return "" if x is None else str(x)

    def _build_accordion_datasets(self) -> Sequence[widgets.Widget]:
        """
        Build first-level (per-date) accordions if processing_state exists.
        Otherwise, return the post-process UI only.
        """
        if not getattr(self.dataset, "processing_state", None):
            pp = self.post_process()
            return _as_children(pp)

        processed_date: list[Any] = [
            pt for pt in self.dataset.processing_state if hasattr(pt, "components")
        ]
        accordion_items: list[widgets.Widget] = [
            widgets.Accordion(children=(widgets.VBox(),)) for _ in processed_date
        ]
        titles: list[str | None] = [
            self._get_iso_date(_safe_attr(pt.main_path, "session_date"))
            for pt in processed_date
        ]
        if _safe_len(titles) == 0 or all(t is None or t == "" for t in titles):
            titles = [
                f"No date {i+1}" for i in range(len(accordion_items))
            ]  # Fallback titles

        for i, title in enumerate(titles):
            acc: widgets.Accordion = accordion_items[i]  # type: ignore[assignment]
            acc.set_title(0, title or "")
            _, color = self._get_component_status(processed_date[i])
            acc.layout.border = f"2px solid {color}"
            handler = partial(
                self._on_date_open,
                components=processed_date[i],
                accordion=acc,
                dataset=self.dataset,
            )
            _safe_reobserve(acc, handler, names="selected_index")

        # Append post-process area (flattened) if provided
        pp = self.post_process()
        if pp:
            accordion_items.extend(_as_children(pp))
        return accordion_items

    def _status_for(self, component: Any) -> tuple[str | None, str]:
        """
        Compute (status_text, color) for a given processing component.

        Rules kept identical to original behavior.
        """
        if getattr(component, "statusFilesLaunched", False):
            if getattr(component, "filesOk", False):
                return "\n".join(np.ravel(component.print_status())), COLOR_PROCESSED
            return "\n".join(np.ravel(component.print_errors())), COLOR_BEING_PROCESSED

        if getattr(component, "statusDetailedLaunched", False):
            if getattr(component, "detailedOk", False):
                return (
                    "\n".join(np.ravel(component.print_status_details())),
                    COLOR_PROCESSED,
                )
            return "\n".join(np.ravel(component.print_errors())), COLOR_BEING_PROCESSED

        return None, COLOR_NOT_PROCESSED

    # Backwards-compatible wrappers
    def _get_date_status(self, component: Any) -> tuple[str | None, str]:
        """
        Date-level representation: if being processed, omit the text in the summary.
        """
        status, color = self._status_for(component)
        if color == COLOR_BEING_PROCESSED and status:
            return None, color
        return status, color

    def _get_component_status(self, component: Any) -> tuple[str | None, str]:
        """
        Component-level status/color report.
        """
        return self._status_for(component)

    # ---- event handlers ----
    def _on_date_open(
        self,
        change: TraitChange,
        components: Any,
        accordion: widgets.Accordion,
        dataset: Any,
    ) -> None:
        """
        When a date-level accordion is opened, populate it with component-level accordions.
        """
        if change.get("name") != "selected_index":
            return
        # Build accordion for date components
        accordion.children = (
            widgets.VBox(children=self._create_accordion(components)),
        )
        _, color = self._get_component_status(components)
        accordion.layout.border = f"2px solid {color}"

    def _on_pt_step_open(
        self, change: TraitChange, components: Any, accordion: widgets.Accordion
    ) -> None:
        """
        When a component-level accordion is opened, show its preview/details.
        """
        if change.get("name") != "selected_index":
            return
        selected_index = change.get("new")
        if selected_index is None or selected_index == -1:
            return
        accordion.children = _as_children(self._create_pt_step_widget(components))
        _, color = self._get_component_status(components)
        accordion.layout.border = f"2px solid {color}"

    # ---- UI builders ----
    def _create_pt_step_widget(self, component: Any) -> widgets.Widget:
        """
        Create the visualization/status widget for a single processing component.
        """
        # Ensure details loaded before showing
        if hasattr(component, "loadStatusDetailed") and not getattr(
            component, "statusDetailedLaunched", False
        ):
            component.loadStatusDetailed()
        status, _ = self._get_component_status(component)
        if getattr(component, "visualize", False):
            try:
                return HDF5ImageViewer(component.target_files[0]).ui
            except Exception as e:
                logger.warning("Failed to build HDF5ImageViewer: %s", e)
        return widgets.HTML(value=status or "", layout=widgets.Layout(width="100%"))

    def _create_accordion(self, processing_state: Any) -> list[widgets.Accordion]:
        """
        Create one accordion per component under a given date group.
        """
        accs: list[widgets.Accordion] = [
            widgets.Accordion(children=(widgets.Output(),))
            for _ in processing_state.components
        ]
        for i, (component, _, component_name) in enumerate(processing_state.components):
            acc = accs[i]
            acc.set_title(0, component_name)
            _, color = self._get_component_status(component)
            acc.layout.border = f"2px solid {color}"
            handler = partial(
                self._on_pt_step_open, components=component, accordion=acc
            )
            _safe_reobserve(acc, handler, names="selected_index")
        return accs


class DatasetSelectionTab(widgets.VBox):
    """
    Main UI tab for dataset selection:
        - Experiment & beamline selectors
        - Folder tree + four method columns (PCT, DCT, FF, s3DXRD)
        - Breadcrumbs and content panel
    """

    def __init__(self) -> None:
        super().__init__()

        # ---- configuration / environment ----
        self.logic = DatasetSelectionLogic(
            base_path=get_visitor_root(),
            method_factories={
                "PCT": tomography_status,
                "s3DXRD": s3DXRD_status,
                "DCT": dct_status,
                "FF": ff_status,
            },
        )
        self.base_path: Path = self.logic.base_path
        self.exp_list: list[str] = self.logic.list_experiments()
        # NOTE: This `layout` is reused for method columns; your original behavior restored it on collapse.
        self.layout: widgets.Layout = widgets.Layout(
            width="auto", flex="1 1 auto", min_width="150px"
        )

        # ---- runtime state ----
        self.active_accordion: widgets.Accordion | None = None
        self.selected_file: Path | None = None
        self.active_button: widgets.Button | None = None
        self.dataset_to_widget: dict[Any, widgets.Accordion] = {}
        self._last_change_ts: float = 0.0  # debounce timestamp

        # ---- widgets ----
        self._init_widgets()
        self._init_layout()

        # ---- initial rendering ----
        self.create_tree_view()
        self.create_breadcrumbs()

    # ---- UI build ----
    def _init_widgets(self) -> None:
        """Create top-level widgets and wire observers."""
        self.tree: widgets.VBox = widgets.VBox()
        self.status_label: widgets.Label = widgets.Label(
            value="Ready", layout=widgets.Layout(width=f"{LAYOUT_WIDTH_WINDOW}%")
        )
        self.refresh_tree_btn: widgets.Button = widgets.Button(
            description="Refresh", layout=widgets.Layout(width="100px")
        )
        self.refresh_tree_btn.on_click(self.refresh_tree)
        self.custom_root: widgets.Text = widgets.Text(
            value=str(self.base_path),
            description="Data root:",
            placeholder="Path with proposal folders",
            layout=widgets.Layout(width="auto", flex="1 1 auto"),
        )
        self.custom_root.style = {"description_width": "100px"}
        self.custom_root_btn: widgets.Button = widgets.Button(
            description="Use path", layout=widgets.Layout(width="120px")
        )
        self.custom_root_btn.on_click(self.on_manual_root_submit)

        self.selected_file_path: widgets.Label = widgets.Label(
            value="", layout=widgets.Layout(width="auto")
        )
        self.file_content: widgets.VBox = widgets.VBox()
        self.breadcrumbs: widgets.HBox = widgets.HBox()

        # Method columns (containers + factories)
        method_factories = self.logic.method_factories
        self.tomo: ExperimentColumn = ExperimentColumn("PCT", method_factories["PCT"])
        self.s3d: ExperimentColumn = ExperimentColumn(
            "s3DXRD", method_factories["s3DXRD"]
        )
        self.dct: ExperimentColumn = ExperimentColumn("DCT", method_factories["DCT"])
        self.ff: ExperimentColumn = ExperimentColumn("FF", method_factories["FF"])
        self.methods: list[ExperimentColumn] = [self.tomo, self.s3d, self.dct, self.ff]

        # Top controls
        self.widget_exp_select: widgets.Combobox = widgets.Combobox(
            options=sorted(self.exp_list), description="Experiment: "
        )
        self.widget_beamline_dropdown: widgets.Dropdown = widgets.Dropdown(
            description="Beamline: "
        )
        for widget in [self.widget_exp_select, self.widget_beamline_dropdown]:
            widget.layout = widgets.Layout(
                width=f"{LAYOUT_WIDTH_WINDOW}%",
                justify_content="space-between",
                display="flex",
            )
            widget.style = {"description_width": "100px"}

        self._setup_observers()

        # If experiment came preselected (e.g., notebook sets it), populate beamlines now.
        if self.widget_exp_select.value:
            self.update_beamline_options()

    def _init_layout(self) -> None:
        """Lay out the page: status line, selectors, breadcrumbs, and four method columns."""
        self.vbox_methods: list[widgets.VBox] = [
            widgets.VBox(
                [widgets.HTML("<h3>Tomography</h3>"), self.tomo], layout=self.layout
            ),
            widgets.VBox([widgets.HTML("<h3>DCT</h3>"), self.dct], layout=self.layout),
            widgets.VBox(
                [widgets.HTML("<h3>Far field</h3>"), self.ff], layout=self.layout
            ),
            widgets.VBox(
                [widgets.HTML("<h3>s3DXRD</h3>"), self.s3d], layout=self.layout
            ),
        ]
        self.children = [
            widgets.HBox(
                children=([self.status_label, self.refresh_tree_btn]),
                layout=widgets.Layout(
                    width=f"{LAYOUT_WIDTH_WINDOW}%",
                    justify_content="space-between",
                    display="flex",
                ),
            ),
            widgets.HTML(
                "<p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>"
            ),
            widgets.HBox(
                children=([self.custom_root, self.custom_root_btn]),
                layout=widgets.Layout(
                    width=f"{LAYOUT_WIDTH_WINDOW}%",
                    justify_content="space-between",
                    display="flex",
                    align_items="center",
                ),
            ),
            widgets.HTML(
                "<p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>"
            ),
            widgets.HBox([self.widget_exp_select, self.widget_beamline_dropdown]),
            widgets.HTML(
                "<p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>"
            ),
            self.breadcrumbs,
            widgets.HTML(
                "<p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>"
            ),
            widgets.HBox(
                [
                    widgets.VBox(
                        [widgets.HTML("<h3>Folder Tree</h3>"), self.tree],
                        layout=widgets.Layout(
                            width="auto",
                            flex="1 1 auto",
                            min_width="100px",
                            max_width="200px",
                        ),
                    ),
                    *self.vbox_methods,
                ]
            ),
        ]

        # Keep each column's original layout to restore later after collapse
        for col in self.vbox_methods:
            if not hasattr(col, "_orig_layout"):
                col._orig_layout = col.layout  # type: ignore[attr-defined]

    def _setup_observers(self) -> None:
        """Wire change observers for the two selectors."""
        # EXPERIMENT change → recompute beamline options from free-typed value
        self.widget_exp_select.observe(self.update_beamline_options, names="value")
        # BEAMLINE change → build tree/accordions (debounced)
        self.widget_beamline_dropdown.observe(
            self._debounced_update_root, names="value"
        )

    # ---- Debounce ----
    def _debounced_update_root(self, change: TraitChange) -> None:
        """Debounce root updates to avoid double builds on quick selector changes."""
        now: float = time.time()
        if now - self._last_change_ts < 0.25:
            return
        self._last_change_ts = now
        self.update_root_folder({"new": True})

    # ---- Actions ----
    def refresh_tree(self, _btn: widgets.Button | None = None) -> None:
        """Manual refresh button: rebuilds the listing if both selectors are set."""
        if self.widget_exp_select.value and self.widget_beamline_dropdown.value:
            self.update_root_folder({"new": True})
        elif self.logic.root_folder:
            self.refresh()

    def on_manual_root_submit(self, _btn: widgets.Button | None = None) -> None:
        """
        Allow the user to override the base visitor root from the UI.
        """
        raw_value: str = (self.custom_root.value or "").strip()
        if not raw_value:
            self.status_label.value = (
                "Enter a session path (contains RAW_DATA/PROCESSED_DATA)."
            )
            return

        candidate = Path(raw_value).expanduser()
        try:
            self.logic.set_base_path(candidate)
            manual_root = self.logic.select_manual_root(candidate)
        except FileNotFoundError:
            self.status_label.value = f"Base path not found: {candidate}"
            return
        except NotADirectoryError:
            self.status_label.value = f"Base path is not a directory: {candidate}"
            return
        except ValueError as exc:
            self.status_label.value = str(exc)
            return
        except Exception as exc:  # noqa: BLE001
            self.status_label.value = f"Cannot use base path {candidate}: {exc}"
            return

        set_visitor_root(str(self.logic.base_path))
        self.base_path = self.logic.base_path
        self.custom_root.value = str(manual_root)
        self.exp_list = []
        self.widget_exp_select.options = []
        # self.widget_exp_select.value = None
        self.widget_beamline_dropdown.options = []
        # self.widget_beamline_dropdown.value = None
        self.tree.children = ()
        self.file_content.children = ()
        self.breadcrumbs.children = ()
        self.dataset_to_widget.clear()
        self.active_accordion = None
        self.selected_file = None
        self.active_button = None
        self.selected_file_path.value = ""
        self.logic.root_folder = manual_root
        self.create_tree_view()
        self.create_breadcrumbs()
        self.status_label.value = f"Exploring {manual_root}"

    def update_beamline_options(self, _change: TraitChange | None = None) -> None:
        """
        Populate beamline dropdown from the *typed* experiment name; do not coerce user input.
        """
        exp: str = (self.widget_exp_select.value or "").strip()
        if not exp:
            self.widget_beamline_dropdown.options = []
            self.widget_beamline_dropdown.value = None
            self.status_label.value = "Select (or type) an experiment."
            return

        self.exp_list = self.logic.list_experiments()
        self.widget_exp_select.options = sorted(self.exp_list)

        try:
            beamlines: list[str] = self.logic.list_beamlines(exp)
        except FileNotFoundError:
            self.widget_beamline_dropdown.options = []
            self.widget_beamline_dropdown.value = None
            suggestions: list[str] = [
                o
                for o in self.widget_exp_select.options
                if exp.lower() in str(o).lower()
            ]
            hint: str = (
                f"  |  Suggestions: {', '.join(suggestions[:5])}" if suggestions else ""
            )
            self.status_label.value = (
                f"Experiment folder not found: {self.base_path / exp}{hint}"
            )
            return
        except OSError as e:
            self.widget_beamline_dropdown.options = []
            self.widget_beamline_dropdown.value = None
            self.status_label.value = (
                f"Cannot list beamlines in {self.base_path / exp}: {e}"
            )
            return

        self.widget_beamline_dropdown.options = beamlines

        # Only auto-select the beamline if exactly one exists and value is empty/invalid
        if len(beamlines) == 1 and self.widget_beamline_dropdown.value != beamlines[0]:
            self.widget_beamline_dropdown.value = beamlines[0]
        elif self.widget_beamline_dropdown.value not in beamlines:
            self.widget_beamline_dropdown.value = None
            self.status_label.value = "Pick a beamline."
        else:
            # If beamline already valid, kick the debounced build (no auto-coercion of experiment)
            self._debounced_update_root({"new": True})

    def update_root_folder(self, change: TraitChange) -> None:
        """
        Compute the experiment root based on current selectors, and (re)build the cache.
        """
        if not change.get("new"):
            return
        if not (self.widget_exp_select.value and self.widget_beamline_dropdown.value):
            return

        self.status_label.value = (
            "Building samples structure for "
            f"{self.base_path / self.widget_exp_select.value / self.widget_beamline_dropdown.value}"
        )
        try:
            self.logic.select_experiment(
                self.widget_exp_select.value, self.widget_beamline_dropdown.value
            )
        except FileNotFoundError as e:
            self.status_label.value = str(e)
            return
        except ValueError as e:
            self.status_label.value = str(e)
            return

        self.create_breadcrumbs()
        self.create_tree_view()
        self.status_label.value = "Ready..."

    def check_completion(self, _=None) -> bool:
        """Return True if both selectors are filled."""
        return all(
            widget.value
            for widget in [self.widget_exp_select, self.widget_beamline_dropdown]
        )

    def create_tree_view(self) -> None:
        """
        Create root folder button and populate its children via update_tree.
        """
        if self.logic.root_folder:
            root_button: widgets.Button = widgets.Button(
                description=str(self.logic.root_folder),
                layout=widgets.Layout(width="auto"),
            )
            root_button.on_click(self.on_folder_click)
            self.tree.children = (root_button,)
            node: FileNode | None = self.logic.ensure_node(self.logic.root_folder)
            if node:
                self.update_tree(node)

    def on_folder_click(self, b: widgets.Button) -> None:
        """
        Navigate into a folder when a folder button is clicked.
        """
        desc_path: Path = Path(str(b.description))
        base_root = self.logic.root_folder
        folder_path: Path
        if desc_path.is_absolute() or base_root is None:
            folder_path = desc_path
        else:
            folder_path = Path(base_root) / b.description
        if folder_path.is_dir():
            self.logic.root_folder = folder_path
            node: FileNode | None = self.logic.ensure_node(folder_path)
            if node:
                self.update_tree(node)
                self.create_breadcrumbs()
            self.file_content.children = ()

    def update_tree(self, node: FileNode | None) -> None:
        """
        Given a FileNode for the current folder, populate the left folder list
        and per-method dataset accordions.
        """
        if not node or not getattr(node, "children", None):
            self.tree.children = ()
            return

        # folders on the left, naturally sorted
        buttons: list[widgets.Button] = [
            widgets.Button(description=child.name, layout=widgets.Layout(width="auto"))
            for child in node.children
            if not getattr(child, "is_file", False)
        ]
        buttons.sort(key=lambda b: _nkey(b.description))
        for btn in buttons:
            btn.on_click(self.on_folder_click)
        self.tree.children = tuple(buttons)

        datasets_by_method = self.logic.datasets_by_path(Path(node.path))
        # per-method dataset accordions
        for wid in self.methods:
            wid.tree = datasets_by_method.get(wid.name, [])
            new_children: list[widgets.Accordion] = []
            for child in wid.tree:
                acc: widgets.Accordion = widgets.Accordion(
                    layout=widgets.Layout(width="auto")
                )
                acc.children = (widgets.VBox(),)
                acc.set_title(0, child.dataset)
                handler = partial(
                    self.on_dataset_accordion_change,
                    dataset=child,
                    method=wid.method,
                    acc=acc,
                )
                _safe_reobserve(acc, handler, names="selected_index")
                new_children.append(acc)

                # collision-proof key + backward-compatible key
                self.dataset_to_widget[(wid.name, child.dataset)] = acc
                self.dataset_to_widget[child.dataset] = acc

                self.update_color_acc(child)
            wid.children = tuple(new_children)

    # Function to be triggered (restores your original first-level behavior)
    def on_dataset_accordion_change(
        self, change: TraitChange, dataset: Any, method: Any, acc: widgets.Accordion
    ) -> None:
        """
        When opening a dataset (first-level) accordion:
            - widen the corresponding method column,
            - collapse the others,
            - inject the ProcessedPathAccordeon for the selected dataset.
        """
        if change.get("name") != "selected_index":
            return

        if change.get("new") is not None:  # section is open
            if self.active_accordion and self.active_accordion != change.get("owner"):
                self.active_accordion.selected_index = None
            self.active_accordion = change.get("owner")

            for wid in self.vbox_methods:
                try:
                    same_method: bool = (
                        isinstance(wid.children[1].method.__class__, method.__class__)
                        and wid.children[1].method.__module__ == method.__module__
                    )
                except Exception:
                    same_method = False

                if same_method:
                    # Put the dataset panel in the currently opened Accordion
                    acc.children = [
                        ProcessedPathAccordeon(dataset, controller=self, method=method)
                    ]  # pass controller+factory
                    # widen active column
                    wid.layout.width = "auto"
                else:
                    # restore your original pattern: replace layout object completely
                    wid.layout = widgets.Layout(width="10px")
        elif self.active_accordion == change.get("owner"):
            self.active_accordion = None
            for child in self.vbox_methods:
                # restore original saved layout
                child.layout = getattr(child, "_orig_layout", self.layout)

        self.update_color_acc(dataset)

    def refresh_dataset(self, dataset: Any, method_factory: Any | None = None) -> None:
        """
        Recompute the processing_state and UI for a single dataset only:
            - rebuild its processing_state from processed_path,
            - re-run status file loads,
            - update its first-level accordion color,
            - rebuild its inner panel (if it's open / present).
        """
        # Resolve factory: prefer the provided one; else infer from dataset.method name
        if method_factory is None:
            mname = getattr(dataset, "method", None)
            if isinstance(mname, str):
                method_factory = self.logic.method_factories.get(mname)

        self.logic.refresh_dataset(dataset, method_factory)

        # Update the dataset-level accordion color
        self.update_color_acc(dataset)

        # If the dataset accordion exists, rebuild its content panel
        acc = self.dataset_to_widget.get(
            (getattr(dataset, "method", None), dataset.dataset)
        ) or self.dataset_to_widget.get(dataset.dataset)
        if isinstance(acc, widgets.Accordion):
            acc.children = [
                ProcessedPathAccordeon(dataset, controller=self, method=method_factory)
            ]

    def update_color_acc(self, dataset: Any) -> None:
        """
        Update the border color of the dataset-level accordion based on current status.
        """
        key_precise = (getattr(dataset, "method", None), dataset.dataset)
        acc: widgets.Accordion | None = self.dataset_to_widget.get(
            key_precise
        ) or self.dataset_to_widget.get(
            dataset.dataset
        )  # type: ignore[assignment]
        if acc:
            color: str = COLOR_NOT_PROCESSED
            if getattr(dataset, "processing_state", None):
                for state in dataset.processing_state:
                    if getattr(state, "statusFilesLaunched", False):
                        if getattr(state, "filesOk", False):
                            color = COLOR_PROCESSED
                        elif color != COLOR_PROCESSED:
                            color = COLOR_BEING_PROCESSED
                    if getattr(state, "statusDetailedLaunched", False):
                        if getattr(state, "detailedOk", False):
                            color = COLOR_PROCESSED
                        elif color != COLOR_PROCESSED:
                            color = COLOR_BEING_PROCESSED
            acc.layout.border = f"2px solid {color}"
        else:
            logger.warning(
                "The dataset %s was not found for color widget update", dataset.dataset
            )

    def load_file_content(self, _=None) -> None:
        """
        Display a structural HTML preview for the currently selected file, if any.
        """
        if self.selected_file:
            content: Any = loadFile(self.selected_file)
            self.file_content.children = (widgets.HTML(value=content.display_struct()),)
        else:
            self.file_content.children = (widgets.HTML(value="No file selected"),)

    def create_breadcrumbs(self) -> None:
        """
        Rebuild the breadcrumb buttons up to the current `root_folder`.
        """
        if self.logic.root_folder:
            path_parts: tuple[str, ...] = Path(self.logic.root_folder).parts
            links: list[widgets.Button] = []
            for i in range(len(path_parts)):
                path_i: Path = Path(*path_parts[: i + 1])
                button: widgets.Button = widgets.Button(
                    description=(path_i.name or str(path_i)),
                    layout=widgets.Layout(width="auto"),
                )
                button.on_click(self.on_breadcrumb_click(path_i))
                links.append(button)
            self.breadcrumbs.children = tuple(links)

    def on_breadcrumb_click(self, path: Path):
        """
        Return a callback that navigates to `path` in the file cache and updates UI.
        """

        def handle_click(_btn: widgets.Button | None = None) -> None:
            self.logic.root_folder = path
            node: FileNode | None = self.logic.ensure_node(path)
            if node:
                self.update_tree(node)
                self.create_breadcrumbs()
            self.file_content.children = ()

        return handle_click

    def refresh(self) -> None:
        """
        Refresh the current folder view, rebuilding the cache if the root has changed.
        """
        self.status_label.value = "Refreshing..."
        node: FileNode | None = self.logic.refresh()
        if node:
            self.update_tree(node)
        self.create_breadcrumbs()
        self.status_label.value = "Ready..."

    # public accessor kept for compatibility
    def get_tab(self) -> DatasetSelectionTab:
        """Return the tab instance (compat API)."""
        return self


def main(*, show: bool = True) -> DatasetSelectionTab:
    """
    Entry point used by CLI wrappers and notebooks.

    Parameters
    ----------
    show:
        When true (default) immediately display the widget via IPython.display.

    Returns
    -------
    DatasetSelectionTab
        The instantiated widget so callers can interact with it programmatically.
    """
    tab = DatasetSelectionTab()
    if show:
        display(tab)
    return tab


if __name__ == "__main__":
    # If you run this file directly, we check if there's an IPython/Jupyter front-end.
    try:
        import IPython

        if IPython.get_ipython() is None:
            raise RuntimeError(
                "This GUI uses ipywidgets and must run in Jupyter (Notebook/Lab/Voila)."
            )
        main()
    except Exception as e:
        # Clear, explicit message when started from plain python
        print(e)
        print(
            "Tip: open a Jupyter Notebook and run:\n\n"
            "    from your_module import main\n"
            "    main()\n\n"
        )
