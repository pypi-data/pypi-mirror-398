from __future__ import annotations

# mypy: allow-untyped-defs
from types import SimpleNamespace

import ipywidgets as widgets
import pytest

from esrf_statusgui.brain import post_process as pp


def test_safe_len_handles_iterables_and_errors():
    assert pp._safe_len([1, 2, 3]) == 3
    assert pp._safe_len((1,)) == 1
    assert pp._safe_len(None) == 0

    class NoLen:
        pass

    assert pp._safe_len(NoLen()) == 0


def test_html_uses_expected_palette():
    html = pp._html("message", kind="warn")
    assert "message" in html.value
    assert "color" in html.value
    html_default = pp._html("default")
    assert "default" in html_default.value


def test_try_import_from_path(tmp_path):
    module_path = tmp_path / "module_for_import.py"
    module_path.write_text("class Holder:\n    value = 123\n")

    resolved = pp._try_import_from_path(
        pp.Path(module_path.as_posix()),
        "Holder.value",
        log_prefix="test",
    )
    assert resolved == 123

    missing = pp._try_import_from_path(
        pp.Path(module_path.as_posix()),
        "Holder.missing",
        log_prefix="test",
    )
    assert missing is None


def test_dataset_view_ok(tmp_path):
    raw_root = (
        tmp_path / "visitor" / "ma9999" / "id11" / "20240101" / "RAW_DATA" / "sample"
    )
    raw_root.mkdir(parents=True)
    sample = SimpleNamespace(
        raw_path=[pp.Path(raw_root.as_posix())],
        processed_path=[],
    )
    dataset = SimpleNamespace(
        method="DCT",
        dataset="sample_dataset",
        sample=sample,
        processing_state=[1, 2],
    )

    view = pp._DatasetView.from_obj(dataset)
    assert view.method == "DCT"
    assert view.dataset == "sample_dataset"
    assert view.sample_raw_root.samefile(raw_root)
    assert view.processing_state == [1, 2]


def test_dataset_view_requires_valid_dataset(tmp_path):
    raw_root = (
        tmp_path / "visitor" / "ma9999" / "id11" / "20240101" / "RAW_DATA" / "sample"
    )
    raw_root.mkdir(parents=True)
    sample = SimpleNamespace(
        raw_path=[pp.Path(raw_root.as_posix())],
        processed_path=[],
    )
    base = dict(
        dataset="name",
        sample=sample,
        processing_state=[],
    )

    with pytest.raises(ValueError):
        pp._DatasetView.from_obj(SimpleNamespace(method=None, **base))

    with pytest.raises(ValueError):
        pp._DatasetView.from_obj(
            SimpleNamespace(
                method="DCT", dataset="", sample=sample, processing_state=[]
            )
        )

    with pytest.raises(ValueError):
        pp._DatasetView.from_obj(
            SimpleNamespace(
                method="DCT", dataset="name", sample=None, processing_state=[]
            )
        )

    bad_sample = SimpleNamespace(raw_path=[], processed_path=[])
    with pytest.raises(ValueError):
        pp._DatasetView.from_obj(
            SimpleNamespace(
                method="DCT", dataset="name", sample=bad_sample, processing_state=[]
            )
        )


def _make_dataset(tmp_path, method="FF"):
    raw_root = (
        tmp_path / "visitor" / "ma9999" / "id11" / "20240101" / "RAW_DATA" / "sample"
    )
    dataset_dir = raw_root / "dataset"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "dataset.h5").touch()

    sample = SimpleNamespace(
        raw_path=[pp.Path(raw_root.as_posix())],
        processed_path=[],
        sample="sample_name",
    )

    dataset = SimpleNamespace(
        dataset="dataset",
        method=method,
        sample=sample,
        processing_state=[],
    )
    return dataset


def test_post_process_widget_build(tmp_path, monkeypatch):
    monkeypatch.setattr(pp, "display", lambda *args, **kwargs: None)
    dataset = _make_dataset(tmp_path)
    proc = pp.Post_process(dataset)
    assert proc.widget
    assert isinstance(proc.widget[0], widgets.VBox)
    assert proc.processed_button.disabled is False

    exported = proc.export_widget()
    assert exported == proc.widget


