import logging as logging
from functools import partial
from importlib.resources import as_file, files

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

from esrf_statusgui.data_managment.dct_parameter import dct_parameter

logger = logging.getLogger(__name__)


class Structure(widgets.VBox):
    def __init__(
        self,
        parameters=None,
        files_by_extension=None,
        on_file_selected_callback=None,
    ):
        super().__init__()
        if parameters is None:
            parameters = dct_parameter()
        self.parameters = parameters
        self._files_by_extension = None  # Private backing field
        self.files_by_extension = files_by_extension  # Uses the setter
        self.selected_file = None
        self.active_button = None
        self.on_file_selected_callback = on_file_selected_callback
        self._init_widgets()
        self._init_layout()
        self.refresh()

    @property
    def files_by_extension(self):
        """Getter for files_by_extension."""
        return self._files_by_extension

    @files_by_extension.setter
    def files_by_extension(self, value):
        """Setter for files_by_extension that normalizes different input types."""
        if value is None:
            self._files_by_extension = None
        elif isinstance(value, str):
            self._files_by_extension = [value]
        elif isinstance(value, (list, tuple, np.ndarray)):
            self._files_by_extension = [f for f in value if f is not None]
        elif isinstance(value, dict):
            # Flatten dictionary values into a single list
            files = []
            for val in value.values():
                if isinstance(val, (list, tuple, np.ndarray)):
                    files.extend([f for f in val if f is not None])
                elif val is not None:
                    files.append(val)
            self._files_by_extension = files
        else:
            raise ValueError(f"Unsupported type for files_by_extension: {type(value)}")

        # Refresh the display whenever files are updated
        if hasattr(self, "files_column"):  # Check if widgets are initialized
            self.refresh()

    def _init_widgets(self):
        """Initialize the widget layout components."""
        self.files_column = widgets.VBox()
        self.file_content = widgets.VBox()
        self.load_content_button = widgets.Button(
            description="Display File Content", button_style="info"
        )
        self.load_content_button.on_click(self.load_file_content)
        self.selected_file_path = widgets.Label(
            value="", layout=widgets.Layout(width="auto")
        )
        self.widgets_map = {"selected_file_path": self.selected_file_path}

    def _init_layout(self):
        """Initialize layout structure."""
        layout = widgets.Layout(width="450px")
        self.children = [
            self.selected_file_path,
            widgets.HBox(
                [
                    widgets.VBox(
                        [widgets.HTML("<h3>Files</h3>"), self.files_column],
                        layout=layout,
                    ),
                    widgets.VBox(
                        [
                            widgets.HTML("<h3>File content</h3>"),
                            self.load_content_button,
                            self.file_content,
                        ],
                        layout=widgets.Layout(
                            width="400px", height="400px", overflow_y="auto"
                        ),
                    ),
                ]
            ),
        ]

    def on_file_click(self, b):
        """Handle file selection logic."""
        if self.active_button:
            self.active_button.button_style = ""
        self.active_button = b
        b.button_style = "success"
        if hasattr(self.parameters.internal, "xop_path"):
            file_path = self.parameters.internal.xop_path / Path(b.description)
            if file_path and file_path.is_file():
                self.selected_file = str(file_path)
                self.selected_file_path.value = f"The selected file is: {file_path}"
                self.file_content.children = [
                    widgets.HTML(value="Click 'Display File Content' to view")
                ]
                if self.on_file_selected_callback:
                    self.on_file_selected_callback(self.selected_file)
        else:
            logging.warning(
                "The code is bound to the ESRF so far. You need access to /data/id11/archive/xop folder for access of cif and csv files"
            )

    def _update_files_column(self):
        """Update file column with available files."""
        self.files_column.children = []  # Clear existing files

        if self.files_by_extension is None:
            return

        # Create buttons for all files
        buttons = [
            widgets.Button(description=f, layout=widgets.Layout(width="auto"))
            for f in self.files_by_extension
        ]
        for btn in buttons:
            btn.on_click(self.on_file_click)
        self.files_column.children = buttons

    def load_file_content(self, _):
        """Load content of the selected file."""
        if self.selected_file:
            content = loadFile(self.selected_file)
            self.file_content.children = [widgets.HTML(value=content.display_struct())]
        else:
            self.file_content.children = [widgets.HTML(value="No file selected")]

    def refresh(self):
        """Refresh file display."""
        self._update_files_column()


