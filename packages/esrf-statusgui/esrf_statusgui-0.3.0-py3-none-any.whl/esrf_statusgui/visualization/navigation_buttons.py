import logging
import os

import ipywidgets as widgets
from esrf_pathlib import ESRFPath as Path
from IPython.display import display

from esrf_statusgui.file_utils.paths import describe

logger = logging.getLogger(__name__)


class Navigation:
    def __init__(self, tabs, parameters, setup_preprocessing):
        self.tabs = tabs
        self.parameters = parameters
        self.setup_preprocessing = setup_preprocessing
        self.prev_button = widgets.Button(description="Previous")
        self.next_button = widgets.Button(description="Next", disabled=True)
        self.prev_button.on_click(self.on_prev_button_clicked)
        self.next_button.on_click(self.on_next_button_clicked)
        self.nav_buttons = widgets.HBox([self.prev_button, self.next_button])
        self.confirmation_output = widgets.Output()
        self.main_layout = widgets.VBox([self.nav_buttons, self.confirmation_output])

    def on_prev_button_clicked(self, _):
        if self.tabs.selected_index > 0:
            self.tabs.selected_index -= 1

    def on_next_button_clicked(self, _):
        if self.tabs.selected_index < len(self.tabs.children) - 1:
            self.tabs.selected_index += 1
        elif self.tabs.selected_index == len(self.tabs.children) - 1:
            self.show_confirmation_dialog()

    def show_confirmation_dialog(self):
        self.confirmation_output.clear_output()
        with self.confirmation_output:
            # Create confirmation buttons
            yes_button = widgets.Button(description="Yes", button_style="success")
            no_button = widgets.Button(description="No", button_style="danger")

            # Define button callbacks
            def on_yes_clicked(_):
                self.setup_preprocessing()  # Call setup_pre_processing if confirmed
                self.confirmation_output.clear_output()  # Clear dialog after confirmation
                user = os.environ.get("USER", "default_user")
                symlink_folder = "Experiments"
                info = describe(self.parameters.acq.dir())
                relative_path = info.relative_to_root
                experiment = info.proposal or (
                    relative_path.parts[0] if relative_path.parts else ""
                )
                try:
                    experiments_root = Path.home() / symlink_folder
                    if not experiments_root.exists():
                        logger.info(
                            "Creating directory %s (parents=True, exist_ok=True)",
                            experiments_root,
                        )
                        os.makedirs(experiments_root, exist_ok=True)
                    experiment_link = (
                        experiments_root / experiment if experiment else None
                    )
                    if experiment and (
                        experiment_link is not None and not experiment_link.exists()
                    ):
                        experiment_link.symlink_to(info.data_root / experiment)
                    logging.info(
                        f"https://jupyter-slurm.esrf.fr/user/{user}/notebooks/{symlink_folder}/{relative_path.as_posix()}"
                    )
                except Exception as exc:
                    logging.info(
                        "The post-treatment ipynb was created in your experiment folder, into SCRIPTS. "
                        "Link creation failed: %s",
                        exc,
                    )

            def on_no_clicked(_):
                self.confirmation_output.clear_output()  # Just close dialog without action

            # Attach callbacks
            yes_button.on_click(on_yes_clicked)
            no_button.on_click(on_no_clicked)

            # Display the confirmation message and buttons
            display(
                widgets.VBox(
                    [
                        widgets.Label("Are you sure you want to start pre-processing?"),
                        widgets.HBox([yes_button, no_button]),
                    ]
                )
            )

    def get_navigation(self):
        return self.main_layout
