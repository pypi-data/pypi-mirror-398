from __future__ import annotations

import logging
from collections.abc import Iterable

import ipywidgets as widgets
from esrf_pathlib import ESRFPath as Path

from esrf_statusgui.brain.dct_dataset_browser import (
    DCTDatasetBrowserLogic,
    DirectoryInfo,
    FileInfo,
    unique_suffixes,
)
from esrf_statusgui.data_managment.dct_parameter import dct_parameter

logger = logging.getLogger(__name__)


class DatasetSelectionTab(widgets.VBox):
    def __init__(self, parameters=None):
        if parameters is None:
            parameters = dct_parameter()
        super().__init__()
        self.parameters = parameters
        self.selected_file: Path | None = None
        self.h5_files_visible = False
        self.other_files_visible = False
        self.active_button: widgets.Button | None = None
        self._current_other_files: list[FileInfo] = []

        self.browser_logic = DCTDatasetBrowserLogic(self.parameters.acq.RAW_DATA)

        self._init_widgets()
        self._init_layout()

        if self.browser_logic.current_folder:
            self.browser_logic.ensure_cache()
            self.create_tree_view()
            self.create_breadcrumbs()

    # ------------------------------------------------------------------ #
    # UI setup
    # ------------------------------------------------------------------ #
    def _init_widgets(self) -> None:
        self.tree = widgets.VBox()
        self.h5_column = widgets.VBox()
        self.other_files_column = widgets.VBox()
        self.file_content = widgets.VBox()
        self.breadcrumbs = widgets.HBox()

        self.h5_button = widgets.Button(
            description="Show H5 Files", button_style="info"
        )
        self.other_files_button = widgets.Button(
            description="Show Other Files", button_style="info"
        )

        self.status_label = widgets.Label(
            value="Ready", layout=widgets.Layout(width="auto")
        )
        self.selected_file_path = widgets.Label(
            value="", layout=widgets.Layout(width="auto")
        )
        self.extension_filter = widgets.SelectMultiple(
            options=(),
            value=(),
            layout=widgets.Layout(width="170px", height="100px", overflow_y="auto"),
        )
        self.load_content_button = widgets.Button(
            description="Display File Content", button_style="info"
        )

        self.h5_button.on_click(self.toggle_h5_files)
        self.other_files_button.on_click(self.toggle_other_files)
        self.load_content_button.on_click(self.load_file_content)
        self.extension_filter.observe(self._filter_other_files, names="value")

    def _init_layout(self) -> None:
        layout = widgets.Layout(width="200px")
        self.children = [
            self.status_label,
            self.breadcrumbs,
            widgets.HBox([self.h5_button, self.other_files_button]),
            widgets.HBox(
                [
                    widgets.VBox(
                        [widgets.HTML("<h3>Folder Tree</h3>"), self.tree], layout=layout
                    ),
                    widgets.VBox(
                        [widgets.HTML("<h3>H5 DCT files</h3>"), self.h5_column],
                        layout=layout,
                    ),
                    widgets.VBox(
                        [
                            widgets.HTML("<h3>Other Files</h3>"),
                            self.extension_filter,
                            self.other_files_column,
                        ],
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
            self.selected_file_path,
        ]

    # ------------------------------------------------------------------ #
    # Tree handling
    # ------------------------------------------------------------------ #
    def create_tree_view(self) -> None:
        current_folder = self.browser_logic.current_folder
        if current_folder:
            root_button = widgets.Button(
                description=str(current_folder), layout=widgets.Layout(width="auto")
            )
            root_button._target_path = current_folder  # type: ignore[attr-defined]
            root_button.on_click(self.on_folder_click)
            self.tree.children = (root_button,)
            self.update_tree(current_folder)
            self.update_files_columns(current_folder)

    def on_folder_click(self, button: widgets.Button) -> None:
        target = getattr(button, "_target_path", None)
        if target is None:
            base = self.browser_logic.current_folder or Path()
            target = base / button.description
        target_path = Path(target)
        if not target_path.is_dir():
            logger.debug("Ignoring folder click on non-directory: %s", target_path)
            return
        self.browser_logic.set_current_folder(target_path)
        self.parameters.acq.RAW_DATA = target_path
        self.update_tree(target_path)
        self.create_breadcrumbs()
        self.file_content.children = ()
        self.update_files_columns(target_path)

    def update_tree(self, folder: Path | str | None) -> None:
        directories: Iterable[DirectoryInfo] = self.browser_logic.list_directories(
            folder
        )
        folders: list[widgets.Button] = []
        h5_count = 0
        for info in directories:
            btn = widgets.Button(
                description=info.name,
                layout=widgets.Layout(width="auto"),
            )
            btn.style.button_color = "lightgreen" if info.has_dct_h5 else "lightgray"
            btn._target_path = info.path  # type: ignore[attr-defined]
            btn.on_click(self.on_folder_click)
            folders.append(btn)
            if info.has_dct_h5:
                h5_count += 1
        self.tree.children = tuple(folders)
        if folders:
            folder_names = ", ".join(info.name for info in directories)
        else:
            folder_names = "<none>"
        self.status_label.value = (
            f"Loaded {len(folders)} folders (H5-ready: {h5_count})."
        )
        logger.debug(
            "DatasetSelectionTab.update_tree -> %s | H5 directories: %s",
            folder_names,
            h5_count,
        )

    # ------------------------------------------------------------------ #
    # File listings
    # ------------------------------------------------------------------ #
    def update_files_columns(self, folder: Path | str | None) -> None:
        folder_path = Path(folder) if folder else self.browser_logic.current_folder
        if folder_path is None:
            return
        self.status_label.value = "Refreshing..."
        h5_files = self.browser_logic.list_dct_h5_files(folder_path)
        other_files = self.browser_logic.list_other_files(folder_path)
        self._update_dct_h5_column(h5_files)
        self._update_other_files_column(other_files)
        self.status_label.value = "Ready..."

    def _update_dct_h5_column(self, files: list[FileInfo]) -> None:
        if self.h5_files_visible:
            buttons = []
            for info in files:
                btn = widgets.Button(
                    description=info.name, layout=widgets.Layout(width="auto")
                )
                btn._target_path = info.path  # type: ignore[attr-defined]
                btn.on_click(self.on_file_click)
                buttons.append(btn)
            self.h5_column.children = tuple(buttons)
        else:
            self.h5_column.children = ()

    def _update_other_files_column(self, files: list[FileInfo]) -> None:
        self._current_other_files = files
        if not self.other_files_visible:
            self.extension_filter.unobserve(self._filter_other_files, names="value")
            self.extension_filter.options = ()
            self.extension_filter.value = ()
            self.extension_filter.observe(self._filter_other_files, names="value")
            self.other_files_column.children = ()
            return

        suffixes = unique_suffixes(files)
        self.extension_filter.unobserve(self._filter_other_files, names="value")
        self.extension_filter.options = tuple(suffixes)
        if suffixes:
            current_selection = tuple(
                value for value in self.extension_filter.value if value in suffixes
            )
            if not current_selection:
                current_selection = tuple(suffixes)
            self.extension_filter.value = current_selection
        else:
            self.extension_filter.value = ()
        self.extension_filter.layout = widgets.Layout(
            width="170px",
            height=f"{min(20 * max(len(self.extension_filter.options), 1), 100)}px",
            overflow_y="auto",
        )
        self.extension_filter.observe(self._filter_other_files, names="value")
        self._filter_other_files({"new": self.extension_filter.value})

    def _filter_other_files(self, change, files: list[FileInfo] | None = None) -> None:
        files = files if files is not None else self._current_other_files
        selection = change.get("new") if isinstance(change, dict) else None
        if not selection:
            selected_suffixes = set(unique_suffixes(files))
        else:
            selected_suffixes = set(selection)

        buttons = []
        for info in files:
            suffix = info.suffix or ""
            if not selected_suffixes or suffix in selected_suffixes:
                btn = widgets.Button(
                    description=info.name, layout=widgets.Layout(width="auto")
                )
                btn._target_path = info.path  # type: ignore[attr-defined]
                btn.on_click(self.on_file_click)
                buttons.append(btn)
        self.other_files_column.children = tuple(buttons)

    # ------------------------------------------------------------------ #
    # File interactions
    # ------------------------------------------------------------------ #
    def toggle_other_files(self, _button) -> None:
        self._toggle_files(self.other_files_button, "other_files_visible")

    def toggle_h5_files(self, _button) -> None:
        self._toggle_files(self.h5_button, "h5_files_visible")

    def _toggle_files(self, button: widgets.Button, attribute: str) -> None:
        setattr(self, attribute, not getattr(self, attribute))
        button.button_style = "success" if getattr(self, attribute) else "info"
        target_folder = (
            self.parameters.acq.RAW_DATA or self.browser_logic.current_folder
        )
        if target_folder:
            self.update_files_columns(target_folder)

    def on_file_click(self, button: widgets.Button) -> None:
        target_path = getattr(button, "_target_path", None)
        if target_path is None:
            logger.debug("Ignoring file click without target path.")
            return
        file_path = Path(target_path)
        if self.active_button:
            self.active_button.button_style = ""
        self.active_button = button
        button.button_style = "success"
        self.selected_file = file_path
        self.selected_file_path.value = f"The selected file is: {file_path}"
        self.file_content.children = (
            widgets.HTML(value="Click 'Display File Content' to view"),
        )

    def load_file_content(self, _button) -> None:
        if not self.selected_file:
            self.file_content.children = (widgets.HTML(value="No file selected"),)
            return

        struct = self.browser_logic.load_file_struct(self.selected_file)
        if struct is None:
            message = f"Unable to read file: {self.selected_file}"
            logger.warning(message)
            self.file_content.children = (widgets.HTML(value=message),)
        else:
            self.file_content.children = (widgets.HTML(value=struct),)

    # ------------------------------------------------------------------ #
    # Breadcrumbs
    # ------------------------------------------------------------------ #
    def create_breadcrumbs(self) -> None:
        current_folder = self.browser_logic.current_folder
        if current_folder is None:
            self.breadcrumbs.children = ()
            return

        path_parts = Path(current_folder).parts
        links = [
            self._create_breadcrumb_button(Path(*path_parts[: i + 1]))
            for i in range(len(path_parts))
        ]
        self.breadcrumbs.children = tuple(links)

    def _create_breadcrumb_button(self, path: Path) -> widgets.Button:
        button = widgets.Button(
            description=(path.name or str(path)), layout=widgets.Layout(width="auto")
        )
        button._target_path = path  # type: ignore[attr-defined]
        button.on_click(self.on_breadcrumb_click(path))
        return button

    def on_breadcrumb_click(self, path: Path):
        def handle_click(_button) -> None:
            self.browser_logic.set_current_folder(path)
            self.parameters.acq.RAW_DATA = path
            self.update_tree(path)
            self.create_breadcrumbs()
            self.file_content.children = ()
            self.update_files_columns(path)

        return handle_click

    # ------------------------------------------------------------------ #
    # Refresh / public API
    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        raw_data_root = self.parameters.acq.RAW_DATA
        if raw_data_root:
            self.browser_logic.set_current_folder(raw_data_root)
        self.status_label.value = "Refreshing..."
        node = self.browser_logic.refresh()
        folder = self.browser_logic.current_folder
        if node is None or folder is None:
            self.status_label.value = "Ready..."
            return
        self.parameters.acq.RAW_DATA = folder
        self.update_tree(folder)
        self.create_breadcrumbs()
        self.update_files_columns(folder)
        self.status_label.value = "Ready..."

    def get_tab(self) -> DatasetSelectionTab:
        return self


if __name__ == "__main__":
    tab = DatasetSelectionTab()