class PhaseTab(widgets.VBox):
    def __init__(
        self,
        parameters=None,
        files_by_extension=None,
        on_file_selected_callback=None,
        tab_index=None,
        parent_tab=None,
        check_phases=None,
    ):
        if files_by_extension is None:
            files_by_extension = {}
        super().__init__()
        if parameters is None:
            parameters = dct_parameter()
        self.parameters = parameters
        self.files_by_extension = files_by_extension
        self.on_file_selected_callback = on_file_selected_callback
        self.tab_index = tab_index  # Index of this phase in the parent tab
        self.parent_tab = parent_tab  # Reference to the parent tab widget
        self.phase_complete = False
        self.check_phases = check_phases

        self._init_widgets()
        self._init_layout()
        self._update_accordions()
        self.setup_observers()

    def _init_widgets(self):
        """Initialize phase-related widgets."""
        self.name_input = widgets.Text(description="Name:")
        self.material_input = widgets.Text(description="Material:")
        self.composition_options = sorted(
            set(
                item
                for sublist in [
                    list(value.keys())
                    for key, value in self.files_by_extension.data.items()
                    if key in [".cif", ".csv", ".dat"]
                ]
                for item in sublist
            )
        )
        self.composition_dropdown = widgets.Dropdown(
            options=self.composition_options, description="Composition:"
        )
        self.cif_output = widgets.Accordion()
        self.reflection_output = widgets.Accordion()

    def _init_layout(self):
        """Set the layout of widgets."""
        self.children = [
            self.name_input,
            self.material_input,
            self.composition_dropdown,
            self.cif_output,
            self.reflection_output,
        ]

    def _update_accordions(self):
        """Update the content of accordions based on selected composition."""
        cif_files = self.files_by_extension.get_value(
            f".cif/{self.composition_dropdown.value}", []
        )
        reflection_files = np.append(
            np.array(
                self.files_by_extension.get_value(
                    f".dat/{self.composition_dropdown.value}"
                )
            ),
            np.array(
                self.files_by_extension.get_value(
                    f".csv/{self.composition_dropdown.value}"
                )
            ),
        )
        self.cif_output.children = [
            Structure(
                self.parameters,
                cif_files,
                partial(self.on_file_selected, accordion=self.cif_output),
            )
        ]
        self.reflection_output.children = [
            Structure(
                self.parameters,
                reflection_files,
                partial(self.on_file_selected, accordion=self.reflection_output),
            )
        ]
        self.cif_output.set_title(0, "Select CIF file")
        self.reflection_output.set_title(0, "Select Reflection file")

    def on_file_selected(self, selected_file, accordion):
        """Callback for when a file is selected. Colors the accordion green."""
        if selected_file:
            accordion.layout.border = "2px solid green"
        self.check_phase_completion()

    def setup_observers(self):
        """Observe changes in dropdown selection and input fields."""
        self.composition_dropdown.observe(self.on_compo_change, names="value")
        self.name_input.observe(self.check_phase_completion, names="value")
        self.material_input.observe(self.check_phase_completion, names="value")

    def on_compo_change(self, change):
        """Handle changes in composition selection."""
        self._update_accordions()

    def check_phase_completion(self, _=None):
        is_complete = bool(self.name_input.value and self.material_input.value)
        for accordion in [self.cif_output, self.reflection_output]:
            if accordion.children:
                structure = accordion.children[0]
                is_complete = is_complete and bool(structure.selected_file)

        title = f"Phase {self.tab_index + 1}"
        if is_complete:
            title = f"✓ {title}"
            self.phase_complete = True
            self.check_phases()
        else:
            self.phase_complete = False
        self.parent_tab.set_title(self.tab_index, title)
        return self.phase_complete


