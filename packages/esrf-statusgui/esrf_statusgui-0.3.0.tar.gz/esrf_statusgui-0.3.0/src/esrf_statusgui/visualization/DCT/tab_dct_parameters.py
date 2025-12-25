import logging
import os
from contextlib import contextmanager
from datetime import date, datetime

import ipywidgets as widgets
import numpy as np

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path
try:
    from esrf_loadFile import loadFile
except ImportError:
    from esrf_statusgui.data_managment.loadFile import loadFile
from IPython.display import display

from esrf_statusgui.data_managment.dct_parameter import dct_parameter
from esrf_statusgui.file_utils.file_utils import is_date
from esrf_statusgui.file_utils.FolderPermissionChecker import FolderPermissionChecker
from esrf_statusgui.file_utils.newExperimentDate import newExperimentDate
from esrf_statusgui.file_utils.paths import _safe_attr, describe
from esrf_statusgui.visualization.DCT.tab_load_parameter import ParametersSelector

logger = logging.getLogger(__name__)


class ParametersEntryTab(widgets.VBox):
    def __init__(self, parameters=None):
        if parameters is None:
            parameters = dct_parameter()
        super().__init__()
        self.parameters = parameters
        self.layout_dropdown = self.parameters.internal.layout or widgets.Layout()
        self.observe_bool = True
        self.detector = None
        self.h5file = None
        self._loaded_raw_data = None
        self._structure_info = None
        self.create_widgets()
        self.setup_observers()
        self.initialize_data()

    def create_widgets(self):
        # TODO: Add the eyepiece dropdown (0.9, 1, 2) for marana1
        hbox_width = "300px"
        self.scan_types = ["fscan_v1", "dctscan", "finterlaced", "ebs_tomo"]
        self.widget_distortion = widgets.Text(
            description="Distortion",
            value=self.parameters.acq.distortion() or "N/A",
            disabled=True,
        )
        self.widget_energy = widgets.FloatText(description="energy - Energy [keV]: ")
        self.widget_phases = widgets.IntText(
            description="phases - Number of phases:", value=1
        )
        self.widget_camera = widgets.Dropdown(
            description="sensortype - Detector used:",
            value=self.parameters.acq.sensortype() or "N/A",
            disabled=True,
            options=[
                "frelon1",
                "frelon16",
                "marana",
                "marana1",
                "marana3",
                "pco_nf",
                "N/A",
            ],
        )
        self.widget_eyepiece = widgets.Dropdown(
            options=["0.9", "1.0", "2.0", "2.5", "1e6"],
            description="eyepiece - Select the eyepiece for m1:",
            value="1.0",
        )
        self.widget_objective = widgets.Dropdown(
            options=["5.0", "7.5", "10.0", "20.0"],
            value="10.0",
            description="objective - Select the objective used:",
        )
        scan_type_value = (
            self.parameters.acq.scan_type()
            if self.parameters.acq.scan_type() in self.scan_types
            else f"Scan not recognized: {self.parameters.acq.scan_type()}"
        )
        self.widget_scan_type = widgets.Dropdown(
            description="scan_type - Scan type: ",
            value=scan_type_value,
            options=self.scan_types + [scan_type_value],
            disabled=True,
        )
        self.widget_date = widgets.HTML()
        self.widget_collection_dir = widgets.Text(
            description="collection_dir - Collection directory:",
            value=self.parameters.acq.collection_dir() or "N/A",
            disabled=True,
        )
        self.widget_name = widgets.Text(
            description="name - Name of the dataset:",
            value=self.parameters.acq.name() or "N/A",
            disabled=True,
        )
        self.widget_dir = widgets.Text(
            description="dir - Directory in which to analyze the data:",
            value=self.parameters.acq.dir() or "N/A",
            disabled=True,
        )
        self.widget_xdet = widgets.IntText(
            description="xdet - Detector ROI size X or U in pixel",
            value=self.parameters.acq.xdet() or None,
            disabled=True,
        )
        self.widget_ydet = widgets.IntText(
            description="ydet - Detector ROI size Y or V in pixel",
            value=self.parameters.acq.ydet() or None,
            disabled=True,
        )
        self.widget_nproj = widgets.IntText(
            description="nproj - Number of images in *180 degrees* of scan",
            value=self.parameters.acq.nproj() or None,
            disabled=True,
        )
        self.widget_refon = widgets.IntText(
            description="nrefon - References after how many images ?",
            value=self.parameters.acq.refon() or 0,
            disabled=True,
        )
        self.widget_nref = widgets.IntText(
            description="nref - How many reference images in a group ?",
            value=self.parameters.acq.nref() or 0,
            disabled=True,
        )
        self.widget_ndark = widgets.IntText(
            description="ndark - How many dark images taken ?",
            value=self.parameters.acq.ndark() or 0,
            disabled=True,
        )
        self.widget_pixel_size = widgets.FloatText(
            description="pixelsize - Detector pixel size (mm/pixel)",
            value=self.parameters.acq.pixelsize() or 0,
            disabled=True,
        )
        self.widget_dist = widgets.FloatText(
            description="dist - Sample-detector distance (mm) [computed]",
            value=self.parameters.acq.dist() or 5,
        )
        self.widget_type = widgets.Dropdown(
            description="type - DCT scan type:",
            value=self.parameters.acq.type() or "360degree",
            options=["180degree", "360degree", "dct", "topotomo"],
            disabled=True,
        )
        self.widget_interlaced_turns = widgets.IntText(
            description="interlaced_turns - Interlaced scan ?",
            value=self.parameters.acq.interlaced_turns() or 0,
            disabled=True,
        )
        self.widget_mono_tune = widgets.IntText(
            description="mono_tune - Monochromator tuned after N groups",
            value=self.parameters.acq.mono_tune() or 0,
            disabled=True,
        )
        self.widget_rotation_axis = widgets.Dropdown(
            description="roration_axis - Rotation axis orientation:",
            value=self.parameters.acq.rotation_axis() or "vertical",
            options=["vertical", "horizontal"],
            disabled=True,
        )
        self.checkbox_direct_beam = widgets.Checkbox(
            value=self.parameters.acq.no_direct_beam() or False,
            disabled=True,
            layout=widgets.Layout(justify_content="flex-start"),
        )
        self.widget_direct_beam = widgets.HBox(
            [
                widgets.Label(
                    "no_direct_beam - taper frelon, offset detector:",
                    layout=widgets.Layout(width=hbox_width, justify_content="flex-end"),
                ),
                self.checkbox_direct_beam,
            ]
        )
        self.widget_detector_def = widgets.Dropdown(
            description="detector_definition - Definition of the detector type:",
            options=["inline", "vertical"],
            value=self.parameters.acq.detector_definition() or "inline",
        )
        self.checkbox_flip_images = widgets.Checkbox(
            value=self.parameters.acq.flip_images() or False,
            disabled=True,
            layout=widgets.Layout(justify_content="flex-start"),
        )
        self.widget_flip_images = widgets.HBox(
            [
                widgets.Label(
                    "flip_image - Do you want to flip the images?",
                    layout=widgets.Layout(width=hbox_width, justify_content="flex-end"),
                ),
                self.checkbox_flip_images,
            ]
        )
        self.checkbox_online = widgets.Checkbox(
            value=self.parameters.acq.online() or False,
            disabled=True,
            layout=widgets.Layout(justify_content="flex-start"),
        )
        self.widget_online = widgets.HBox(
            [
                widgets.Label(
                    "online - Is the analysis online?",
                    layout=widgets.Layout(width=hbox_width, justify_content="flex-end"),
                ),
                self.checkbox_online,
            ]
        )
        self.checkbox_expert_mode = widgets.Checkbox(
            value=self.parameters.expert_mode() or False,
            layout=widgets.Layout(justify_content="flex-start"),
        )
        self.widget_expert_mode = widgets.HBox(
            [
                widgets.Label(
                    "Expert mode ? (check to activate)",
                    layout=widgets.Layout(width=hbox_width, justify_content="flex-end"),
                ),
                self.checkbox_expert_mode,
            ]
        )
        self.button_load_h5 = widgets.Button(
            description="Load from old parameters",
        )
        self.widget_load_h5 = widgets.Output()
        self.widget_flats_select = widgets.SelectMultiple(
            description="h5 group number of the flats",
            value=self._normalize_group(self.parameters.acq.flat(), [1, 3]),
            options=list(range(1, 5)),
            disabled=True,
        )
        self.widget_darks_select = widgets.SelectMultiple(
            description="h5 group number of the darks",
            value=self._normalize_group(self.parameters.acq.dark(), [4]),
            options=list(range(1, 5)),
            disabled=True,
        )
        self.widget_projections_select = widgets.SelectMultiple(
            description="h5 group number of the dct projections",
            value=self._normalize_group(self.parameters.acq.projections(), [2]),
            options=list(range(1, 5)),
            disabled=True,
        )

        self.children = [
            widgets.VBox(
                [
                    widgets.HBox(
                        [self.widget_date, self.button_load_h5],
                        layout=widgets.Layout(justify_content="space-between"),
                    ),
                    self.widget_load_h5,
                ]
            ),
            self.widget_expert_mode,
            self.widget_camera,
            self.widget_objective,
            self.widget_eyepiece,
            self.widget_energy,
            self.widget_phases,
            self.widget_dist,
            self.widget_scan_type,
            self.widget_type,
            self.widget_rotation_axis,
            self.widget_flip_images,
            self.widget_online,
            self.widget_direct_beam,
            self.widget_distortion,
            self.widget_collection_dir,
            self.widget_name,
            self.widget_dir,
            self.widget_xdet,
            self.widget_ydet,
            self.widget_projections_select,
            self.widget_nproj,
            self.widget_refon,
            self.widget_flats_select,
            self.widget_nref,
            self.widget_darks_select,
            self.widget_ndark,
            self.widget_pixel_size,
            self.widget_interlaced_turns,
            self.widget_mono_tune,
            self.widget_detector_def,
        ]

        self.widgets_map = {
            "widget_objective": (self.widget_objective, "objective"),
            "widget_energy": (self.widget_energy, "energy"),
            "widget_phases": (self.widget_phases, "nof_phases"),
            "widget_scan_type": (self.widget_scan_type, "scan_type"),
            "widget_camera": (self.widget_camera, "sensortype"),
            "widget_eyepiece": (self.widget_eyepiece, "eyepiece"),
            "widget_distortion": (self.widget_distortion, "distortion"),
            "widget_collection_dir": (self.widget_collection_dir, "collection_dir"),
            "widget_name": (self.widget_name, "name"),
            "widget_dir": (self.widget_dir, "dir"),
            "widget_xdet": (self.widget_xdet, "xdet"),
            "widget_ydet": (self.widget_ydet, "ydet"),
            "widget_projections_select": (
                self.widget_projections_select,
                "projections",
            ),
            "widget_nproj": (self.widget_nproj, "nproj"),
            "widget_refon": (self.widget_refon, "refon"),
            "widget_flats_select": (self.widget_flats_select, "flat"),
            "widget_nref": (self.widget_nref, "nref"),
            "widget_darks_select": (self.widget_darks_select, "dark"),
            "widget_ndark": (self.widget_ndark, "ndark"),
            "widget_pixel_size": (self.widget_pixel_size, "pixelsize"),
            "widget_dist": (self.widget_dist, "dist"),
            "widget_type": (self.widget_type, "type"),
            "widget_interlaced_turns": (
                self.widget_interlaced_turns,
                "interlaced_turns",
            ),
            "widget_mono_tune": (self.widget_mono_tune, "mono_tune"),
            "widget_rotation_axis": (self.widget_rotation_axis, "rotation_axis"),
            "checkbox_direct_beam": (self.checkbox_direct_beam, "no_direct_beam"),
            "widget_detector_def": (self.widget_detector_def, "detector_definition"),
            "checkbox_flip_images": (self.checkbox_flip_images, "flip_images"),
            "checkbox_online": (self.checkbox_online, "online"),
        }
        self.expert_widgets = [
            self.widget_camera,
            self.widget_type,
            self.widget_rotation_axis,
            self.widget_flip_images,
            self.widget_online,
            self.widget_direct_beam,
            self.widget_distortion,
            self.widget_collection_dir,
            self.widget_name,
            self.widget_dir,
            self.widget_xdet,
            self.widget_ydet,
            self.widget_projections_select,
            self.widget_nproj,
            self.widget_refon,
            self.widget_flats_select,
            self.widget_nref,
            self.widget_darks_select,
            self.widget_ndark,
            self.widget_pixel_size,
            self.widget_interlaced_turns,
            self.widget_mono_tune,
            self.widget_detector_def,
            self.checkbox_online,
            self.checkbox_direct_beam,
            self.checkbox_flip_images,
            self.widget_scan_type,
        ]

        self.configure_widgets()

    @staticmethod
    def _normalize_group(value, default):
        """Return a list suitable for SelectMultiple.value."""
        if value is None:
            return default

        # If it's a plain integer, wrap it
        if isinstance(value, int):
            return [value]

        # If it's something iterable (list, tuple, np.ndarray, etc.)
        try:
            value_list = list(value)
        except TypeError:
            # Not iterable but not None/int (very odd), wrap it
            return [value]

        # If the iterable is empty, use default
        return value_list if value_list else default

    @staticmethod
    def _normalize_group_type(description):
        """Normalize raw HDF5 group description into a canonical type."""
        if isinstance(description, (list, tuple)):
            description = next((item for item in description if item), None)
        if isinstance(description, np.ndarray):
            description = description.tolist()
            if isinstance(description, list):
                description = next((item for item in description if item), None)
        if isinstance(description, bytes):
            description = description.decode("utf-8", errors="ignore")

        if description is None:
            return None, None

        label = str(description).strip()
        if not label:
            return None, None

        lowered = label.lower()
        if "flat" in lowered:
            return "flat", label
        if "dark" in lowered:
            return "dark", label
        if "proj" in lowered:
            return "projections", label

        return lowered, label

    @staticmethod
    def _coerce_group_value(value):
        """Best-effort conversion of assorted identifiers into an integer group id."""
        if value is None:
            return None
        if isinstance(value, (int, np.integer)):
            return int(value)
        if isinstance(value, float) and value.is_integer():
            return int(value)
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            pass
        try:
            return int(text.split(".")[0])
        except (ValueError, IndexError):
            pass
        digits = "".join(char for char in text if char.isdigit())
        if digits:
            try:
                return int(digits)
            except ValueError:
                return None
        return None

    @classmethod
    def _min_group_identifier(cls, value):
        """Return the smallest valid integer identifier from assorted container types."""
        normalized = cls._normalize_group(value, [])
        candidates = [
            cls._coerce_group_value(item) for item in normalized if item is not None
        ]
        candidates = [item for item in candidates if item is not None]
        if not candidates:
            raise ValueError(f"No valid group identifiers found in {value!r}")
        return int(min(candidates))

    @staticmethod
    def _format_group_option(entry):
        """Format a SelectMultiple label combining group key and type."""
        group_label = entry.get("key") or entry.get("group_id") or "?"
        type_label = entry.get("type_label") or entry.get("type") or "unknown"
        if isinstance(type_label, (list, tuple)):
            type_label = ", ".join(str(item) for item in type_label if item)
        type_label = str(type_label) if type_label else "unknown"
        return f"{group_label} ({type_label})"

    def _resolve_default_selection(self, entries, parameter_value, all_values):
        """Determine default selection preserving existing values when possible."""
        normalized_current = self._normalize_group(parameter_value, [])
        current_values = [self._coerce_group_value(item) for item in normalized_current]
        current_values = [value for value in current_values if value in all_values]

        if current_values:
            return current_values

        entry_values = [
            self._coerce_group_value(entry.get("group_id")) for entry in entries
        ]
        entry_values = [value for value in entry_values if value is not None]

        if entry_values:
            return entry_values

        if all_values:
            return [all_values[0]]

        return []

    def _update_group_widgets(self, structure_info):
        """Populate group selection widgets with labeled options and sensible defaults."""
        if not self.h5file:
            return

        entries = []
        if structure_info:
            entries = structure_info.get("entries") or []

        if entries:
            options = [
                (self._format_group_option(entry), entry["group_id"])
                for entry in entries
            ]
            if options:
                all_values = [entry["group_id"] for entry in entries]
                self.widget_flats_select.options = options
                self.widget_projections_select.options = options
                self.widget_darks_select.options = options

                flat_selection = self._resolve_default_selection(
                    structure_info.get("flat_entries", []),
                    self.parameters.acq.flat(),
                    all_values,
                )
                projections_selection = self._resolve_default_selection(
                    structure_info.get("proj_entries", []),
                    self.parameters.acq.projections(),
                    all_values,
                )
                dark_selection = self._resolve_default_selection(
                    structure_info.get("dark_entries", []),
                    self.parameters.acq.dark(),
                    all_values,
                )

                self.widget_flats_select.value = tuple(flat_selection)
                self.widget_projections_select.value = tuple(projections_selection)
                self.widget_darks_select.value = tuple(dark_selection)

                self.parameters.acq.flat.value = list(flat_selection)
                self.parameters.acq.projections.value = list(projections_selection)
                self.parameters.acq.dark.value = list(dark_selection)

                self._update_acquisition_counts(
                    structure_info,
                    flat_selection,
                    projections_selection,
                    dark_selection,
                )
                return

        # Fallback: keep previously selected values available for editing
        current_flat = [
            self._coerce_group_value(item)
            for item in self._normalize_group(self.parameters.acq.flat(), [])
        ]
        current_projections = [
            self._coerce_group_value(item)
            for item in self._normalize_group(self.parameters.acq.projections(), [])
        ]
        current_dark = [
            self._coerce_group_value(item)
            for item in self._normalize_group(self.parameters.acq.dark(), [])
        ]

        flat_selection = [value for value in current_flat if value is not None]
        projections_selection = [
            value for value in current_projections if value is not None
        ]
        dark_selection = [value for value in current_dark if value is not None]

        fallback_values = sorted(
            {
                *flat_selection,
                *projections_selection,
                *dark_selection,
            }
        )

        options = [(str(value), value) for value in fallback_values]

        self.widget_flats_select.options = options
        self.widget_projections_select.options = options
        self.widget_darks_select.options = options

        if options:
            if not flat_selection:
                flat_selection = [options[0][1]]
            if not projections_selection:
                projections_selection = [options[0][1]]
            if not dark_selection:
                dark_selection = [options[0][1]]
        else:
            flat_selection = []
            projections_selection = []
            dark_selection = []

        self.widget_flats_select.value = tuple(flat_selection)
        self.widget_projections_select.value = tuple(projections_selection)
        self.widget_darks_select.value = tuple(dark_selection)

        self.parameters.acq.flat.value = list(flat_selection)
        self.parameters.acq.projections.value = list(projections_selection)
        self.parameters.acq.dark.value = list(dark_selection)

    def _mean_frames(self, entries, selected_ids):
        if not entries or not selected_ids:
            return 0
        selected_set = {
            self._coerce_group_value(identifier) for identifier in selected_ids
        }
        frame_values: list[int] = []
        for entry in entries:
            group_id = self._coerce_group_value(entry.get("group_id"))
            if group_id in selected_set:
                frames = entry.get("frames")
                try:
                    frame_values.append(int(frames))
                except (TypeError, ValueError):
                    continue
        if not frame_values:
            return 0
        return int(sum(frame_values) / len(frame_values))

    def _update_acquisition_counts(
        self,
        structure_info,
        flat_selection,
        projections_selection,
        dark_selection,
    ):
        if not structure_info:
            return

        proj_frames = self._mean_frames(
            structure_info.get("proj_entries", []), projections_selection
        )
        dark_frames = self._mean_frames(
            structure_info.get("dark_entries", []), dark_selection
        )
        flat_frames = self._mean_frames(
            structure_info.get("flat_entries", []), flat_selection
        )

        self.parameters.acq.refon.value = proj_frames
        self.parameters.acq.nproj.value = int(proj_frames // 2)
        self.parameters.acq.ndark.value = dark_frames
        self.parameters.acq.nref.value = flat_frames

    def configure_widgets(self):
        for widget in self.children:
            if not isinstance(widget, widgets.HBox):
                widget.layout = self.layout_dropdown
                widget.style = {"description_width": "300px"}

    def on_button_load_h5_clicked(self, b):
        experiment = getattr(self.parameters.internal, "experiment", None)
        if not experiment and hasattr(self.parameters.acq, "RAW_DATA"):
            raw_path = getattr(self.parameters.acq, "RAW_DATA", None)
            if raw_path is not None:
                raw_path = Path(raw_path)
                info = describe(raw_path)
                experiment = info.proposal
                if not experiment:
                    try:
                        relative = raw_path.relative_to(info.data_root)
                        experiment = relative.parts[0] if relative.parts else None
                    except Exception:
                        experiment = None
        self.parameters_selector_widget = ParametersSelector(
            experiment, self.parameters.internal.exp_list
        )
        self.send_parameters_button = widgets.Button(description="Apply parameters.h5")
        self.send_parameters_button.on_click(self.apply_parameters)
        self.parameters_selector_widget.children[2].children = (
            self.parameters_selector_widget.children[2].children
            + (self.send_parameters_button,)
        )
        with self.widget_load_h5:
            self.widget_load_h5.clear_output()
            display(self.parameters_selector_widget)

    def apply_parameters(self, b):
        if self.parameters_selector_widget.path_selector.value is not None:
            if Path(self.parameters_selector_widget.path_selector.value).exists():
                self.parameters.internal.input_parameters = dct_parameter(
                    self.parameters_selector_widget.path_selector.value
                )
                to_keep = [
                    "dir",
                    "collection_dir",
                    "collection_dir_old",
                    "name",
                ]
                for par_to_keep in to_keep:
                    getattr(
                        self.parameters.internal.input_parameters.acq, par_to_keep
                    ).value = getattr(self.parameters.acq, par_to_keep)()
                self.parameters.internal.input_parameters.acq.RAW_DATA = (
                    self.parameters.acq.RAW_DATA
                )
                for key in list(self.parameters.internal.input_parameters.__dict__):
                    if hasattr(self.parameters, key):
                        setattr(
                            self.parameters,
                            key,
                            getattr(self.parameters.internal.input_parameters, key),
                        )
                self.parameters.internal.input_parameters = True
                if self.parameters.acq.beamline() is None:
                    self.load_detector_parameters()
                self.refresh()
            else:
                logging.warning(
                    f"File {str(Path(self.parameters_selector_widget.path_selector.value))} not available on disk"
                )
                self.parameters.internal.inputh5 = None

    def setup_observers(self):
        for _, (widget, param_attr) in self.widgets_map.items():
            widget.observe(
                lambda change, param_attr=param_attr: self.on_widget_change(
                    change, param_attr
                ),
                names=["value"],
            )
        self.checkbox_expert_mode.observe(self.on_expert_mode_change, names=["value"])
        self.button_load_h5.on_click(self.on_button_load_h5_clicked)

    def on_widget_change(self, change, param_attr):
        getattr(self.parameters.acq, param_attr).value = change["new"]
        if self.observe_bool:
            self.refresh()

    def on_expert_mode_change(self, change):
        self.parameters.expert_mode.value = change["new"]
        for widget in self.expert_widgets:
            widget.disabled = not change["new"]
        if self.observe_bool:
            self.refresh()

    @contextmanager
    def _pause_observers(self):
        previous_state = self.observe_bool
        self.observe_bool = False
        try:
            yield
        finally:
            self.observe_bool = previous_state

    @staticmethod
    def _coerce_raw_data_path(raw_data_value):
        if not raw_data_value:
            return None
        return (
            raw_data_value if isinstance(raw_data_value, Path) else Path(raw_data_value)
        )

    def _clear_loaded_state(self):
        self._loaded_raw_data = None
        self.h5file = None
        self.detector = None
        self._structure_info = None

    def initialize_data(self):
        with self._pause_observers():
            self._run_refresh_pipeline(force_reload=True)

    def _run_refresh_pipeline(self, force_reload=False):
        self._update_raw_dataset(force_reload=force_reload)
        self._finalize_refresh()

    def _update_raw_dataset(self, force_reload=False):
        current_raw = self._coerce_raw_data_path(self.parameters.acq.RAW_DATA)
        should_reload = force_reload or (
            current_raw is not None
            and (self._loaded_raw_data is None or current_raw != self._loaded_raw_data)
        )

        if current_raw is None:
            self._clear_loaded_state()
            return

        if should_reload:
            self._load_new_raw_dataset(current_raw)

    def _finalize_refresh(self):
        self._update_derived_parameters()
        self.update_html_widgets_date()
        self._sync_widgets_from_parameters()

    def setup_parameters(self):
        acquisition_dir = self._determine_acquisition_dir()

        force_update = self.detector is None
        if str(self.parameters.acq.dir.value) != str(acquisition_dir) or force_update:
            self.parameters.acq.dir.value = acquisition_dir
            self.parameters.acq.name.value = acquisition_dir.name
            self.parameters.acq.pair_tablename.value = (
                f"{acquisition_dir.name}spotpairs"
            )
            self.parameters.acq.calib_tablename.value = (
                f"{acquisition_dir.name}paircalib"
            )
            self.parameters.acq.collection_dir.value = (
                acquisition_dir / "0_rawdata/Orig"
            )
            self.parameters.acq.collection_dir_old.value = Path(
                self.parameters.acq.RAW_DATA
            ).parent
            self.load_detector_parameters()
            self.load_scan_parameters()
        self.update_scan_parameters()

    def _determine_acquisition_dir(self):
        """Return the processing directory associated with the current RAW dataset."""
        raw_dir = Path(self.parameters.acq.RAW_DATA)
        if hasattr(raw_dir, "raw_dataset_path"):
            direct_path = self._determine_dir_from_dataset_root(
                raw_dir.raw_dataset_path
            )
        else:
            direct_path = self._determine_dir_from_dataset_root(raw_dir)
        if direct_path is not None:
            return direct_path

        return self._determine_dir_legacy(raw_dir)

    def _determine_dir_from_dataset_root(self, dataset_root):
        """Best-effort resolution relying on ESRFPath metadata helpers."""
        try:
            session_date = _safe_attr(dataset_root, "session_date")
            raw_data_root = _safe_attr(dataset_root, "raw_data_path")
            if raw_data_root is not None and isinstance(raw_data_root, Path):
                beamline_root = raw_data_root.parent.parent
            else:
                beamline_root = dataset_root.parent.parent.parent

            latest_session_date = session_date
            try:
                session_candidates: list[tuple[date, Path]] = []
                with os.scandir(beamline_root) as entries:
                    for entry in entries:
                        if not entry.is_dir():
                            continue
                        entry_path = Path(entry.path)
                        try:
                            candidate_date = entry_path.session_date
                        except AttributeError:
                            continue
                        session_candidates.append((candidate_date, entry_path))
                if session_candidates:
                    latest_session_date, _ = max(
                        session_candidates, key=lambda pair: pair[0]
                    )
            except Exception:  # pragma: no cover - best effort discovery
                logger.debug(
                    "Unable to enumerate session directories under %s", beamline_root
                )

            # TODO: Change the date by checking the most recent one available is not owned by root (restored from tape). If it's the case, create a new date with SCRIPT and PROCESSED_DATA folder structure
            return dataset_root.replace_fields(
                data_type="PROCESSED_DATA", session_date=latest_session_date
            )
        except (AttributeError, RuntimeError) as exc:
            logger.debug(
                "Falling back to legacy path handling for %s: %s", dataset_root, exc
            )
            return None

    def _determine_dir_legacy(self, raw_dir):
        """Fallback to legacy filesystem heuristics when metadata helpers fail."""
        acquisition_dir = None
        temp_dir = raw_dir
        fallback_dir = Path(raw_dir.as_posix().replace("RAW_DATA", "PROCESSED_DATA"))
        if raw_dir.is_file():
            fallback_dir = fallback_dir.parent

        while not is_date(temp_dir.name):
            if temp_dir.parent == temp_dir:
                temp_dir = None
                break
            temp_dir = temp_dir.parent

        if temp_dir and is_date(temp_dir.name):
            dataset = raw_dir.relative_to(temp_dir / "RAW_DATA")
            beamline_root = temp_dir.parent
            dates = []
            with os.scandir(beamline_root) as entries:
                for candidate in entries:
                    if not candidate.is_dir() or candidate.name.startswith("."):
                        continue
                    parsed = is_date(candidate.name)
                    if parsed:
                        dates.append(parsed)
            if dates:
                latest_date = max(dates)
                target_session = beamline_root / latest_date.strftime("%Y%m%d")
                acquisition_dir = target_session / "PROCESSED_DATA" / dataset.parent
                if not FolderPermissionChecker(target_session).checkWritePermission():
                    new_session_date = datetime.now().strftime("%Y%m%d")
                    target_session = beamline_root / new_session_date
                    newExperimentDate(target_session, True)
                    acquisition_dir = target_session / "PROCESSED_DATA" / dataset.parent

        if acquisition_dir is None:
            acquisition_dir = fallback_dir
        return acquisition_dir

    def guess_objective(self):
        tolerance = 0.05
        objective_index: int | None = None

        def _extract_scalar(value):
            if value is None:
                return None
            arr = np.asarray(value)
            if arr.size == 0:
                return None
            if arr.ndim == 0:
                return float(arr)
            return float(np.median(arr))

        def _active_pixels(profile: np.ndarray) -> int:
            if profile.size == 0:
                return 0
            threshold = float(np.std(profile))
            active = int(np.count_nonzero(profile > threshold))
            if active:
                return active
            # fallback on mean if std-based threshold fails
            threshold = float(np.mean(profile))
            return int(np.count_nonzero(profile > threshold))

        try:
            beamline = self.parameters.acq.beamline()
            detector = self.parameters.acq.sensortype()
            if not beamline or not detector:
                logging.warning("Beamline or detector information is missing.")

            path_prefix = f"entry_0000/{beamline}/{detector}"
            pixel_size_detector = (
                self.detector.get_value(
                    f"{path_prefix}/detector_information/pixel_size/xsize"
                )
                / (
                    np.array(self.widget_objective.options, dtype=float)
                    * float(self.parameters.acq.eyepiece())
                )
                * 1e3
            )
            raw_frame = self.detector.get_value(f"{path_prefix}/data")[0]
            if raw_frame.ndim != 2:
                logging.warning("Unexpected detector frame shape.")

            ref_scan_beg = getattr(self.parameters.internal, "ref_scan_beg", None)
            if ref_scan_beg is None:
                logging.warning("Reference scan begin index is not defined.")
                ref_scan_beg = 1

            ref_prefix = f"{ref_scan_beg}.1/instrument/positioners"
            slit_values = {
                "horizontal": _extract_scalar(
                    self.h5file.get_value(f"{ref_prefix}/s7hg")
                ),
                "vertical": _extract_scalar(
                    self.h5file.get_value(f"{ref_prefix}/s7vg")
                ),
            }

            profiles = {
                "horizontal": np.std(raw_frame, axis=0),
                "vertical": np.std(raw_frame, axis=1),
            }

            estimates: list[float] = []
            candidate_records: list[tuple[int, float]] = []
            expected_sizes = np.asarray(pixel_size_detector, dtype=float)

            for orientation, profile in profiles.items():
                slit_value = slit_values.get(orientation)
                if slit_value is None or not np.isfinite(slit_value):
                    continue
                pixels = _active_pixels(profile)
                if pixels <= 0:
                    continue
                estimate = slit_value / pixels
                if not np.isfinite(estimate):
                    continue
                estimates.append(estimate)

                differences = np.abs(expected_sizes - estimate)
                idx = int(np.argmin(differences))
                expected_value = expected_sizes[idx]
                if expected_value == 0:
                    continue
                rel_error = differences[idx] / abs(expected_value)
                candidate_records.append((idx, rel_error))

            valid_candidates = [
                record for record in candidate_records if record[1] <= tolerance
            ]
            if valid_candidates:
                by_index: dict[int, list[float]] = {}
                for idx, rel_err in valid_candidates:
                    by_index.setdefault(idx, []).append(rel_err)
                objective_index = max(
                    by_index.items(),
                    key=lambda item: (len(item[1]), -min(item[1])),
                )[0]
            elif len(estimates) >= 2:
                combined = float(np.median(estimates))
                differences = np.abs(expected_sizes - combined)
                idx = int(np.argmin(differences))
                expected_value = expected_sizes[idx]
                if expected_value != 0:
                    rel_error = differences[idx] / abs(expected_value)
                    if rel_error <= tolerance:
                        objective_index = idx
        except Exception as exc:
            logging.warning(
                "Raw image could not be opened for objective determination: %s", exc
            )

        if objective_index is not None:
            self.parameters.acq.objective.value = self.widget_objective.options[
                objective_index
            ]
        else:
            self.parameters.acq.objective.value = "10.0"
            logging.info("Objective was not possible to guess")

    def load_detector_parameters(self):
        if not self.detector:
            self.detector = loadFile(
                f"{Path(self.parameters.acq.RAW_DATA).parent}/scan0001/{self.parameters.acq.sensortype()}_0000.h5"
            )
        self.parameters.acq.beamline.value = [
            i for i in self.detector.get_keys("entry_0000") if "ESRF" in i
        ][0]
        detector_data = self.detector.get_value(
            f"entry_0000/{self.parameters.acq.beamline()}/{self.parameters.acq.sensortype()}"
        )
        image_operation = detector_data.get_value("image_operation")
        detector_info = detector_data.get_value("detector_information")

        self.parameters.acq.xdet.value = image_operation.get_value("dimension/xsize")
        self.parameters.acq.ydet.value = image_operation.get_value("dimension/ysize")
        self.parameters.acq.true_detsizeu.value = detector_info.get_value(
            "max_image_size/xsize"
        )
        self.parameters.acq.true_detsizev.value = detector_info.get_value(
            "max_image_size/ysize"
        )
        self.parameters.acq.detroi_u_off.value = image_operation.get_value(
            "region_of_interest/xstart"
        )
        self.parameters.acq.detroi_v_off.value = image_operation.get_value(
            "region_of_interest/ystart"
        )
        self.parameters.detgeo.readout_delay_sec.value = detector_data.get_value(
            "acquisition/latency_time"
        )

    def load_scan_parameters(self):
        projection_group = self._min_group_identifier(self.parameters.acq.projections())
        flat_group = self._min_group_identifier(self.parameters.acq.flat())
        dark_group = self._min_group_identifier(self.parameters.acq.dark())

        if f"{projection_group}.1" in self.h5file.get_keys():
            pars_dct = self.h5file.get_value(f"{projection_group}.1/instrument")
        else:
            logging.warning("Projection scan not found")
            pars_dct = None

        if f"{flat_group}.1" in self.h5file.get_keys():
            pars_ref = self.h5file.get_value(f"{flat_group}.1/projections")
        else:
            logging.warning("Reference scan not found")
            pars_ref = None

        if f"{dark_group}.1" in self.h5file.get_keys():
            pars_dark = self.h5file.get_value(f"{dark_group}.1/projections")
        else:
            logging.warning("Dark scan not found")
            pars_dark = None

        if pars_dct:
            if "dct_parameters" in pars_dct.get_keys():
                par_key = "dct_parameters"
                self.parameters.acq.count_time.value = pars_dct.get_value(
                    f"{par_key}/exp_time"
                )
                self.parameters.acq.nproj.value = (
                    pars_dct.get_value(f"{par_key}/rot_range")
                    / pars_dct.get_value(f"{par_key}/step_size")
                    / 2
                    if not self.parameters.acq.nproj()
                    else self.parameters.acq.nproj()
                )
                self.parameters.acq.refon.value = pars_dct.get_value(
                    f"{par_key}/rot_range"
                ) / pars_dct.get_value(f"{par_key}/step_size")
                self.parameters.acq.scan_type.value = "dctscan"
                self.parameters.acq.interlaced_turns.value = (
                    pars_dct.get_value(f"{par_key}/scan_name") == "finterlaced"
                )
                # TODO: Change the diffrz determination by adding the parameter in the dct acquisition class
                if "id11" in self.parameters.acq.dir().parts:
                    self.parameters.acq.rotation_name.value = "diffrz"
                elif "id03" in self.parameters.acq.dir().parts:
                    self.parameters.acq.rotation_name.value = "omega"
            else:
                par_key = "fscan_parameters"
                self.parameters.acq.count_time.value = pars_dct.get_value(
                    f"{par_key}/acq_time"
                )
                self.parameters.acq.nproj.value = (
                    pars_dct.get_value(f"{par_key}/npoints") / 2
                    if not self.parameters.acq.nproj()
                    else self.parameters.acq.nproj()
                )
                self.parameters.acq.refon.value = pars_dct.get_value(
                    f"{par_key}/npoints"
                )
                self.parameters.acq.scan_type.value = pars_dct.get_value(
                    f"{par_key}/scan_name"
                )
                self.parameters.acq.interlaced_turns.value = (
                    pars_dct.get_value(f"{par_key}/scan_name") == "finterlaced"
                )
                self.parameters.acq.rotation_name.value = pars_dct.get_value(
                    f"{par_key}/motor"
                )

            self.parameters.acq.dist.value = pars_dct.get_value("positioners/nfdtx")
            dct = dct_parameter()
            dct.load_group(pars_dct.get_value("positioners_start"), dct.acq.motors)
            self.parameters.acq.motors.merge(dct.acq.motors)
            self.parameters.acq.motors.diffrz.value = pars_dct.get_value(
                f"{self.parameters.acq.rotation_name.value}/value"
            )
        if pars_ref:
            self.parameters.acq.nref.value = pars_ref.get_value(
                self.parameters.acq.sensortype()
            ).shape[0]
        if pars_dark:
            self.parameters.acq.ndark.value = pars_dark.get_value(
                self.parameters.acq.sensortype()
            ).shape[0]
        if self.parameters.acq.motors.samtx():
            self.parameters.acq.sample_shifts.value = [
                getattr(
                    self.parameters.acq.motors,
                    self.parameters.diffractometer.motor_samtx(),
                )(),
                getattr(
                    self.parameters.acq.motors,
                    self.parameters.diffractometer.motor_samty(),
                )(),
                getattr(
                    self.parameters.acq.motors,
                    self.parameters.diffractometer.motor_samtz(),
                )(),
            ]
        else:
            self.parameters.acq.sample_shifts.value = [0, 0, 0]
        if getattr(
            self.parameters.acq.motors,
            self.parameters.diffractometer.motor_samtilt_bot(),
        )():
            self.parameters.acq.sample_tilts.value = [
                getattr(
                    self.parameters.acq.motors,
                    self.parameters.diffractometer.motor_samtilt_bot(),
                )(),
                getattr(
                    self.parameters.acq.motors,
                    self.parameters.diffractometer.motor_samtilt_top(),
                )(),
            ]
        else:
            self.parameters.acq.sample_tilts.value = [0, 0]
        if self.parameters.acq.scan_type() == "fscan":
            self.parameters.acq.scan_type.value = "fscan_v1"
        self.parameters.acq.beamchroma.value = "mono"
        self.parameters.diffractometer = dct_parameter.Diffractometer()

    def update_scan_parameters(self):
        self.parameters.acq.beamline.value = [
            i for i in self.detector.get_keys("entry_0000") if "ESRF" in i
        ][0]
        self.parameters.acq.pixelsize.value = (
            self.detector.get_value(
                f"entry_0000/{self.parameters.acq.beamline()}/{self.parameters.acq.sensortype()}/detector_information/pixel_size/xsize"
            )
            / (
                float(self.parameters.acq.objective())
                * float(self.parameters.acq.eyepiece())
            )
            * 1e3
        )
        self.set_distortion_values()

    def set_sensor_type(self):
        self.parameters.acq.date.value = datetime.fromisoformat(
            self.h5file.get_value("1.1/end_time")
        )
        if self.parameters.acq.sensortype() is None:
            self.detect_sensor_type()

    def setup_distortions(self, guess_obj=False):
        if self.parameters.acq.objective() is None:
            if guess_obj:
                self.guess_objective()

        self.set_distortion_values()

    def detect_sensor_type(self):
        # TODO: detect the detector name from the h5 more cleverly.
        sensor_type_keys = [
            i
            for i in self.h5file.get_keys("1.1/instrument")
            if i in self.widget_camera.options
        ]
        if "marana1" == sensor_type_keys[0]:
            self.parameters.acq.eyepiece.value = "0.9"
            if self.parameters.acq.date() < self.parameters.internal.reference_dates[2]:
                self.parameters.acq.sensortype.value = "frelon1"
            elif (
                self.parameters.acq.date() < self.parameters.internal.reference_dates[0]
            ):
                self.parameters.acq.sensortype.value = "frelon16"
            elif (
                self.parameters.acq.date() < self.parameters.internal.reference_dates[1]
            ):
                self.parameters.acq.sensortype.value = "marana2"
            else:
                self.parameters.acq.sensortype.value = "marana1"
        elif "marana3" == sensor_type_keys[0]:
            if (
                self.parameters.acq.date()
                >= self.parameters.internal.reference_dates[0]
            ):
                self.parameters.acq.eyepiece.value = "1.0"
            else:
                self.parameters.acq.eyepiece.value = "0.9"
            if self.parameters.acq.date() < self.parameters.internal.reference_dates[1]:
                self.parameters.acq.sensortype.value = "marana"
            else:
                self.parameters.acq.sensortype.value = "marana3"
        elif sensor_type_keys[0] == "frelon1":
            self.parameters.acq.eyepiece.value = "1.0"
            self.parameters.acq.sensortype.value = "frelon1"
        elif sensor_type_keys[0] == "frelon16":
            self.parameters.acq.eyepiece.value = "1.0"
            self.parameters.acq.sensortype.value = "frelon16"
        else:
            logging.warning(
                f"{sensor_type_keys[0]} is not recognizable! Please review the logic of the code to include your detector"
            )
            self.parameters.acq.eyepiece.value = "1e6"

    def set_distortion_values(self):
        if self.parameters.acq.sensortype() in ["marana", "marana3"]:
            self.widget_eyepiece.disabled = True
            self.set_marana3_distortion()
        elif self.parameters.acq.sensortype() == "marana1":
            self.widget_eyepiece.disabled = False
            self.set_marana1_distortion()
        elif self.parameters.acq.sensortype() == "frelon1":
            self.parameters.acq.distortion.value = (
                "/data/id11/archive/distortion/frelon1/WB_10X_no_eyepiece.dm"
            )
        elif self.parameters.acq.sensortype() == "frelon16":
            self.parameters.acq.distortion.value = f"/data/id11/archive/distortion/frelon16/latest/dm_{float(self.parameters.acq.objective()):.2g}x.dm"
        else:
            self.parameters.acq.distortion.value = None

    def set_marana3_distortion(self):
        if self.parameters.acq.date() >= self.parameters.internal.reference_dates[0]:
            if self.parameters.acq.objective() != "7.5":
                distortion_file = (
                    f"distmap_{float(self.parameters.acq.objective()):.2g}x.dm"
                )
            else:
                distortion_file = "distmap_7p5x.dm"
        else:
            distortion_file = f"dm_{float(self.parameters.acq.objective()):.2g}x.mat"

        self.parameters.acq.distortion.value = (
            f"/data/id11/archive/distortion/marana_d3/{distortion_file}"
        )

    def set_marana1_distortion(self):
        if self.parameters.acq.objective() != "7.5":
            distortion_file = (
                f"distmap_{float(self.parameters.acq.objective()):.2g}x.dm"
            )
        else:
            distortion_file = "distmap_7p5x.dm"
        self.parameters.acq.distortion.value = (
            f"/data/id11/archive/distortion/marana_d1/latest/{distortion_file}"
        )

    def update_html_widgets_date(self):
        raw_date = self.parameters.acq.date()
        formatted = "N/A"

        if raw_date:
            parsed = None
            if isinstance(raw_date, datetime):
                parsed = raw_date
            elif isinstance(raw_date, date):
                parsed = datetime.combine(raw_date, datetime.min.time())
            elif isinstance(raw_date, str):
                try:
                    parsed = datetime.fromisoformat(raw_date)
                except ValueError:
                    for fmt in ("%Y%m%d", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                        try:
                            parsed = datetime.strptime(raw_date, fmt)
                            break
                        except ValueError:
                            continue
            if parsed:
                formatted = parsed.strftime("%Y/%m/%d, %H:%M:%S")
            else:
                formatted = str(raw_date)

        self.widget_date.value = f"<p>Raw data collected on {formatted}</p>"

    def _load_new_raw_dataset(self, raw_path):
        """Load H5 content and detector metadata for a RAW_DATA selection."""
        self._clear_loaded_state()
        resolved_raw_path = raw_path if isinstance(raw_path, Path) else Path(raw_path)
        try:
            self.h5file = loadFile(resolved_raw_path)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.error("Unable to load RAW_DATA file %s: %s", resolved_raw_path, exc)
            return

        self._loaded_raw_data = resolved_raw_path
        self.set_sensor_type()
        self.load_detector_parameters()
        self.setup_distortions(True)
        self._structure_info = self._detect_dataset_structure()
        if self._structure_info:
            self._update_group_widgets(self._structure_info)
        self.setup_parameters()

    def _update_derived_parameters(self):
        """Recompute values that depend on current selections (objective, eyepiece)."""
        if not self.detector:
            return
        try:
            self.update_scan_parameters()
        except Exception as exc:  # pragma: no cover - keep UI responsive
            logger.warning("Scan parameters update failed: %s", exc)

    def _sync_widgets_from_parameters(self):
        """Push parameter values into the widgets without clobbering falsy values."""
        for widget, param_attr in self.widgets_map.values():
            try:
                value = getattr(self.parameters.acq, param_attr)()
                if isinstance(widget, widgets.SelectMultiple):
                    if value is None:
                        continue
                    if isinstance(value, int):
                        widget.value = (value,)
                    elif isinstance(value, (list, tuple, np.ndarray)):
                        widget.value = tuple(value)
                    else:
                        continue
                    continue

                if isinstance(value, Path):
                    widget.value = str(value)
                elif value is not None:
                    widget.value = value
            except Exception as exc:  # pragma: no cover - keep UI responsive
                logger.warning(
                    "Unable to sync widget for parameter %s: %s", param_attr, exc
                )

    def refresh(self):
        with self._pause_observers():
            self._run_refresh_pipeline()

    def check_completion(self, _=None):
        return all(
            widget.value is not None
            for widget in self.children
            if not isinstance(widget, (widgets.HBox, widgets.VBox, widgets.Output))
        )

    def get_tab(self):
        return self

    def _detect_dataset_structure(self):
        if not self.h5file or not self.parameters.acq.RAW_DATA:
            return None

        sensor = self.parameters.acq.sensortype()
        if not sensor:
            sensor = self.detect_sensor_type()
            if sensor:
                self.parameters.acq.sensortype.value = sensor

        groups_info = []
        for key in sorted(self.h5file.get_keys()):
            if "version" in str(key).lower():
                continue
            try:
                entry_type_raw = self.h5file.get_description(f"{key}")
            except Exception:
                entry_type_raw = None

            key_str = str(key)
            if "." in key_str:
                suffix = key_str.rsplit(".", 1)[-1]
                if suffix != "1":
                    continue
            canonical_type, type_label = self._normalize_group_type(entry_type_raw)

            frame_count = 0
            if sensor:
                try:
                    frame_size = self.h5file.get_size(f"{key}/measurement/{sensor}")
                except Exception:
                    frame_size = None
                if isinstance(frame_size, tuple):
                    frame_count = frame_size[0]
                elif isinstance(frame_size, int):
                    frame_count = frame_size
            try:
                group_id = self._coerce_group_value(key)
            except Exception:
                group_id = None
            if group_id is None:
                continue
            groups_info.append(
                {
                    "key": key,
                    "type": canonical_type or "unknown",
                    "type_label": type_label or canonical_type or "unknown",
                    "group_id": group_id,
                    "frames": frame_count,
                }
            )

        if not groups_info:
            return None

        if len(groups_info) == 4:
            expected_types = {"projections", "flat", "dark"}
            actual_types = {g["type"] for g in groups_info}
            if not expected_types.issubset(actual_types):
                key_lookup = {str(g["key"]): g for g in groups_info}

                def _force_type(key_name, forced_type):
                    entry = key_lookup.get(key_name)
                    if not entry:
                        return
                    entry["type"] = forced_type

                _force_type("1.1", "flat")
                _force_type("2.1", "projections")
                _force_type("3.1", "flat")
                _force_type("4.1", "dark")

        structure = {
            "entries": groups_info,
            "flat_entries": [g for g in groups_info if g["type"] == "flat"],
            "dark_entries": [g for g in groups_info if g["type"] == "dark"],
            "proj_entries": [g for g in groups_info if g["type"] == "projections"],
        }

        return structure
