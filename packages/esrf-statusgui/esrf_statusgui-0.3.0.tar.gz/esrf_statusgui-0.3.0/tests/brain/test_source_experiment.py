from __future__ import annotations

# mypy: allow-untyped-defs
import os
from pathlib import Path

import pytest

from esrf_statusgui.brain import source_experiment as src


class DummyProgress:
    def __init__(self, **kwargs):
        self.value = kwargs.get("value", 0)
        self.max = kwargs.get("max", 0)


def test_gtMoveData_copies_files_and_links_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(src, "Path", Path)
    monkeypatch.setattr(src.widgets, "IntProgress", DummyProgress)
    monkeypatch.setattr(src, "display", lambda *args, **kwargs: None)

    old_path = tmp_path / "old"
    new_path = tmp_path / "new"
    raw_dir = old_path / "0_rawdata"
    diff_dir = old_path / "2_difspot"

    raw_dir.mkdir(parents=True)
    diff_dir.mkdir(parents=True)
    (raw_dir / "raw.txt").write_text("raw")
    (diff_dir / "spot.txt").write_text("spot")
    (old_path / "single.txt").write_text("file")

    output = pytest.importorskip("ipywidgets").Output()

    src.gtMoveData(str(old_path), str(new_path), output)

    copied_file = new_path / "single.txt"
    assert copied_file.exists()
    assert copied_file.read_text() == "file"

    dest_raw = new_path / "0_rawdata"
    dest_spot = new_path / "2_difspot"
    assert dest_raw.is_dir()
    assert dest_spot.is_dir()
    linked_raw = dest_raw / "raw.txt"
    assert linked_raw.is_symlink()
    assert os.readlink(linked_raw) == str(raw_dir / "raw.txt")
    linked_spot = dest_spot / "spot.txt"
    assert linked_spot.is_symlink()
    assert os.readlink(linked_spot) == str(diff_dir / "spot.txt")
