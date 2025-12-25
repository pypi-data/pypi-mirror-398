from datetime import date, datetime
from types import SimpleNamespace

# mypy: allow-untyped-defs
import ipywidgets as widgets
import pytest

from esrf_statusgui.visualization import statusGUI as status_gui


class DummyDataset:
    """Convenience stub for ProcessedPathAccordeon tests."""

    def __init__(self, sample=None, processing_state=None):
        self.sample = sample
        self.dataset = "dataset_001"
        self.processing_state = processing_state if processing_state is not None else []


@pytest.fixture
def int_slider():
    return widgets.IntSlider()


def test_is_date_parses_valid_and_invalid_strings():
    parsed = status_gui.is_date("20240210")
    assert isinstance(parsed, datetime)
    assert parsed.year == 2024 and parsed.month == 2 and parsed.day == 10
    assert status_gui.is_date("not-a-date") is None


def _make_component(**overrides):
    defaults = dict(
        statusFilesLaunched=False,
        filesOk=False,
        statusDetailedLaunched=False,
        detailedOk=False,
        visualize=False,
        target_files=[],
        print_status=lambda: ["OK"],
        print_errors=lambda: ["ERR"],
        print_status_details=lambda: ["DETAIL"],
        loadStatusDetailed=lambda: None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_nkey_enables_natural_sort_order():
    names = ["sample_10", "sample_2", "sample_1"]
    ordered = sorted(names, key=status_gui._nkey)
    assert ordered == ["sample_1", "sample_2", "sample_10"]


def test_as_children_flattens_nested_iterables():
    label = widgets.Label("hello")
    nested = [label, [widgets.Label("inner")], None]
    children = status_gui._as_children(nested)
    assert len(children) == 2
    assert all(isinstance(child, widgets.Widget) for child in children)


def test_as_children_logs_non_widget_entries(caplog):
    caplog.set_level("WARNING")
    label = widgets.Label("ok")
    children = status_gui._as_children([label, object()])
    assert children == (label,)
    assert "Ignoring non-widget" in caplog.text


def test_safe_reobserve_is_idempotent_for_single_trait(int_slider):
    collected = []

    def handler(change):
        collected.append(change["new"])

    for _ in range(3):
        status_gui._safe_reobserve(int_slider, handler, names="value")

    start = int_slider.value
    for step in range(1, 4):
        int_slider.value = start + step

    assert collected == [start + 1, start + 2, start + 3]


def test_safe_reobserve_supports_iterable_names(int_slider):
    calls = []

    def handler(change):
        calls.append(change["new"])

    status_gui._safe_reobserve(int_slider, handler, names=("value",))
    status_gui._safe_reobserve(int_slider, handler, names=("value",))

    int_slider.value += 1
    assert calls == [int_slider.value]


def test_safe_reobserve_accepts_none_names(int_slider):
    calls = []

    def handler(change):
        calls.append(change["new"])

    status_gui._safe_reobserve(int_slider, handler, names=None)
    status_gui._safe_reobserve(int_slider, handler, names=None)

    start = int_slider.value
    int_slider.value = start + 1
    int_slider.value = start + 2

    assert calls == [start + 1, start + 2]


def test_processed_path_accordeon_post_process_triggers_refresh(monkeypatch):
    class FakePostProcess:
        def __init__(self, dataset):
            self.dataset = dataset

        def export_widget(self):
            return widgets.Label("Post process UI")

    dummy_sample = SimpleNamespace(raw_path=["/raw"], processed_path=["/proc"])
    dataset = DummyDataset(sample=dummy_sample)

    class Controller:
        def __init__(self):
            self.calls = []

        def refresh_dataset(self, dataset_arg, method_arg):
            self.calls.append((dataset_arg, method_arg))

    controller = Controller()
    method = object()

    monkeypatch.setattr(status_gui, "Post_process", FakePostProcess)

    accord = status_gui.ProcessedPathAccordeon(
        dataset, controller=controller, method=method
    )

    widget = accord.post_process()
    assert isinstance(widget, widgets.VBox)
    toolbar = widget.children[0]
    assert isinstance(toolbar, widgets.HBox)
    refresh_button = toolbar.children[0]
    refresh_button.click()
    assert controller.calls == [(dataset, method)]


def test_processed_path_accordeon_builds_accordion_for_processing_state():
    component = SimpleNamespace(
        statusFilesLaunched=True,
        filesOk=True,
        print_status=lambda: ["All good"],
        print_errors=lambda: ["Error"],
        print_status_details=lambda: ["Detail"],
        visualize=False,
        statusDetailedLaunched=True,
        target_files=[],
    )
    processing_state = SimpleNamespace(
        components=[(component, None, "Step A")],
        main_path=SimpleNamespace(session_date="20240101"),
    )
    dataset = DummyDataset(processing_state=[processing_state])

    accord = status_gui.ProcessedPathAccordeon(dataset)

    assert len(accord.children) == 1
    date_accordion = accord.children[0]
    assert isinstance(date_accordion, widgets.Accordion)
    assert date_accordion.get_title(0) == "20240101"


def test_on_date_open_populates_components():
    component = _make_component(statusFilesLaunched=True, filesOk=True)
    processing_state = SimpleNamespace(
        components=[(component, None, "Step A")],
        main_path=SimpleNamespace(session_date="20240101"),
    )
    dataset = DummyDataset(processing_state=[processing_state])
    accord = status_gui.ProcessedPathAccordeon(dataset)

    date_accordion = accord.children[0]
    assert isinstance(date_accordion, widgets.Accordion)

    change = {"name": "selected_index", "new": 0}
    accord._on_date_open(change, processing_state, date_accordion, dataset)

    assert isinstance(date_accordion.children[0], widgets.VBox)
    assert len(date_accordion.children[0].children) == 1
    child = date_accordion.children[0].children[0]
    assert isinstance(child, widgets.Accordion)
    assert child.get_title(0) == "Step A"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime(2024, 1, 1, 12, 30), "20240101"),
        (date(2023, 12, 31), "20231231"),
        ("20240102", "20240102"),
        (None, ""),
    ],
)
def test_get_iso_date_formats_known_types(value, expected):
    assert status_gui.ProcessedPathAccordeon._get_iso_date(value) == expected