def test_post_process_on_button_clicked_ff(tmp_path, monkeypatch):
    dataset = _make_dataset(tmp_path, method="FF")
    processed_root = tmp_path / "processed"
    processed_root.mkdir()
    imaged11_root = processed_root / "ImageD11"
    helper_src = imaged11_root / "ImageD11" / "nbGui" / "TDXRD" / "use_only_if_needed"
    helper_src.mkdir(parents=True)
    (helper_src / "README.txt").write_text("helper")

    created = {}

    def fake_nb(*args):
        created["args"] = args

    class DummyStatus:
        def __init__(self, path):
            self.path = path
            self.loaded = False

        def loadStatusFiles(self):
            self.loaded = True

    monkeypatch.setattr(pp, "display", lambda *args, **kwargs: None)
    monkeypatch.setattr(pp, "create_processing_nb_FF", fake_nb)
    monkeypatch.setattr(pp, "ff_status", lambda path: DummyStatus(path))

    latest = pp.Path((processed_root / "dataset").as_posix())
    latest.mkdir(parents=True, exist_ok=True)

    def fake_latest(self, raw_dir=None):
        return latest

    monkeypatch.setattr(pp.Post_process, "_get_latest_date_path", fake_latest)

    proc = pp.Post_process(dataset)
    proc.on_button_clicked(None)

    assert dataset.processing_state
    status_obj = dataset.processing_state[0]
    assert isinstance(status_obj, DummyStatus)
    assert status_obj.loaded is True
    assert created["args"][1] == latest


def test_start_dct_from_scratch_sets_defaults(tmp_path, monkeypatch):
    dataset = _make_dataset(tmp_path, method="DCT")
    monkeypatch.setattr(pp, "display", lambda *args, **kwargs: None)

    class ParametersTab:
        def __init__(self):
            self.refreshed = False

        def refresh(self):
            self.refreshed = True

    class FakePySetup:
        last = None

        def __init__(self):
            FakePySetup.last = self
            self.dataset_selection_tab = SimpleNamespace(selected_file=None)
            self.parameters = SimpleNamespace(internal=SimpleNamespace(experiment=None))
            self.parameters_tab = ParametersTab()
            self.tabs = SimpleNamespace(
                selected_index=0,
                children=[
                    SimpleNamespace(layout=SimpleNamespace(display="block")),
                    SimpleNamespace(layout=SimpleNamespace(display="block")),
                    SimpleNamespace(layout=SimpleNamespace(display="block")),
                ],
            )

        def display(self):
            return "ui"

    monkeypatch.setattr(pp, "pySetupH5", FakePySetup)
    proc = pp.Post_process(dataset)
    proc._start_dct_from_scratch()

    widget = FakePySetup.last
    assert widget is not None
    assert widget.dataset_selection_tab.selected_file == proc.path
    assert widget.tabs.selected_index == 2
    assert widget.parameters_tab.refreshed
    assert widget.tabs.children[0].layout.display == "none"


def test_ensure_acquisition_dir_creates_path(tmp_path):
    dataset = _make_dataset(tmp_path)
    proc = pp.Post_process(dataset)

    base = tmp_path / "visitor" / "ma9999" / "id11" / "20240102"
    (base / "PROCESSED_DATA").mkdir(parents=True)
    target = pp.Path((base / "PROCESSED_DATA" / "dataset").as_posix())
    ensured = proc._ensure_acquisition_dir(target)
    assert ensured.exists()
    assert ensured.is_dir()


def test_show_confirmation_dialog_sets_dialog(tmp_path, monkeypatch):
    dataset = _make_dataset(tmp_path, method="DCT")
    monkeypatch.setattr(pp, "display", lambda *args, **kwargs: None)
    proc = pp.Post_process(dataset)
    proc.show_confirmation_dialog()
    assert isinstance(proc._confirmation_dialog, widgets.VBox)