class CrystalloTab(widgets.VBox):
    def __init__(self, parameters=None):
        super().__init__()
        PACKAGE = "esrf_statusgui.data_managment"
        with as_file(files(PACKAGE) / "DCT_crystallo.h5") as path:
            self.xops_files = Path(path)
        if parameters is None:
            parameters = dct_parameter()
        self.parameters = parameters
        self.all_phases_completion = widgets.Checkbox(value=False)
        self.files_by_extension = {}
        self.phase_completion = []
        self.selected_files = []
        self.read_xops_struct()
        self._init_widgets()
        self._init_phases()

    def _init_widgets(self):
        self.status_label = widgets.Label(
            value="Ready", layout=widgets.Layout(width="auto")
        )
        self.reset_db = widgets.Button(
            description="Reset db", layout=widgets.Layout(width="auto")
        )
        self.reset_db.on_click(self.populate_files_by_extension)
        self.phase_tab = widgets.Tab()

    def _init_phases(self):
        """Create tabs for each phase."""
        if self.parameters.acq.nof_phases():
            self.phase_completion = [False] * self.parameters.acq.nof_phases()
            if not self.phase_tab.children:
                children = []
                for i in range(self.parameters.acq.nof_phases()):
                    children.append(
                        PhaseTab(
                            self.parameters,
                            self.files_by_extension,
                            on_file_selected_callback=partial(
                                self.on_file_selected, phase_index=i
                            ),
                            tab_index=i,
                            parent_tab=self.phase_tab,
                            check_phases=self.check_all_phases_completion,
                        )
                    )
            else:
                children = list(self.phase_tab.children)
                if len(children) >= self.parameters.acq.nof_phases():
                    children = children[0 : self.parameters.acq.nof_phases()]
                else:
                    for i in range(len(children), self.parameters.acq.nof_phases()):
                        children.append(
                            PhaseTab(
                                self.parameters,
                                self.files_by_extension,
                                on_file_selected_callback=partial(
                                    self.on_file_selected, phase_index=i
                                ),
                                tab_index=i,
                                parent_tab=self.phase_tab,
                                check_phases=self.check_all_phases_completion,
                            )
                        )
            self.phase_tab.children = children
            for i in range(self.parameters.acq.nof_phases()):
                self.phase_tab.set_title(i, f"Phase {i + 1}")
            self.build_widget()

    def build_widget(self):
        self.children = [
            widgets.HBox(
                children=([self.status_label, self.reset_db]),
                layout=widgets.Layout(
                    width="400px", justify_content="space-between", display="flex"
                ),
            ),
            self.phase_tab,
        ]

    def read_xops_struct(self):
        if self.xops_files.exists():
            self.files_by_extension = loadFile(self.xops_files)
        else:
            self.populate_files_by_extension()

    def populate_files_by_extension(self):
        """Populate files grouped by their extensions."""
        xop_path = Path(self.parameters.internal.xop_path)
        self.files_by_extension = {}
        for file_path in xop_path.rglob("*"):
            try:
                if file_path.is_file():
                    extension = file_path.suffix
                    self.files_by_extension.setdefault(extension, {}).setdefault(
                        file_path.stem, []
                    ).append(file_path.relative_to(xop_path).as_posix())
            except Exception:
                logger.warning("The path %s is not accessible", file_path)
        from silx.io.dictdump import dicttoh5

        dicttoh5(self.files_by_extension, str(self.xops_files), mode="w")

    def on_file_selected(self, selected_file, phase_index):
        """Callback to handle file selection for each phase."""
        self.phase_completion[phase_index] = bool(selected_file)
        self.check_all_phases_completion()

    def check_all_phases_completion(self):
        if all(tab.phase_complete for tab in self.phase_tab.children):
            self.all_phases_completion.value = True

    def get_selected_files(self):
        """Retrieve selected files from each PhaseTab."""
        self.selected_files = []

        # Iterate through each PhaseTab in the CrystalloTab
        for phase_index, phase_tab in enumerate(self.phase_tab.children):
            # Access the Structure in the CIF and Reflection accordions
            cif_structure = phase_tab.cif_output.children[0]
            reflection_structure = phase_tab.reflection_output.children[0]
            name = phase_tab.name_input.value
            material = phase_tab.material_input.value
            composition = phase_tab.composition_dropdown.value

            # Get selected files from both CIF and Reflection structures
            cif_selected_file = (
                cif_structure.selected_file if cif_structure.selected_file else None
            )
            reflection_selected_file = (
                reflection_structure.selected_file
                if reflection_structure.selected_file
                else None
            )

            # Append the selected files for this phase
            self.selected_files.append(
                {
                    "phase_index": phase_index,
                    "cif_file": cif_selected_file,
                    "reflection_file": reflection_selected_file,
                    "name": name,
                    "material": material,
                    "composition": composition,
                }
            )

        return self.selected_files

    def refresh(self):
        """Refresh the tab contents."""
        self.create_phase_tabs()

    def get_tab(self):
        return self


if __name__ == "__main__":
    test = CrystalloTab()
    print(test.files_by_extension.get_keys())
