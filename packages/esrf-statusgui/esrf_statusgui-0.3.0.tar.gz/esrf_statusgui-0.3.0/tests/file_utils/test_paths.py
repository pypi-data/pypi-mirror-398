from __future__ import annotations

from esrf_statusgui.file_utils.paths import (
    clean_dir_name,
    get_visitor_root,
    relative_to_visitor,
)


def test_clean_dir_name_removes_gpfs_prefix_and_replaces_characters():
    clean_path, name, orig_path, orig_name = clean_dir_name(
        "/gpfs/easy/ma1234/id11/20240101/sample.name/test-run"
    )

    assert str(clean_path) == "/ma1234/id11/20240101/samplepname/test_run"
    assert name == "test_run"
    assert str(orig_path) == "/gpfs/easy/ma1234/id11/20240101/sample.name/test-run"
    assert orig_name == "test-run"


def test_clean_dir_name_handles_mnt_storage_prefix_and_dash():
    clean_path, name, orig_path, orig_name = clean_dir_name("/mnt/storage/user/run-1")

    assert str(clean_path) == "/user/run_1"
    assert name == "run_1"
    assert str(orig_path) == "/mnt/storage/user/run-1"
    assert orig_name == "run-1"


def test_clean_dir_name_preserves_paths_without_prefixes():
    clean_path, name, orig_path, orig_name = clean_dir_name("relative.sample-2")

    assert str(clean_path) == "relativepsample_2"
    assert name == "relativepsample_2"
    assert str(orig_path) == "relative.sample-2"
    assert orig_name == "relative.sample-2"


def test_relative_to_visitor_handles_gpfs_prefix(monkeypatch):
    monkeypatch.setenv("ESRF_VISITOR_ROOT", "/data/visitor")
    get_visitor_root.cache_clear()

    rel = relative_to_visitor("/gpfs/easy/data/visitor/ma1234/id11/20240101")
    assert str(rel) == "ma1234/id11/20240101"
