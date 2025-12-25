from __future__ import annotations

# mypy: allow-untyped-defs
import time
from pathlib import Path
from types import SimpleNamespace

import ipywidgets as widgets
import pytest

from esrf_statusgui.visualization import statusGUI as status_gui


@pytest.fixture
def tab_with_logic(monkeypatch):
    instances: list[FakeLogic] = []

    def fake_get_root() -> Path:
        return Path("/visitor")

    monkeypatch.setattr(status_gui, "get_visitor_root", fake_get_root)

    class FakeLogic:
        def __init__(self, base_path, method_factories):
            self.base_path = Path(base_path)
            self.method_factories = method_factories
            self.root_folder = Path("/visitor/exp0/RAW_DATA")
            self.datasets_for_path: dict[str, dict[str, list[SimpleNamespace]]] = {}
            self.last_refresh: tuple[SimpleNamespace, object] | None = None
            self.last_select: tuple[str, str] | None = None
            self.last_beamlines_arg: str | None = None
            self.last_ensure: Path | None = None
            self.last_datasets_path: str | None = None
            instances.append(self)

        def list_experiments(self) -> list[str]:
            return ["expB", "expA"]

        def list_beamlines(self, experiment: str) -> list[str]:
            self.last_beamlines_arg = experiment
            return ["bm1", "bm2"]

        def select_experiment(self, experiment: str, beamline: str) -> None:
            self.last_select = (experiment, beamline)
            self.root_folder = Path(f"/visitor/{experiment}/{beamline}/RAW_DATA")

        def ensure_node(self, path: Path) -> SimpleNamespace:
            self.last_ensure = Path(path)
            return SimpleNamespace(path=str(path), children=[])

        def datasets_by_path(self, path: Path) -> dict[str, list[SimpleNamespace]]:
            self.last_datasets_path = str(path)
            return self.datasets_for_path.get(self.last_datasets_path, {})

        def refresh_dataset(
            self, dataset: SimpleNamespace, method_factory: object | None
        ) -> None:
            self.last_refresh = (dataset, method_factory)

        def refresh_all(self) -> None:  # pragma: no cover - not exercised here
            pass

    monkeypatch.setattr(status_gui, "DatasetSelectionLogic", FakeLogic)

    tab = status_gui.DatasetSelectionTab()
    logic = instances[-1]
    return tab, logic


def test_dataset_selection_tab_initialises_logic(tab_with_logic):
    tab, logic = tab_with_logic

    assert logic.base_path == Path("/visitor")
    assert set(logic.method_factories) == {"PCT", "s3DXRD", "DCT", "FF"}
    assert list(tab.widget_exp_select.options) == ["expA", "expB"]
    assert logic.last_ensure == logic.root_folder

    root_buttons = tab.tree.children
    assert root_buttons == ()


def test_update_root_folder_selects_experiment(tab_with_logic):
    tab, logic = tab_with_logic

    tab.widget_exp_select.value = "expA"
    tab.update_beamline_options()
    assert logic.last_beamlines_arg == "expA"
    assert list(tab.widget_beamline_dropdown.options) == ["bm1", "bm2"]

    tab._last_change_ts = time.time()
    tab.widget_beamline_dropdown.value = "bm1"
    tab.update_root_folder({"new": True})

    assert logic.last_select == ("expA", "bm1")
    assert logic.last_ensure == logic.root_folder
    assert tab.status_label.value == "Ready..."
    root_node = logic.ensure_node(logic.root_folder)
    root_node.children = [SimpleNamespace(name="sample", is_file=False)]
    tab.update_tree(root_node)
    assert tab.tree.children[0].description == "sample"


def test_refresh_dataset_delegates_to_logic(tab_with_logic):
    tab, logic = tab_with_logic
    dataset = SimpleNamespace(dataset="sample", method="DCT")

    tab.refresh_dataset(dataset)

    assert logic.last_refresh is not None
    refreshed_dataset, factory = logic.last_refresh
    assert refreshed_dataset is dataset
    assert factory is logic.method_factories["DCT"]


def test_update_tree_builds_method_accordions(tab_with_logic):
    tab, logic = tab_with_logic
    dataset = SimpleNamespace(dataset="ds1", method="DCT", processing_state=[])
    logic.datasets_for_path[str(logic.root_folder)] = {"DCT": [dataset]}

    node = SimpleNamespace(
        path=str(logic.root_folder),
        children=[SimpleNamespace(name="sample", is_file=False)],
    )
    tab.update_tree(node)

    assert len(tab.dct.children) == 1
    accordion: widgets.Accordion = tab.dct.children[0]
    assert accordion.get_title(0) == "ds1"
    assert tab.dataset_to_widget[("DCT", "ds1")] is accordion
    assert tab.dataset_to_widget["ds1"] is accordion
