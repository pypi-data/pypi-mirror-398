import runpy
from unittest import mock

# mypy: allow-untyped-defs


def test_main_entry_instantiates_and_displays_widget(monkeypatch):
    """Ensure the CLI entry point builds the dataset tab and calls display()."""
    fake_tab = mock.Mock()
    dataset_cls = mock.Mock(return_value=fake_tab)
    monkeypatch.setattr(
        "esrf_statusgui.visualization.statusGUI.DatasetSelectionTab",
        dataset_cls,
    )

    runpy.run_module("src.main", run_name="__main__")

    dataset_cls.assert_called_once_with()
    fake_tab.display.assert_called_once_with()
