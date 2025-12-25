from __future__ import annotations

import logging

import ipywidgets as widgets
from esrf_pathlib import ESRFPath as Path

from esrf_statusgui.brain.dct_experiment_logic import DCTExperimentSelectionLogic
from esrf_statusgui.data_managment.dct_parameter import dct_parameter

logger = logging.getLogger(__name__)


class WelcomeTab(widgets.VBox):
    def __init__(self, parameters=None):
        if parameters is None:
            parameters = dct_parameter()
        super().__init__()
        self.parameters = parameters
        self.logic = DCTExperimentSelectionLogic(self.parameters.internal.base_path)
        seed = parameters.internal.exp_list or []
        self.exp_list = self.logic.list_experiments(seed)
        self.manual_root: Path | None = None
        self.layout_dropdown = parameters.internal.layout or widgets.Layout()
        self.create_widgets()
        self.setup_observers()

    def create_widgets(self):
        self.widget_exp_select = widgets.Combobox(
            options=sorted(self.exp_list),
            description="Select the name of the experiment:",
        )
        self.widget_beamline_dropdown = widgets.Dropdown(
            description="Select the beamline of the experiment"
        )
        self.widget_experiment_date = widgets.Dropdown(
            description="Select the date of the experiment"
        )
        self.manual_root_input = widgets.Text(
            value="",
            description="Manual RAW path:",
            placeholder="e.g. /data/visitor/maXXXX/idXX/20240101/RAW_DATA",
        )
        self.manual_root_button = widgets.Button(description="Use path")
        self.status_label = widgets.Label(value="")
        self.children = [
            widgets.HTML("<p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>"),
            widgets.HTML(
                "<p>~&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Welcome to Grain Tracking at the ESRF!&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;~</p>"
            ),
            widgets.HTML("<p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>"),
            self.widget_exp_select,
            self.widget_beamline_dropdown,
            self.widget_experiment_date,
            widgets.HBox([self.manual_root_input, self.manual_root_button]),
            self.status_label,
        ]
        for widget in [
            self.widget_exp_select,
            self.widget_beamline_dropdown,
            self.widget_experiment_date,
        ]:
            widget.layout = self.layout_dropdown
            widget.style = {"description_width": "400px"}
        self.manual_root_input.layout = self.layout_dropdown
        self.manual_root_input.style = {"description_width": "200px"}

    def setup_observers(self):
        self.widget_exp_select.observe(self.update_beamline_options, names="value")
        self.widget_beamline_dropdown.observe(
            self.update_experiment_date_options, names="value"
        )
        for widget in [
            self.widget_exp_select,
            self.widget_beamline_dropdown,
            self.widget_experiment_date,
        ]:
            widget.observe(self.check_completion, names="value")
        self.manual_root_button.on_click(self.on_manual_root_submit)

    def update_beamline_options(self, change):
        if not change.get("new"):
            self.widget_beamline_dropdown.options = ()
            self.widget_beamline_dropdown.value = None
            self.widget_experiment_date.options = ()
            self.widget_experiment_date.value = None
            return

        experiment = self.widget_exp_select.value
        try:
            beamline_folders = self.logic.list_beamlines(experiment)
        except FileNotFoundError:
            logger.warning("Experiment folder not found: %s", experiment)
            beamline_folders = []
        except OSError as exc:
            logger.warning("Cannot list beamlines for %s: %s", experiment, exc)
            beamline_folders = []

        self.widget_beamline_dropdown.options = beamline_folders
        self.widget_beamline_dropdown.value = None
        self.widget_experiment_date.options = ()
        self.widget_experiment_date.value = None

        if len(beamline_folders) == 1:
            self.widget_beamline_dropdown.value = beamline_folders[0]

    def update_experiment_date_options(self, change):
        if not change.get("new"):
            self.widget_experiment_date.options = ()
            self.widget_experiment_date.value = None
            return

        experiment = self.widget_exp_select.value
        beamline = self.widget_beamline_dropdown.value
        if not experiment or not beamline:
            return

        try:
            date_folders = self.logic.list_dates(experiment, beamline)
        except FileNotFoundError:
            logger.warning(
                "Beamline folder not found for experiment %s, beamline %s",
                experiment,
                beamline,
            )
            date_folders = []
        except OSError as exc:
            logger.warning(
                "Cannot list experiment dates for %s/%s: %s", experiment, beamline, exc
            )
            date_folders = []

        self.widget_experiment_date.options = date_folders
        self.widget_experiment_date.value = None
        if len(date_folders) == 1:
            self.widget_experiment_date.value = date_folders[0]

    def check_completion(self, _=None):
        if self.manual_root:
            return True
        return all(
            widget.value
            for widget in [
                self.widget_exp_select,
                self.widget_beamline_dropdown,
                self.widget_experiment_date,
            ]
        )

    def on_manual_root_submit(self, _btn=None) -> None:
        raw_value = (self.manual_root_input.value or "").strip()
        if not raw_value:
            self.status_label.value = "Enter a path inside RAW_DATA."
            self.manual_root = None
            return

        candidate = Path(raw_value).expanduser()
        if not candidate.exists():
            self.status_label.value = f"Path not found: {candidate}"
            self.manual_root = None
            return
        if not candidate.is_dir():
            self.status_label.value = f"Not a directory: {candidate}"
            self.manual_root = None
            return

        self.manual_root = candidate
        # Clear combo selections to avoid conflicts with manual override
        self.widget_exp_select.value = ""
        self.widget_beamline_dropdown.options = ()
        self.widget_beamline_dropdown.value = None
        self.widget_experiment_date.options = ()
        self.widget_experiment_date.value = None
        self.status_label.value = f"Manual RAW path set: {candidate}"
        self.check_completion()

    def get_tab(self):
        return self
