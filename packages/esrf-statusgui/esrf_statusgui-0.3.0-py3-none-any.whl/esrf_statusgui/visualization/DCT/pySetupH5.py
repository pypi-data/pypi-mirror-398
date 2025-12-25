import copy
import logging
import os
from datetime import datetime, timezone
from types import SimpleNamespace

import h5py
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

# Add custom module path
from esrf_statusgui.file_utils.createProcessingNotebook import create_processing_nb_DCT
from esrf_statusgui.file_utils.file_utils import create_DCT_directories
from esrf_statusgui.file_utils.paths import get_visitor_root
from esrf_statusgui.visualization.navigation_buttons import Navigation

from .tab_crystallo import CrystalloTab
from .tab_dataset_walk import DatasetSelectionTab
from .tab_dct_parameters import ParametersEntryTab
from .tab_experiment_selection import WelcomeTab

logger = logging.getLogger(__name__)


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


class pySetupH5:
    def __init__(self):
        self.initialize()
        self.create_tabs()
        self.navigation = Navigation(
            self.tabs, self.parameters, self.setup_pre_processing
        )
        self.out_message = widgets.Output()
        self.setup_tab_change_observer()

    def initialize(
        self,
        ref_scan_beg: int = 1,
        proj_scan_dct: int = 2,
        ref_scan_end: int = 3,
        dark_scan: int = 4,
    ):
        self.parameters = dct_parameter()
        self.parameters.internal = SimpleNamespace()
        self.parameters.internal.base_path = get_visitor_root()
        if os.path.exists("/data/id11/archive/file_xop"):
            self.parameters.internal.xop_path = Path("/data/id11/archive/file_xop")
        else:
            logging.warning(
                "This functionality is not implemented yet outside of the ESRF network. You need access to /data/id11/archive/file_xop"
            )
        self.parameters.internal.ref_scan_beg = ref_scan_beg
        self.parameters.internal.proj_scan_dct = proj_scan_dct
        self.parameters.internal.ref_scan_end = ref_scan_end
        self.parameters.internal.dark_scan = dark_scan
        self.parameters.acq.RAW_DATA = None
        self.parameters._set_default()
        self.parameters.internal.reference_dates = [
            datetime(2023, 11, 14, tzinfo=timezone.utc),
            datetime(2024, 1, 16, tzinfo=timezone.utc),
            datetime(2023, 1, 1, tzinfo=timezone.utc),
        ]

        try:
            exp_entries = os.listdir(self.parameters.internal.base_path)
        except (FileNotFoundError, PermissionError) as exc:
            logging.warning(
                "Visitor root %s is not accessible (%s); use the manual RAW path field.",
                self.parameters.internal.base_path,
                exc,
            )
            exp_entries = []
        self.parameters.internal.exp_dirs = [
            self.parameters.internal.base_path / item
            for item in exp_entries
            if (self.parameters.internal.base_path / item).is_dir()
        ]
        self.parameters.internal.exp_list = [
            item.stem for item in self.parameters.internal.exp_dirs
        ]
        self.parameters.internal.layout = widgets.Layout(
            width="600px", justify_content="space-between", display="flex"
        )

    def create_tabs(self):
        self.welcome_tab = WelcomeTab(self.parameters)
        self.dataset_selection_tab = DatasetSelectionTab(self.parameters)
        self.parameters_tab = ParametersEntryTab(self.parameters)
        self.phases_tab = CrystalloTab(self.parameters)

        self.tabs = widgets.Tab(
            children=[
                self.welcome_tab.get_tab(),
                self.dataset_selection_tab.get_tab(),
                self.parameters_tab.get_tab(),
                self.phases_tab.get_tab(),
            ]
        )
        self.tabs.set_title(0, "Welcome")
        self.tabs.set_title(1, "Dataset selection")
        self.tabs.set_title(2, "Parameters")
        self.tabs.set_title(3, "Crystallography")

    def setup_tab_change_observer(self):
        self.tabs.observe(self.on_tab_change, "selected_index")
        self.welcome_tab.widget_exp_select.observe(
            self.check_tab_completion, names="value"
        )
        self.welcome_tab.widget_beamline_dropdown.observe(
            self.check_tab_completion, names="value"
        )
        self.welcome_tab.widget_experiment_date.observe(
            self.check_tab_completion, names="value"
        )
        self.welcome_tab.manual_root_button.on_click(self.on_manual_root_chosen)
        self.dataset_selection_tab.selected_file_path.observe(
            self.check_tab_completion, names="value"
        )
        self.phases_tab.all_phases_completion.observe(
            self.check_tab_completion, names="value"
        )

    def on_manual_root_chosen(self, _btn=None):
        """
        When the user provides a manual RAW path, sync acquisition root and rebuild the tree.
        """
        self._sync_raw_data_from_welcome()
        if self.parameters.acq.RAW_DATA:
            self.dataset_selection_tab.refresh()
        self.check_tab_completion()

    def on_tab_change(self, change):
        self._sync_raw_data_from_welcome()
        if change["new"] == 1:  # Index of the FolderExplorer tab
            self.dataset_selection_tab.refresh()
        if change["new"] == 2:  # Index of the FolderExplorer tab
            selected_file = self.dataset_selection_tab.selected_file
            if selected_file:
                self.parameters.acq.RAW_DATA = Path(selected_file)
            self.parameters_tab.refresh()
        if change["new"] == 3:  # Index of the FolderExplorer tab
            if (
                hasattr(self.parameters.internal, "input_parameters")
                and self.parameters.internal.input_parameters is not None
            ):
                self.navigation.next_button.disabled = False
                self.navigation.next_button.click()
            else:
                self.phases_tab._init_phases()
        self.check_tab_completion()

    def _sync_raw_data_from_welcome(self) -> None:
        manual_root = getattr(self.welcome_tab, "manual_root", None)
        if manual_root:
            self.parameters.acq.RAW_DATA = Path(manual_root)
            return

        if self.welcome_tab.check_completion():
            self.parameters.acq.RAW_DATA = (
                Path(self.parameters.internal.base_path)
                / self.welcome_tab.widget_exp_select.value
                / self.welcome_tab.widget_beamline_dropdown.value
                / self.welcome_tab.widget_experiment_date.value
                / "RAW_DATA"
            )
        else:
            self.parameters.acq.RAW_DATA = None

    def check_tab_completion(self, _=None):
        if self.tabs.selected_index == 0:
            manual_root = getattr(self.welcome_tab, "manual_root", None)
            if manual_root:
                all_filled = True
                self.parameters.acq.RAW_DATA = Path(manual_root)
            else:
                all_filled = self.welcome_tab.check_completion()
                if all_filled:
                    self.parameters.acq.RAW_DATA = (
                        Path(self.parameters.internal.base_path)
                        / self.welcome_tab.widget_exp_select.value
                        / self.welcome_tab.widget_beamline_dropdown.value
                        / self.welcome_tab.widget_experiment_date.value
                        / "RAW_DATA"
                    )
            self.tabs.set_title(0, "[done] Welcome" if all_filled else "Welcome")
            self.navigation.next_button.disabled = not all_filled
        elif self.tabs.selected_index == 1:
            file_selected = bool(self.dataset_selection_tab.selected_file)
            self.tabs.set_title(
                1,
                "[done] Dataset selection" if file_selected else "Dataset selection",
            )
            self.navigation.next_button.disabled = not file_selected
        elif self.tabs.selected_index == 2:
            all_filled = self.parameters_tab.check_completion()
            self.tabs.set_title(2, "[done] Parameters" if all_filled else "Parameters")
            self.navigation.next_button.disabled = not all_filled
            if all_filled:
                for _, (widget, param_attr) in self.parameters_tab.widgets_map.items():
                    if hasattr(self.parameters.acq, param_attr):
                        getattr(self.parameters.acq, param_attr).value = widget.value
                    else:
                        logging.warning(
                            f"Attribute error on the parameters form, {widget.description.split(' - ')[0]} not found in parameters.acq"
                        )
        elif self.tabs.selected_index == 3:
            all_filled = self.phases_tab.all_phases_completion.value
            self.tabs.set_title(
                3,
                "[done] Crystallography" if all_filled else "Crystallography",
            )
            self.navigation.next_button.disabled = not all_filled

    def display(self):
        display(
            widgets.VBox(
                [self.tabs, self.navigation.get_navigation(), self.out_message]
            )
        )

    def link_raw_data(self, src_dir, dest_dir):
        src_path = Path(src_dir)
        dest_path = Path(dest_dir)

        # Ensure the destination directory exists
        logger.info("Creating directory %s (parents=True, exist_ok=True)", dest_path)
        dest_path.mkdir(parents=True, exist_ok=True)

        try:
            with os.scandir(src_path) as entries:
                for entry in entries:
                    src_item = Path(entry.path).resolve()  # Resolve the full path
                    dest_item = dest_path / entry.name  # Set the destination symlink

                    if entry.is_dir():
                        # Recursively create symlinks for directories
                        self.link_raw_data(src_item, dest_item)
                    else:
                        try:
                            os.symlink(src_item, dest_item)
                            print(f"Symlink created: {dest_item} -> {src_item}")
                        except FileExistsError:
                            print(f"Symlink already exists: {dest_item}")
                        except OSError as e:
                            print(f"Error creating symlink: {e}")
        except OSError as exc:
            print(f"Error scanning {src_path}: {exc}")

    @staticmethod
    def _normalize_group_ids(values):
        if values is None:
            return []
        if isinstance(values, (int, np.integer)):
            return [int(values)]
        if isinstance(values, float) and values.is_integer():
            return [int(values)]
        if isinstance(values, str):
            values = [values]
        result: list[int] = []
        for item in values:
            if item is None:
                continue
            if isinstance(item, (int, np.integer)):
                result.append(int(item))
                continue
            if isinstance(item, float) and item.is_integer():
                result.append(int(item))
                continue
            text = str(item).strip()
            if not text:
                continue
            try:
                result.append(int(text))
                continue
            except ValueError:
                pass
            for separator in (".", "_"):
                if separator in text:
                    head = text.split(separator, 1)[0]
                    if head.isdigit():
                        result.append(int(head))
                        break
            else:
                digits = "".join(ch for ch in text if ch.isdigit())
                if digits:
                    try:
                        result.append(int(digits))
                    except ValueError:
                        continue
        seen = set()
        ordered: list[int] = []
        for value in result:
            if value not in seen:
                ordered.append(value)
                seen.add(value)
        return ordered

    @staticmethod
    def _group_name_matches(name: str, group_token: str) -> bool:
        if group_token not in name:
            return False
        idx = name.find(group_token)
        end_idx = idx + len(group_token)
        before = name[idx - 1] if idx > 0 else ""
        after = name[end_idx] if end_idx < len(name) else ""
        if before.isdigit() or after.isdigit():
            return False
        return True

    @staticmethod
    def _ensure_symlink(source: Path, destination: Path):
        logger.info(
            "Creating directory %s (parents=True, exist_ok=True)",
            destination.parent,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            if destination.exists() or destination.is_symlink():
                return
        except OSError:
            return
        try:
            os.symlink(source, destination)
        except FileExistsError:
            return
        except OSError as exc:
            logging.debug(
                "Failed to create symlink %s -> %s: %s", destination, source, exc
            )

    @staticmethod
    def _link_scan_sensor_files(
        scan_source: Path, scan_dest: Path, sensor_name: str | None
    ):
        logger.info("Creating directory %s (parents=True, exist_ok=True)", scan_dest)
        scan_dest.mkdir(parents=True, exist_ok=True)
        if scan_source.is_file():
            pySetupH5._ensure_symlink(scan_source, scan_dest / scan_source.name)
            return

        if not scan_source.is_dir():
            return

        sensor_token = (sensor_name or "").lower()
        h5_candidates = []
        if sensor_token:
            h5_candidates.extend(
                child
                for child in scan_source.iterdir()
                if child.is_file()
                and child.suffix.lower() == ".h5"
                and child.name.lower().startswith(sensor_token)
            )
        if not h5_candidates:
            h5_candidates.extend(
                child
                for child in scan_source.iterdir()
                if child.is_file() and child.suffix.lower() == ".h5"
            )
        if not h5_candidates:
            # Fallback to full directory linking if nothing matches.
            for child in scan_source.iterdir():
                if child.is_dir():
                    pySetupH5._link_scan_sensor_files(
                        child, scan_dest / child.name, sensor_name
                    )
                else:
                    pySetupH5._ensure_symlink(child, scan_dest / child.name)
            return

        for file_path in sorted(h5_candidates):
            pySetupH5._ensure_symlink(file_path, scan_dest / file_path.name)

    @staticmethod
    def _group_id_from_name(name: str) -> int | None:
        if not name:
            return None
        if not name[0].isdigit():
            return None
        head = name.split(".", 1)[0]
        digits = "".join(ch for ch in head if ch.isdigit())
        if not digits:
            return None
        try:
            return int(digits)
        except ValueError:
            return None

    def _dataset_group_names(
        self, dataset_path: Path, allowed_groups: set[int]
    ) -> list[str]:
        if not dataset_path or not dataset_path.exists():
            return []
        group_names: list[str] = []
        try:
            with h5py.File(dataset_path, "r") as handle:
                for key in handle.keys():
                    group_id = self._group_id_from_name(key)
                    if group_id is not None and group_id in allowed_groups:
                        group_names.append(key)
        except OSError as exc:
            logging.warning("Unable to inspect dataset %s: %s", dataset_path, exc)
        return group_names

    @staticmethod
    def _create_dataset_subset(
        dataset_src: Path, dest_dataset: Path, group_names: set[str]
    ) -> bool:
        if not group_names:
            return False
        logger.info(
            "Creating directory %s (parents=True, exist_ok=True)",
            dest_dataset.parent,
        )
        dest_dataset.parent.mkdir(parents=True, exist_ok=True)
        if dest_dataset.exists():
            try:
                dest_dataset.unlink()
            except OSError as exc:
                logging.warning(
                    "Unable to remove existing dataset %s: %s", dest_dataset, exc
                )
                return False
        try:
            with h5py.File(dest_dataset, "w") as handle:
                handle.attrs["source_dataset"] = str(dataset_src)
                for name in group_names:
                    handle[name] = h5py.ExternalLink(str(dataset_src), name)
        except OSError as exc:
            logging.warning(
                "Failed to create dataset subset %s from %s: %s",
                dest_dataset,
                dataset_src,
                exc,
            )
            return False
        return True

    def _link_selected_raw_data(
        self, src_dir: Path, dest_dir: Path, par, gr_index: int
    ):
        src_dir = src_dir.raw_dataset_path
        logger.info("Creating directory %s (parents=True, exist_ok=True)", dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        flat_groups = self._normalize_group_ids(par.acq.flat())
        dark_groups = self._normalize_group_ids(par.acq.dark())
        proj_groups = self._normalize_group_ids([gr_index])
        selected_groups: set[int] = set(flat_groups + dark_groups + proj_groups)
        if not selected_groups:
            logging.warning(
                "No group identifiers provided for selective RAW_DATA linking."
            )
            return
        group_name: set[str] = set()
        for group_id in sorted(selected_groups):
            scan = src_dir / f"scan{group_id:04d}"
            if scan.is_dir():
                logger.info(
                    "Creating directory %s (parents=True, exist_ok=True)",
                    dest_dir / scan.name,
                )
                (dest_dir / scan.name).mkdir(parents=True, exist_ok=True)
            for file in scan.iterdir():
                try:
                    os.symlink(file, dest_dir / scan.name / file.name)
                    logging.info(
                        f"Symlink created: {dest_dir / scan.name / file.name} -> {file}"
                    )
                except FileExistsError:
                    logging.info(
                        f"Symlink already exists: {dest_dir / scan.name / file.name}"
                    )
                except OSError as e:
                    logging.warning(f"Error creating symlink: {e}")
            group_name.add(f"{group_id}.1")
            group_name.add(f"{group_id}.2")

        if not self._create_dataset_subset(
            src_dir.raw_dataset_file,
            dest_dir / dest_dir.processed_dataset_file.name,
            sorted(group_name),
        ):
            logging.warning(
                "Failed creating selective dataset file at %s",
                dest_dir / dest_dir.processed_dataset_file.name,
            )
            return

    def check_distortion(self):
        if self.parameters.acq.sensortype() == "frelon16" and (
            self.parameters.acq.objective() == "5.0"
            or self.parameters.acq.objective() == "7.5"
        ):
            self.parameters.acq.distortion.value = None
        if not Path(self.parameters.acq.distortion()).exists():
            logging.warning(
                f"The distortion file {self.parameters.acq.distortion()} doesn't exists, changed to None"
            )
            self.parameters.acq.distortion.value = None

    def gt_load_reflections_from_file(self, file: Path) -> dct_parameter.Xop:
        xop = dct_parameter.Xop()
        file = Path(file)
        reflections = loadFile(file)
        # Assign values to Xop object
        xop.hkl.value = reflections.get_value("hkl")
        xop.twotheta.value = reflections.get_value("twotheta")
        xop.dspacing.value = reflections.get_value("dspacing")
        xop.int.value = reflections.get_value("int")
        xop.formfactor.value = reflections.get_value("formfactor")
        xop.mult.value = reflections.get_value("mult")
        xop.xop_dir.value = file.parent
        xop.filename.value = file.name
        if xop.hkl() is not None:
            logging.info(f"Successfully loaded reflections from {file.name}")
        return xop

    def gt_load_symm_from_file(self, file: Path) -> dct_parameter.Cryst:
        # Helper function to simulate grep functionality in Python
        cryst = dct_parameter.Cryst()
        file = Path(file)
        cif = loadFile(file)
        # Determine file type and set patterns accordingly
        logging.info(f"Reading CIF data from {file}...")
        cryst.latticepar.value = cif.get_value("latticepar")
        cryst.opsym.value = cif.get_value("opsym")
        cryst.spacegroup.value = cif.get_value("spacegroup")
        cryst.hermann_mauguin.value = cif.get_value("hermann_mauguin")
        cryst.crystal_system.value = cif.get_value("crystal_system")
        logging.info(f"Successfully read CIF data from {file.name}")
        return cryst

    def xop_to_cryst(self, phase_id, to_extract=None):
        if to_extract is None:
            to_extract = ["hkl"]
        cryst_out = dct_parameter.Cryst()
        hkl = self.parameters.xop[phase_id].hkl()
        crystal_system = self.parameters.cryst[phase_id].crystal_system()

        if crystal_system in {"hexagonal", "trigonal"}:
            if hkl.shape[1] == 3:  # Change to four index hkil
                hkl = np.column_stack(
                    (hkl[:, 0], hkl[:, 1], -hkl[:, 0] - hkl[:, 1], hkl[:, 2])
                )
                self.parameters.xop[phase_id].hkl.value = hkl
            test = np.column_stack(
                (np.sort(np.abs(hkl[:, :3]), axis=1), np.abs(hkl[:, 3]))
            )
        elif crystal_system == "cubic":  # Sort hkl - h, k,l all equivalent
            test = np.sort(hkl, axis=1)
        elif crystal_system == "tetragonal":  # Assuming the output is already sorted
            test = hkl
        elif crystal_system == "orthorhombic":
            # treat sign variants as equivalent but keep axis ordering (a != b != c)
            test = np.abs(hkl)
        else:
            logging.warning(
                f'Need to add crystal system "{crystal_system}" to gt_find_families... quitting'
            )

        _, ind = np.unique(test, axis=0, return_index=True)  # Remove duplicates
        inds = np.sort(ind)  # Sort indexes
        for i in to_extract:
            getattr(cryst_out, i).value = getattr(self.parameters.xop[phase_id], i)()[
                inds
            ]
        return cryst_out

    def gt_cryst_hkl2cartesian_matrix(self, phaseID):
        def gt_maths_cross(vec1, vec2, dim=2):
            """
            Computes the cross product of vectors 1 and 2.
            Vectors should be ROW vectors.
            If multiple lines exist, computes the cross product of each line.
            """
            if dim == 1:
                res = np.array(
                    [
                        vec1[1, :] * vec2[2, :] - vec1[2, :] * vec2[1, :],
                        vec1[2, :] * vec2[0, :] - vec1[0, :] * vec2[2, :],
                        vec1[0, :] * vec2[1, :] - vec1[1, :] * vec2[0, :],
                    ]
                )
            elif dim == 2:
                res = np.array(
                    [
                        vec1[:, 1] * vec2[:, 2] - vec1[:, 2] * vec2[:, 1],
                        vec1[:, 2] * vec2[:, 0] - vec1[:, 0] * vec2[:, 2],
                        vec1[:, 0] * vec2[:, 1] - vec1[:, 1] * vec2[:, 0],
                    ]
                )
            elif dim == 3:
                res = np.array(
                    [
                        vec1[:, :, 1] * vec2[:, :, 2] - vec1[:, :, 2] * vec2[:, :, 1],
                        vec1[:, :, 2] * vec2[:, :, 0] - vec1[:, :, 0] * vec2[:, :, 2],
                        vec1[:, :, 0] * vec2[:, :, 1] - vec1[:, :, 1] * vec2[:, :, 0],
                    ]
                )
            return res

        cos_alpha = np.cos(np.radians(self.parameters.cryst[phaseID].latticepar()[3]))
        cos_beta = np.cos(np.radians(self.parameters.cryst[phaseID].latticepar()[4]))
        cos_gamma = np.cos(np.radians(self.parameters.cryst[phaseID].latticepar()[5]))
        sin_gamma = np.sin(np.radians(self.parameters.cryst[phaseID].latticepar()[5]))
        a = self.parameters.cryst[phaseID].latticepar()[0] * np.array([1, 0, 0])
        b = self.parameters.cryst[phaseID].latticepar()[1] * np.array(
            [cos_gamma, sin_gamma, 0]
        )
        c1 = self.parameters.cryst[phaseID].latticepar()[2] * cos_beta
        c2 = (
            self.parameters.cryst[phaseID].latticepar()[2]
            * (cos_alpha - cos_gamma * cos_beta)
            / sin_gamma
        )
        c = np.array(
            [
                c1,
                c2,
                np.sqrt(
                    self.parameters.cryst[phaseID].latticepar()[2] ** 2 + c1**2 + c2**2
                ),
            ]
        )
        Amat = np.vstack((a, b, c))
        cross_prods = gt_maths_cross(Amat, Amat[[1, 2, 0], :])
        cell_vol = np.dot(a, cross_prods[:, 1])
        Bmat = cross_prods[:, [1, 2, 0]] / cell_vol
        Amat = Amat.T
        return Bmat, Amat

    def gt_cryst_theta(self, dsp):
        """
        Calculates theta angle given a list of d-spacing.
        """

        def gt_conv_energy_to_wavelength(energy: float):
            """
            Converts beam energy in keV to wavelength in Angstroms.
            """
            return 6.62607015e-34 * 299792458 / (energy * 1.6021766339999e-16) * 1e10

        energy = self.parameters.acq.energy()
        sin_theta = gt_conv_energy_to_wavelength(energy) / (2 * dsp)
        theta = np.arcsin(sin_theta) * (180 / np.pi)  # Convert radians to degrees
        return theta, sin_theta

    def gt_cryst_d_spacing(self, hkl, bmat=None, phase_id=0):
        """
        Calculates d-spacing for a given set of Miller indices and lattice parameters.
        """
        if bmat is None:
            bmat = self.gt_cryst_hkl2cartesian_matrix(phase_id)[0]
        if hkl.shape[0] == 4:
            hkl = hkl[[0, 1, 3], :]
        ghkl = bmat @ hkl
        dsp = 1.0 / np.sqrt(np.sum(ghkl**2, axis=0))
        return dsp

    def gt_detector_two_theta(self, phaseID):
        cryst = self.xop_to_cryst(
            phaseID, to_extract=["hkl", "int", "formfactor", "mult"]
        )
        logging.info(f"hkl total families: {cryst.hkl().shape[1]}")
        cryst.dspacing.value = self.gt_cryst_d_spacing(cryst.hkl().T)
        cryst.theta.value = self.gt_cryst_theta(cryst.dspacing())[0]

        # Remove reflections out of detector
        ind = np.where(
            (cryst.theta() > self.parameters.detgeo.detanglemax() / 2)
            | (cryst.theta() < self.parameters.detgeo.detanglemin() / 2)
        )[0]

        # Remove them
        for j in ["theta", "dspacing", "int", "mult", "formfactor"]:
            getattr(cryst, j).value = np.delete(getattr(cryst, j)(), ind)
        cryst.hkl.value = np.delete(cryst.hkl(), ind, axis=0)

        # Order reflections by increasing theta values
        ind_tt = np.argsort(cryst.theta())
        for j in ["theta", "dspacing", "int", "mult", "formfactor"]:
            getattr(cryst, j).value = getattr(cryst, j)()[ind_tt]
        cryst.hkl.value = cryst.hkl()[ind_tt, :]
        cryst.thetatype.value = np.arange(1, len(cryst.mult()) + 1)

        print(f"Families on the detector: {cryst.hkl().shape[0]}")
        print("Now reflections are sorted by increasing theta values")
        return cryst

    def get_cubic_symmetry_operators(self, phase_id=0):
        g3_mats = [
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [[0, 0, -1], [0, -1, 0], [-1, 0, 0]],
            [[0, 0, -1], [0, 1, 0], [1, 0, 0]],
            [[-1, 0, 0], [0, 1, 0], [0, 0, -1]],
            [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],
            [[1, 0, 0], [0, 0, -1], [0, 1, 0]],
            [[1, 0, 0], [0, -1, 0], [0, 0, -1]],
            [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
            [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
            [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],
            [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],
            [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
            [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],
            [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],
            [[0, 1, 0], [0, 0, -1], [-1, 0, 0]],
            [[0, 0, -1], [1, 0, 0], [0, -1, 0]],
            [[0, 0, 1], [-1, 0, 0], [0, -1, 0]],
            [[0, -1, 0], [0, 0, -1], [1, 0, 0]],
            [[0, 1, 0], [1, 0, 0], [0, 0, -1]],
            [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
            [[0, 0, 1], [0, -1, 0], [1, 0, 0]],
            [[0, -1, 0], [-1, 0, 0], [0, 0, -1]],
            [[-1, 0, 0], [0, 0, -1], [0, -1, 0]],
        ]

        def _embed_g3(g3_mat):
            g_mat = np.eye(4)
            g_mat[:3, :3] = g3_mat
            return g_mat

        symm_ops = []
        for g3 in g3_mats:
            symm = dct_parameter.Cryst.Symm()
            symm.g3.value = np.array(g3, dtype=float)
            symm.g.value = _embed_g3(symm.g3())
            symm_ops.append(symm)
        self.parameters.cryst[phase_id].symm = symm_ops

    def get_tetragonal_symmetry_operators(self, phase_id=0):
        g3_mats = [
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
            [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],
            [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],
            [[1, 0, 0], [0, -1, 0], [0, 0, -1]],
            [[-1, 0, 0], [0, 1, 0], [0, 0, -1]],
            [[0, 1, 0], [1, 0, 0], [0, 0, -1]],
            [[0, -1, 0], [-1, 0, 0], [0, 0, -1]],
        ]

        def _embed_g3(g3_mat):
            g_mat = np.eye(4)
            g_mat[:3, :3] = g3_mat
            return g_mat

        symm_ops = []
        for g3 in g3_mats:
            symm = dct_parameter.Cryst.Symm()
            symm.g3.value = np.array(g3, dtype=float)
            symm.g.value = _embed_g3(symm.g3())
            symm_ops.append(symm)
        self.parameters.cryst[phase_id].symm = symm_ops

    def get_hexagonal_symmetry_operators(self, phase_id=0):
        g_mats = [
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]],
            [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]],
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]],
            [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, -1]],
            [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, -1]],
            [[-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]],
            [[0, 0, -1, 0], [-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 0, 1]],
            [[0, -1, 0, 0], [0, 0, -1, 0], [-1, 0, 0, 0], [0, 0, 0, 1]],
            [[-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, -1]],
            [[0, 0, -1, 0], [-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 0, -1]],
            [[0, -1, 0, 0], [0, 0, -1, 0], [-1, 0, 0, 0], [0, 0, 0, -1]],
        ]
        self.parameters.cryst[phase_id].symm = []
        for g_mat in g_mats:
            symm = dct_parameter.Cryst.Symm()
            symm.g.value = np.array(g_mat, dtype=float)
            symm.g3.value = symm.g()[:3, :3]
            self.parameters.cryst[phase_id].symm.append(symm)
        mirror = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
        for i in range(6):
            angle = i * 60
            ca, sa = np.cos(np.radians(angle)), np.sin(np.radians(angle))
            self.parameters.cryst[phase_id].symm[i].g3.value = np.array(
                [[ca, sa, 0], [-sa, ca, 0], [0, 0, 1]]
            )
        for i in range(6):
            self.parameters.cryst[phase_id].symm[i + 6].g3.value = (
                mirror @ self.parameters.cryst[phase_id].symm[i].g3()
            )

    def get_trigonal_symmetry_operators(self, phase_id=0):
        c = np.cos(np.radians(120))
        s = np.sin(np.radians(120))
        g3 = [
            np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]]),
            np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]),
            np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]]),
        ]
        g3.append(g3[1] @ g3[3] @ g3[2])  # Rotate 180 around hex axis 2
        g3.append(g3[2] @ g3[3] @ g3[1])  # Rotate 180 around hex axis 3
        g_mats = [
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]],
            [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]],
            [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, -1]],
            [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, -1]],
            [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]],
        ]

        self.parameters.cryst[phase_id].symm = []
        for g3_mat, g_mat in zip(g3, g_mats):
            symm = dct_parameter.Cryst.Symm()
            symm.g3.value = np.array(g3_mat, dtype=float)
            symm.g.value = np.array(g_mat, dtype=float)
            self.parameters.cryst[phase_id].symm.append(symm)

    def gt_cryst_get_symm_operators(self, phase_id=0):
        """
        Provides the symmetry operators for the crystal systems: cubic, hexagonal, trigonal, tetragonal.
        """
        if self.parameters.cryst[phase_id].crystal_system() is None:
            if self.parameters.cryst[phase_id].spacegroup() is not None:
                if 195 <= self.parameters.cryst[phase_id].spacegroup() <= 230:
                    self.parameters.cryst[phase_id].crystal_system.value = "cubic"
                elif (
                    168 <= self.parameters.cryst[phase_id].spacegroup() <= 194
                    or self.parameters.cryst[phase_id].spacegroup() == 663
                ):
                    self.parameters.cryst[phase_id].crystal_system.value = "hexagonal"
                elif 143 <= self.parameters.cryst[phase_id].spacegroup() <= 167:
                    self.parameters.cryst[phase_id].crystal_system.value = "trigonal"
                elif 75 <= self.parameters.cryst[phase_id].spacegroup() <= 142:
                    self.parameters.cryst[phase_id].crystal_system.value = "tetragonal"
                else:
                    logging.warning(
                        f"Unimplemented spacegroup ({self.parameters.cryst[phase_id].spacegroup()})!"
                    )
            else:
                # Load from parameters file, simulated here as a dictionary
                parameters = dct_parameter()
                if parameters.cryst[phase_id].crystal_system() is None:
                    logging.warning(
                        "crystal_system is missing and parameters file cannot be found!"
                    )
        elif self.parameters.cryst[phase_id].spacegroup() is None:
            # Simulated parameters file lookup
            parameters = dct_parameter()

        # Define symmetry operators based on the crystal system
        if self.parameters.cryst[phase_id].crystal_system() == "cubic":
            if self.parameters.cryst[phase_id].spacegroup() and not (
                195 <= self.parameters.cryst[phase_id].spacegroup() <= 230
            ):
                logging.warning(
                    f"spacegroup ({self.parameters.cryst[phase_id].spacegroup()}) does not match with the crystal system ({self.parameters.cryst[phase_id].crystal_system()})!"
                )
            self.get_cubic_symmetry_operators(phase_id)

        elif self.parameters.cryst[phase_id].crystal_system() == "tetragonal":
            if self.parameters.cryst[phase_id].spacegroup() and not (
                75 <= self.parameters.cryst[phase_id].spacegroup() <= 142
            ):
                logging.warning(
                    f"spacegroup ({self.parameters.cryst[phase_id].spacegroup()}) does not match with the crystal system ({self.parameters.cryst[phase_id].crystal_system()})!"
                )
            self.get_tetragonal_symmetry_operators(phase_id)

        elif self.parameters.cryst[phase_id].crystal_system() == "hexagonal":
            if self.parameters.cryst[phase_id].spacegroup() and not (
                168 <= self.parameters.cryst[phase_id].spacegroup() <= 194
                or self.parameters.cryst[phase_id].spacegroup() == 663
            ):
                logging.warning(
                    f"spacegroup ({self.parameters.cryst[phase_id].spacegroup()}) does not match with the crystal system ({self.parameters.cryst[phase_id].crystal_system()})!"
                )
            self.get_hexagonal_symmetry_operators(phase_id)

        elif self.parameters.cryst[phase_id].crystal_system() == "trigonal":
            if self.parameters.cryst[phase_id].spacegroup() and not (
                143 <= self.parameters.cryst[phase_id].spacegroup() <= 167
            ):
                logging.warning(
                    f"spacegroup ({self.parameters.cryst[phase_id].spacegroup()}) does not match with the crystal system ({self.parameters.cryst[phase_id].crystal_system()})!"
                )
            self.get_trigonal_symmetry_operators(phase_id)

        else:
            logging.warning(
                f"Unsupported crystal system: {self.parameters.cryst[phase_id].crystal_system()}"
            )

    def gt_cryst_signed_HKLs(self, hkl, symm=None, phase_id=0):
        """
        Computes a complete list of signed hkl planes by applying symmetry
        operators of the specified space group to the input list of plane families.
        """

        # Ensure hkl is of type double (float)
        hkl = np.asarray(hkl, dtype=float)

        # reflections in rows
        if hkl.shape[0] == 1:
            hkl = hkl.T

        # Load symmetry operators if not provided
        if symm is None:
            symm = self.gt_cryst_get_symm_operators(phase_id)

        num_axes = hkl.shape[0]
        num_indexes = hkl.shape[1]
        num_symm_ops = len(symm)

        # Collect symmetry matrices, falling back to the alternative representation when
        # one of g/g3 is missing (e.g. hexagonal data with 3-index hkl).
        symm_matrices = []
        for op in symm:
            mat = None
            if num_indexes == 4:
                mat = op.g()
                if mat is None and op.g3() is not None:
                    mat = np.eye(4)
                    mat[:3, :3] = op.g3()
            elif num_indexes == 3:
                mat = op.g3()
                if mat is None and op.g() is not None:
                    mat = op.g()[:3, :3]
            else:
                raise ValueError(
                    "gt_cryst_signed_HKLs:wrongSize",
                    "Incorrect size for hkl list...Quitting",
                )

            if mat is None:
                raise ValueError(
                    "gt_cryst_signed_HKLs:missingSymmMatrix",
                    "Symmetry operators are missing matrices compatible with the provided hkl.",
                )
            symm_matrices.append(np.asarray(mat, dtype=float))

        allshkls = []
        allhklinds = []
        mult = []
        hklsp = []
        thtype = []

        # Loop through input hkl types
        for ii in range(num_axes):
            shkls = np.zeros((num_symm_ops * 2, num_indexes))
            tmp_shkl = np.stack([hkl[ii] @ mat for mat in symm_matrices])
            shkls[0::2, :] = tmp_shkl
            shkls[1::2, :] = -tmp_shkl

            # Remove duplicates
            newshkls = np.unique(shkls, axis=0)
            newshkls = newshkls[
                np.lexsort(
                    (
                        -newshkls.T[-num_indexes + 2],
                        -newshkls.T[-num_indexes + 1],
                        -newshkls.T[-num_indexes],
                    )
                )
            ]
            nhkls = newshkls.shape[0] // 2

            # Accumulate results
            mult.append(nhkls * 2)
            allshkls.append(newshkls)
            allhklinds.extend([ii + 1] * nhkls * 2)
            hklsp.append(newshkls[nhkls:])
            thtype.extend([ii + 1] * nhkls)

        # Convert lists to np.ndarrays for output
        allshkls = np.vstack(allshkls)
        allhklinds = np.array(allhklinds)
        mult = np.array(mult)
        hklsp = np.vstack(hklsp)
        thtype = np.array(thtype)

        return allshkls, allhklinds, mult, hklsp, thtype

    def gt_symmetric_reflexions(self, phase_id=0):
        cryst_out = dct_parameter.Cryst()
        hkltypes_used = np.array(self.parameters.cryst[phase_id].hkl(), dtype=float)
        if hkltypes_used.shape[0] == 1:
            hkltypes_used = hkltypes_used.T

        if (
            self.parameters.cryst[phase_id].crystal_system().lower() == "hexagonal"
            and hkltypes_used.shape[0] == 3
        ):
            hkltypes_used = np.vstack(
                [
                    hkltypes_used,
                    hkltypes_used[2, :],
                    -hkltypes_used[0, :] - hkltypes_used[1, :],
                ]
            )

        (
            _,
            _,
            cryst_out.mult.value,
            cryst_out.hklsp.value,
            cryst_out.thetatypesp.value,
        ) = self.gt_cryst_signed_HKLs(
            hkltypes_used, self.parameters.cryst[phase_id].symm
        )

        intensity = []
        for ii in range(len(cryst_out.mult.value)):
            nhkls = cryst_out.mult()[ii] // 2
            intensity.extend([self.parameters.cryst[phase_id].int()[ii]] * int(nhkls))

        # Convert intensity to numpy array
        cryst_out.intsp.value = np.array(intensity)

        # Compute Bmat, dspacingsp, and thetasp
        cryst_out.dspacingsp.value = self.gt_cryst_d_spacing(cryst_out.hklsp().T)
        cryst_out.thetasp.value = self.gt_cryst_theta(cryst_out.dspacingsp())[0]
        cryst_out.symm = self.parameters.cryst[phase_id].symm
        return cryst_out

    def handle_xop_and_symm(self):
        # TODO: Make sure all subfunctions are okay with local_par
        if self.parameters.acq.nof_phases():
            self.parameters.xop = []
            self.parameters.cryst = []
            self.phases_tab.get_selected_files()
            for i in range(self.parameters.acq.nof_phases()):
                # TODO: Error with import from h5
                if self.phases_tab.selected_files[i]["reflection_file"]:
                    self.parameters.xop.append(
                        self.gt_load_reflections_from_file(
                            self.phases_tab.selected_files[i]["reflection_file"]
                        )
                    )
                else:
                    self.parameters.xop.append(dct_parameter.Xop())
                if self.phases_tab.selected_files[i]["cif_file"]:
                    self.parameters.cryst.append(
                        self.gt_load_symm_from_file(
                            self.phases_tab.selected_files[i]["cif_file"]
                        )
                    )
                    self.parameters.cryst[i].name.value = (
                        self.phases_tab.selected_files[i]["name"]
                    )
                    self.parameters.cryst[i].composition.value = (
                        self.phases_tab.selected_files[i]["composition"]
                    )
                    self.parameters.cryst[i].material.value = (
                        self.phases_tab.selected_files[i]["material"]
                    )
                    self.parameters.cryst[i].merge(self.gt_detector_two_theta(i))
                    self.gt_cryst_get_symm_operators(i)
                    self.parameters.cryst[i].merge(self.gt_symmetric_reflexions(i))
                else:
                    logging.warning(
                        "You should load XOP reflection information before proceding with the analysis"
                    )
                    self.parameters.cryst.append(dct_parameter.Cryst())
                logger.info(
                    "Creating directory %s (parents=True, exist_ok=True)",
                    self.parameters.acq.dir() / f"4_grains/phase_{i + 1:02d}",
                )
                os.makedirs(
                    self.parameters.acq.dir() / f"4_grains/phase_{i + 1:02d}",
                    exist_ok=True,
                )

            for i in range(self.parameters.acq.nof_phases()):
                numhkl = len(self.parameters.cryst[i].theta())
                if (
                    self.parameters.cryst[i].usedfam() is None
                    or self.parameters.cryst[i].usedfam() == 0
                ):
                    self.parameters.cryst[i].usedfam.value = [False] * numhkl
                    if numhkl <= 10:
                        self.parameters.cryst[i].usedfam.value[:numhkl] = True
                    else:
                        self.parameters.cryst[i].usedfam.value[:10] = True

    def _snapshot_preprocessing_state(self):
        return self.parameters

    def _restore_preprocessing_state(self, snapshot):
        self.parameters = snapshot

    def _normalize_dataset_configs(self, dataset_configs):
        if dataset_configs is None:
            auto_configs = getattr(
                self.parameters.internal, "multi_dataset_configs", None
            )
            if auto_configs:
                return [dict(config) for config in auto_configs]
            return [{}]
        if isinstance(dataset_configs, dict):
            return [dataset_configs]
        if isinstance(dataset_configs, (list, tuple)):
            normalized = []
            for item in dataset_configs:
                if item is None:
                    normalized.append({})
                elif isinstance(item, dict):
                    normalized.append(item)
                else:
                    raise TypeError(
                        "Each dataset configuration must be a dict or None."
                    )
            return normalized or [{}]
        raise TypeError("dataset_configs must be None, a dict, or a sequence of dicts.")

    def _apply_preprocessing_config(self, config):
        config = config or {}
        raw_path = config.get("raw_path")
        if raw_path is None:
            raw_path = self.parameters.acq.RAW_DATA
        if raw_path is None:
            selection = getattr(
                getattr(self, "dataset_selection_tab", None), "selected_file", None
            )
            if selection is not None:
                raw_path = selection
        if raw_path is None:
            raise ValueError(
                "Raw dataset path is not set. Please select a dataset before preprocessing."
            )
        raw_path = Path(raw_path)
        self.parameters.acq.RAW_DATA = raw_path

        flat_groups = config.get("flat_groups")
        if flat_groups is not None and not isinstance(flat_groups, (list, tuple)):
            flat_groups = [flat_groups]
        if flat_groups:
            flat_groups = [
                self._coerce_int(group, "flat_groups") for group in flat_groups
            ]
            self.parameters.internal.ref_scan_beg = flat_groups[0]
            self.parameters.internal.ref_scan_end = flat_groups[-1]
        else:
            begin_group = self._coerce_int(
                config.get("flat_group_begin"), "flat_group_begin"
            )
            end_group = self._coerce_int(config.get("flat_group_end"), "flat_group_end")
            if begin_group is not None:
                self.parameters.internal.ref_scan_beg = begin_group
            if end_group is not None:
                self.parameters.internal.ref_scan_end = end_group
        if flat_groups is None:
            self.parameters.internal.ref_scan_beg = 1
            self.parameters.internal.ref_scan_end = 3

        dark_group = config.get("dark_groups", config.get("dark_group"))
        if isinstance(dark_group, (list, tuple)):
            dark_group = dark_group[0] if dark_group else None
        dark_group = self._coerce_int(dark_group, "dark_group")
        if dark_group is not None:
            self.parameters.internal.dark_scan = dark_group
        else:
            self.parameters.internal.dark_scan = 4

        proj_group = config.get("projections_group", config.get("proj_group"))
        proj_group = self._coerce_int(proj_group, "projections_group")
        if proj_group is not None:
            self.parameters.internal.proj_scan_dct = proj_group
        else:
            self.parameters.internal.proj_scan_dct = 2

        if "flat_path" in config:
            self.parameters.internal.flat_path = Path(config["flat_path"])
        if "dark_path" in config:
            self.parameters.internal.dark_path = Path(config["dark_path"])

        if self.parameters.acq.RAW_DATA:
            try:
                self.parameters_tab.refresh()
            except Exception:
                logging.debug(
                    "Failed to refresh parameters tab with new configuration",
                    exc_info=True,
                )

        raw_dir = raw_path.parent if raw_path.is_file() else raw_path
        if raw_dir:
            self.parameters.acq.collection_dir_old.value = raw_dir

        dataset_name = config.get("dataset_name")
        processed_path = config.get("processed_path")
        dest_dir = Path(self.parameters.acq.dir())
        if processed_path:
            dest_dir = Path(processed_path)
        elif dataset_name:
            dest_dir = dest_dir.parent / dataset_name
        dataset_name = dataset_name or dest_dir.name

        self.parameters.acq.dir.value = dest_dir
        self.parameters.acq.name.value = dataset_name
        self.parameters.acq.collection_dir.value = dest_dir / "0_rawdata/Orig"
        self.parameters.acq.pair_tablename.value = f"{dataset_name}sportpairs"
        self.parameters.acq.calib_tablename.value = f"{dataset_name}paircalib"

        return dataset_name, dest_dir

    def _clone_parameters_for_processing(self):
        """Deep copy parameters while stripping ipywidget instances that block deepcopy."""
        internal = getattr(self.parameters, "internal", None)
        widget_attrs = []
        if internal is not None:
            for attr, value in list(vars(internal).items()):
                if self._is_ipywidget_instance(value):
                    widget_attrs.append((internal, attr, value))
                    setattr(internal, attr, None)
        try:
            return copy.deepcopy(self.parameters)
        finally:
            for owner, attr, value in widget_attrs:
                setattr(owner, attr, value)

    @staticmethod
    def _is_ipywidget_instance(value):
        if value is None:
            return False
        module_name = getattr(type(value), "__module__", "")
        return module_name.startswith("ipywidgets")

    @staticmethod
    def _coerce_int(value, name):
        if value is None:
            return None
        if isinstance(value, (int, np.integer)):
            return int(value)
        try:
            return int(str(value))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid integer value for '{name}': {value!r}") from exc

    def _run_single_preprocessing(self):
        dest_dir = Path(self.parameters.acq.dir())
        dataset_name = self.parameters.acq.name()

        if (
            not hasattr(self.parameters.internal, "input_parameters")
            or self.parameters.internal.input_parameters is None
        ):
            self.check_distortion()
            self.parameters._init_parameters()
            self.handle_xop_and_symm()

        projections_groups = self._normalize_group_ids(
            self.parameters.acq.projections()
        )
        flat_groups = self._normalize_group_ids(self.parameters.acq.flat())
        dark_groups = self._normalize_group_ids(self.parameters.acq.dark())

        structure_info = None
        entries_by_group: dict[int, dict] = {}
        try:
            structure_info = self.parameters_tab._detect_dataset_structure()
        except Exception:
            logging.debug(
                "Failed to detect dataset structure for preprocessing", exc_info=True
            )
        if structure_info:
            entries = structure_info.get("entries", [])
            entries_by_group = {
                entry.get("group_id"): entry
                for entry in entries
                if entry.get("group_id") is not None
            }

        def _frames_for_group(group_id: int) -> int:
            entry = entries_by_group.get(group_id)
            frames = entry.get("frames") if entry else 0
            try:
                return int(frames)
            except (TypeError, ValueError):
                return 0

        if len(projections_groups) == 1:
            create_DCT_directories(dest_dir, dataset_name)
            self.link_raw_data(
                self.parameters.acq.collection_dir_old(),
                dest_dir / "0_rawdata/Orig",
            )
            self.parameters.save_parameter()
            create_processing_nb_DCT(dest_dir, dataset_name)
            logging.info("Ready for Preprocessing (%s)", dataset_name)
            return [(dataset_name, dest_dir)]

        # Multi-projection case
        results: list[tuple[str, Path]] = []
        base_parent = dest_dir.parent

        original_state = {
            "name": self.parameters.acq.name(),
            "dir": Path(self.parameters.acq.dir()),
            "collection_dir": self.parameters.acq.collection_dir(),
            "pair_tablename": self.parameters.acq.pair_tablename(),
            "calib_tablename": self.parameters.acq.calib_tablename(),
            "projections": self.parameters.acq.projections(),
            "refon": self.parameters.acq.refon(),
            "nproj": self.parameters.acq.nproj(),
            "ndark": self.parameters.acq.ndark(),
            "nref": self.parameters.acq.nref(),
            "dist": self.parameters.acq.dist(),
            "distortion": self.parameters.acq.distortion(),
        }

        for group in projections_groups:
            if group is None:
                continue
            dataset_variant = f"{dataset_name}_{int(group):04d}"
            dest_variant = base_parent / dataset_variant

            self.parameters.acq.dir.value = dest_variant
            self.parameters.acq.name.value = dataset_variant
            self.parameters.acq.collection_dir.value = dest_variant / "0_rawdata/Orig"
            self.parameters.acq.pair_tablename.value = f"{dataset_variant}sportpairs"
            self.parameters.acq.calib_tablename.value = f"{dataset_variant}paircalib"

            create_DCT_directories(dest_variant, dataset_variant)

            groups_to_link: set[int] = set(flat_groups)
            groups_to_link.update(dark_groups)
            groups_to_link.add(group)
            self._link_selected_raw_data(
                groups_to_link, dest_variant / "0_rawdata/Orig"
            )

            proj_frames = _frames_for_group(group)
            if not proj_frames:
                proj_frames = original_state["refon"] or 0

            flat_frames = sum(_frames_for_group(item) for item in flat_groups)
            if not flat_frames:
                flat_frames = original_state["nref"] or 0

            dark_frames = sum(_frames_for_group(item) for item in dark_groups)
            if not dark_frames:
                dark_frames = original_state["ndark"] or 0

            self.parameters.acq.refon.value = proj_frames
            self.parameters.acq.nproj.value = (
                proj_frames // 2 if proj_frames else original_state["nproj"]
            )
            self.parameters.acq.ndark.value = dark_frames

            self.parameters.acq.nref.value = flat_frames

            self.parameters.acq.projections.value = [group]
            self.parameters.save_parameter()
            create_processing_nb_DCT(dest_variant, dataset_variant)
            logging.info("Ready for Preprocessing (%s)", dataset_variant)
            results.append((dataset_variant, dest_variant))

        # Restore original acquisition metadata for UI consistency
        self.parameters.acq.dir.value = original_state["dir"]
        self.parameters.acq.name.value = original_state["name"]
        self.parameters.acq.collection_dir.value = original_state["collection_dir"]
        self.parameters.acq.pair_tablename.value = original_state["pair_tablename"]
        self.parameters.acq.calib_tablename.value = original_state["calib_tablename"]
        self.parameters.acq.projections.value = original_state["projections"]
        self.parameters.acq.refon.value = original_state["refon"]
        self.parameters.acq.nproj.value = original_state["nproj"]
        self.parameters.acq.ndark.value = original_state["ndark"]

        self.parameters.acq.nref.value = original_state["nref"]
        self.parameters.acq.dist.value = original_state["dist"]
        self.parameters.acq.distortion.value = original_state["distortion"]

        return results

    def setup_pre_processing(self, dataset_configs=None):
        configs = self._normalize_dataset_configs(dataset_configs)
        state_snapshot = self._snapshot_preprocessing_state()
        results = []
        self.out_message.clear_output()
        try:
            for config in configs:
                try:
                    self._apply_preprocessing_config(config)
                except ValueError as exc:
                    with self.out_message:
                        display(_html(str(exc), kind="error"))
                    return []
                run_results = self._run_single_preprocessing()
                results.extend(run_results)
        finally:
            self._restore_preprocessing_state(state_snapshot)

        if results:
            with self.out_message:
                for dataset_name, dest_dir in results:
                    display(
                        _html(
                            f"Processing folder created for {dataset_name}. "
                            f"Check the notebook in {dest_dir}.",
                            kind="ok",
                        )
                    )
        return results


if __name__ == "__main__":
    gt_setup = pySetupH5()
    # gt_setup.display()