def test_status_for_returns_processed_summary():
    dataset = DummyDataset()
    accord = status_gui.ProcessedPathAccordeon(dataset)
    component = _make_component(statusFilesLaunched=True, filesOk=True)
    status, color = accord._status_for(component)
    assert "OK" in status
    assert color == status_gui.COLOR_PROCESSED


@pytest.mark.parametrize(
    "component, expected_status, expected_color",
    [
        (
            _make_component(statusFilesLaunched=True, filesOk=False),
            "ERR",
            status_gui.COLOR_BEING_PROCESSED,
        ),
        (
            _make_component(
                statusFilesLaunched=False,
                statusDetailedLaunched=True,
                detailedOk=False,
            ),
            "ERR",
            status_gui.COLOR_BEING_PROCESSED,
        ),
        (
            _make_component(),
            None,
            status_gui.COLOR_NOT_PROCESSED,
        ),
    ],
)
def test_status_for_handles_non_processed_states(
    component, expected_status, expected_color
):
    accord = status_gui.ProcessedPathAccordeon(DummyDataset())
    status, color = accord._status_for(component)
    if expected_status is None:
        assert status is None
    else:
        assert expected_status in status
    assert color == expected_color


def test_create_pt_step_widget_returns_html_with_status():
    dataset = DummyDataset()
    accord = status_gui.ProcessedPathAccordeon(dataset)
    component = _make_component(
        statusFilesLaunched=True,
        filesOk=False,
        print_errors=lambda: ["Problem detected"],
        statusDetailedLaunched=True,
    )
    widget = accord._create_pt_step_widget(component)
    assert isinstance(widget, widgets.HTML)
    assert "Problem detected" in widget.value


def test_create_pt_step_widget_uses_hdf5_viewer(monkeypatch):
    dataset = DummyDataset()
    accord = status_gui.ProcessedPathAccordeon(dataset)

    class Viewer:
        def __init__(self, path):
            self.ui = widgets.Label(f"Viewer for {path}")

    component = SimpleNamespace(
        statusFilesLaunched=True,
        filesOk=True,
        print_status=lambda: ["OK"],
        print_errors=lambda: ["ERR"],
        print_status_details=lambda: ["DETAIL"],
        visualize=True,
        statusDetailedLaunched=False,
        target_files=["/path/to/file.h5"],
    )

    def load_status_detailed():
        component.statusDetailedLaunched = True

    component.loadStatusDetailed = load_status_detailed

    monkeypatch.setattr(status_gui, "HDF5ImageViewer", Viewer)

    widget = accord._create_pt_step_widget(component)
    assert isinstance(widget, widgets.Label)
    assert "Viewer for /path/to/file.h5" == widget.value
    assert component.statusDetailedLaunched is True


def test_create_pt_step_widget_falls_back_on_viewer_error(monkeypatch):
    dataset = DummyDataset()
    accord = status_gui.ProcessedPathAccordeon(dataset)

    component = _make_component(
        statusFilesLaunched=True,
        filesOk=True,
        visualize=True,
        target_files=["/path/to/file.h5"],
    )

    class Viewer:
        def __init__(self, path):
            raise RuntimeError("boom")

    monkeypatch.setattr(status_gui, "HDF5ImageViewer", Viewer)

    widget = accord._create_pt_step_widget(component)
    assert isinstance(widget, widgets.HTML)
    assert "OK" in widget.value
