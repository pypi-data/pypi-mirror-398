from __future__ import annotations

# mypy: allow-untyped-defs
from esrf_statusgui.brain import structure


def test_merge_paths_handles_string_and_list(tmp_path):
    single = structure.merge_paths(str(tmp_path / "file"))
    assert single == [structure.Path(str(tmp_path / "file"))]

    nested_input = [
        str(tmp_path / "one"),
        [str(tmp_path / "two"), [str(tmp_path / "three")]],
    ]
    nested = structure.merge_paths(nested_input)
    assert len(nested) == 3
    assert all(isinstance(item, structure.Path) for item in nested)


def test_sample_add_dataset_and_prevents_duplicates(monkeypatch, tmp_path):
    monkeypatch.setattr(structure.Dataset, "get_method", lambda self: None)
    raw_sample = structure.Path((tmp_path / "RAW_DATA" / "sample").as_posix())
    sample = structure.Sample("sample", raw_sample, "RAW_DATA")
    sample.add_dataset("dataset1")
    assert len(sample.datasets) == 1
    assert sample.datasets[0].sample is sample

    # Duplicate should be ignored
    sample.add_dataset("dataset1")
    assert len(sample.datasets) == 1


def test_sample_manager_create_and_find(monkeypatch, tmp_path):
    monkeypatch.setattr(structure.Dataset, "get_method", lambda self: None)
    manager = structure.SampleManager()

    raw_path = structure.Path((tmp_path / "RAW_DATA" / "sample").as_posix())
    processed_path = structure.Path((tmp_path / "PROCESSED_DATA" / "sample").as_posix())
    manager.create_sample("sample", raw_path, "RAW_DATA")
    manager.create_sample("sample", processed_path, "PROCESSED_DATA")

    sample = manager.find_sample_by_name("sample")
    assert sample is not None
    assert raw_path in sample.raw_path
    assert processed_path in sample.processed_path

    by_path = manager.find_sample_by_path(raw_path)
    assert by_path is sample


def test_sample_manager_dataset_queries(monkeypatch, tmp_path):
    monkeypatch.setattr(structure.Dataset, "get_method", lambda self: None)
    manager = structure.SampleManager()
    raw_sample = structure.Path((tmp_path / "RAW_DATA" / "sample").as_posix())
    processed = structure.Path((tmp_path / "PROCESSED_DATA" / "sample").as_posix())

    sample = manager.create_sample("sample", raw_sample, "RAW_DATA")
    manager.create_sample("sample", processed, "PROCESSED_DATA")

    sample.add_dataset("dataset1")
    dataset = sample.datasets[0]
    dataset.method = "DCT"
    dataset.sample.processed_path = [processed]

    assert manager.get_datasets_by_method("DCT") == [dataset]
    queried = manager.get_datasets_by_path(raw_sample)
    assert dataset in queried


def test_sample_list_datasets_returns_names(monkeypatch, tmp_path):
    monkeypatch.setattr(structure.Dataset, "get_method", lambda self: None)
    sample_path = structure.Path((tmp_path / "RAW_DATA" / "sample").as_posix())
    sample = structure.Sample("sample", sample_path, "RAW_DATA")

    sample.add_dataset("dataset1")
    sample.add_dataset(structure.Dataset("dataset2"))

    assert sample.list_datasets() == ["dataset1", "dataset2"]
    assert all(ds.sample is sample for ds in sample.datasets)


def test_sample_manager_merges_paths_for_existing_sample(monkeypatch, tmp_path):
    monkeypatch.setattr(structure.Dataset, "get_method", lambda self: None)
    manager = structure.SampleManager()

    raw_a = structure.Path((tmp_path / "RAW_DATA" / "sample_a").as_posix())
    raw_b = structure.Path((tmp_path / "RAW_DATA" / "sample_b").as_posix())
    processed = structure.Path((tmp_path / "PROCESSED_DATA" / "sample").as_posix())

    sample = manager.create_sample("sample", raw_a, "RAW_DATA")
    manager.create_sample("sample", processed, "PROCESSED_DATA")
    manager.create_sample("sample", raw_b, "RAW_DATA")

    assert sample.raw_path == [raw_a, raw_b]
    assert sample.processed_path == [processed]
    assert manager.find_sample_by_name("sample") is sample


def test_sample_manager_lists_and_finds_datasets(monkeypatch, tmp_path):
    monkeypatch.setattr(structure.Dataset, "get_method", lambda self: None)
    manager = structure.SampleManager()

    raw_path = structure.Path((tmp_path / "RAW_DATA" / "sample").as_posix())
    sample = manager.create_sample("sample", raw_path, "RAW_DATA")
    sample.add_dataset("dataset1")
    sample.add_dataset("dataset2")

    other_path = structure.Path((tmp_path / "RAW_DATA" / "other").as_posix())
    other = manager.create_sample("other", other_path, "RAW_DATA")
    other.add_dataset("dataset3")

    assert manager.list_all_samples() == [sample, other]
    assert manager.list_all_datasets() == sample.datasets + other.datasets
    assert manager.find_dataset_by_name("sample", "dataset2") is sample.datasets[1]
    assert manager.find_dataset_by_name("sample", "missing") is None


def test_sample_manager_get_datasets_by_processed_path(monkeypatch, tmp_path):
    monkeypatch.setattr(structure.Dataset, "get_method", lambda self: None)
    manager = structure.SampleManager()

    raw_path = structure.Path((tmp_path / "RAW_DATA" / "sample").as_posix())
    processed_path = structure.Path((tmp_path / "PROCESSED_DATA" / "sample").as_posix())

    sample = manager.create_sample("sample", raw_path, "RAW_DATA")
    manager.create_sample("sample", processed_path, "PROCESSED_DATA")
    sample.add_dataset("dataset1")
    dataset = sample.datasets[0]

    by_processed = manager.get_datasets_by_path(processed_path)
    assert by_processed == [dataset]
