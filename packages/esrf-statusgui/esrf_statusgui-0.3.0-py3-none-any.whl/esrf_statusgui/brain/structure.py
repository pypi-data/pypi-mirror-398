import json
import logging
import os
from typing import Optional, Union

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path
try:
    from esrf_loadFile import loadFile
except ImportError:
    from esrf_statusgui.data_managment.loadFile import loadFile

import esrf_statusgui.exp_methods.MasterClass_Status as MasterClass_Status
from esrf_statusgui.file_utils.file_utils import path_is_root_of

logger = logging.getLogger(__name__)

H5_EXTENSIONS: set[str] = {".h5", ".hdf5"}


def _candidate_h5_paths(base: Path, dataset_name: str) -> tuple[list[Path], list[Path]]:
    """
    Return (existing_candidates, all_candidates_checked) for a dataset.

    Only .h5/.hdf5 files are considered. If the dataset name already has a
    non-HDF extension (e.g. .edf, .csv), no candidates are produced.
    """
    ds_path = Path(dataset_name)
    suffix = ds_path.suffix.lower()
    if suffix and suffix not in H5_EXTENSIONS:
        return [], []

    base = Path(base)
    dataset_dir = base / dataset_name
    candidates: list[Path] = []

    if dataset_dir.is_dir():
        stem = ds_path.stem
        same_name = dataset_dir / dataset_dir.name
        if same_name.suffix.lower() in H5_EXTENSIONS:
            candidates.append(same_name)
        try:
            with os.scandir(dataset_dir) as entries:
                for entry in entries:
                    if (
                        entry.is_file()
                        and os.path.splitext(entry.name)[1].lower() in H5_EXTENSIONS
                    ):
                        candidates.append(Path(entry.path))
        except OSError:
            logger.debug("Failed to scan %s for HDF5 files", dataset_dir, exc_info=True)
        for ext in H5_EXTENSIONS:
            candidates.append(dataset_dir / f"{stem}{ext}")
    else:
        if dataset_dir.suffix.lower() in H5_EXTENSIONS:
            candidates.append(dataset_dir)
        else:
            for ext in H5_EXTENSIONS:
                candidates.append(dataset_dir.with_suffix(ext))

    seen: set[Path] = set()
    unique: list[Path] = []
    for cand in candidates:
        if cand not in seen:
            seen.add(cand)
            unique.append(cand)

    existing = [cand for cand in unique if cand.exists()]
    return existing, unique


def merge_paths(
    input_paths: Union[str, Path, list[Union[str, Path]]],
) -> list[Path]:
    """Merges multiple paths into a list of Path objects"""
    if isinstance(input_paths, (str, Path)):
        return [Path(input_paths)]
    elif isinstance(input_paths, list):
        paths = []
        for path in input_paths:
            paths.extend(merge_paths(path))
        return paths
    else:
        return []


class Sample:
    """Represents a sample with raw and processed data paths and associated datasets"""

    def __init__(self, sample: str, path: Path, type: str):
        self.sample = sample
        if type == "RAW_DATA":
            self.raw_path = [path]
            self.processed_path = None
        if type == "PROCESSED_DATA":
            self.raw_path = None
            self.processed_path = [path]
        self.datasets: list[Dataset] = []

    def add_dataset(self, dataset):
        """Adds a dataset to the sample and establishes a reciprocal link."""
        if not isinstance(dataset, Dataset):
            dataset = Dataset(dataset)
        if dataset.dataset in self.list_datasets():
            # print(f"Dataset already exists in Sample: {self.sample}")
            return
        dataset.sample = self  # Link dataset back to this sample
        dataset.get_method()
        self.datasets.append(dataset)

    def list_datasets(self):
        """Lists all datasets associated with this sample."""
        return [i.dataset for i in self.datasets]

    def __str__(self):
        return f"Sample(name={self.sample}, datasets={len(self.datasets)})"

    def __repr__(self) -> str:
        return f"Sample(name={self.sample}, datasets={len(self.datasets)})"


class Dataset:
    """
    Represents a dataset with methods to determine its acquisition technique (method),
    processing state and associated sample.
    """

    json_data = None

    def __init__(self, name: str):
        self.sample: Optional[Sample] = None
        self.dataset = name
        self.method = None
        self.processing_state = None

    def get_method(self):
        # Load JSON data once if it hasn't been loaded yet
        if Dataset.json_data is None:
            json_path = Path(MasterClass_Status.__file__).parent / "status.json"
            try:
                with open(json_path) as f:
                    Dataset.json_data = json.load(f)
            except FileNotFoundError:
                logging.warning(f"JSON file {json_path} not found.")
                Dataset.json_data = None
        if Dataset.json_data is not None:
            for method in Dataset.json_data:
                id_key = False
                if "dataset_key" in Dataset.json_data[method]:
                    if isinstance(Dataset.json_data[method]["dataset_key"], list):
                        if any(
                            key.lower() in self.dataset.lower()
                            for key in Dataset.json_data[method]["dataset_key"]
                        ):
                            self.method = method
                            id_key = True
                    else:
                        if (
                            Dataset.json_data[method]["dataset_key"].lower()
                            in self.dataset.lower()
                        ):
                            self.method = method
                            id_key = True
                if self.sample.raw_path:
                    for r_path in self.sample.raw_path:
                        if not id_key and r_path is not None:
                            existing, checked = _candidate_h5_paths(
                                Path(r_path), self.dataset
                            )

                            h5 = None
                            for candidate in existing:
                                try:
                                    h5 = loadFile(candidate)
                                except Exception as exc:  # noqa: BLE001
                                    if logger.isEnabledFor(logging.DEBUG):
                                        logger.debug(
                                            "Failed to load %s: %s",
                                            candidate,
                                            exc,
                                        )
                                if h5 is not None:
                                    break

                            if h5 is None:
                                if logger.isEnabledFor(logging.DEBUG) and checked:
                                    logger.debug(
                                        "No HDF5 match for dataset '%s' (checked %s)",
                                        self.dataset,
                                        ", ".join(str(c) for c in checked),
                                    )
                                continue

                            if h5 is not None:
                                for camera in Dataset.json_data[method]["h5_keys"]:
                                    for skey in camera.keys():
                                        if not self.compare_values_json(
                                            camera[skey],
                                            h5.get_value(camera[skey]["path"]),
                                        ):
                                            break
                                    else:
                                        if self.method is None:
                                            self.method = method
                                        elif isinstance(self.method, str):
                                            if self.method != self.method:
                                                self.method = [self.method, method]
                                        elif isinstance(self.method, list):
                                            if self.method not in self.method:
                                                self.method.append(method)

    def compare_values_json(self, json, h5):
        out = False
        if h5:
            if "value_min" in json.keys() and "value_max" in json.keys():
                out = h5 > json["value_min"] and h5 < json["value_max"]
            elif "value_min" in json.keys():
                out = h5 > json["value_min"]
            elif "value_max" in json.keys():
                out = h5 < json["value_max"]
            elif "value" in json.keys():
                out = json["value"] in h5
            elif "key" in json.keys():
                out = json["key"] in h5.get_keys()
        return out

    def __str__(self):
        return f"Dataset(name={self.dataset}, associated_sample={self.sample.sample if self.sample else None})"

    def __repr__(self) -> str:
        return f"Dataset(name={self.dataset}, associated_sample={self.sample.sample if self.sample else None})"


class SampleManager:
    """
    Manages a collection of samples and datasets,
    providing methods to create, find, and list samples and datasets.
    """

    def __init__(self):
        self.samples: list[Sample] = []

    def create_sample(self, name: str, path: Path, type: str) -> Sample:
        """Creates a new Sample and adds it to the manager."""
        if not self.find_sample_by_name(name):
            sample = Sample(sample=name, path=path, type=type)
            self.samples.append(sample)
            return sample
        else:
            inp = Sample(sample=name, path=path, type=type)
            ref = self.find_sample_by_name(name)
            for attr in ["raw_path", "processed_path"]:
                if getattr(inp, attr):
                    if getattr(ref, attr) is None:
                        setattr(ref, attr, getattr(inp, attr))
                    else:
                        getattr(ref, attr).extend(getattr(inp, attr))
            return ref

    def append_sample(self, sample: Sample) -> None:
        """Appends an existing Sample to the manager if not already present."""
        if not self.find_sample_by_name(sample.name):
            self.samples.append(sample)

    def find_sample_by_name(self, name: str) -> Optional[Sample]:
        """Finds a Sample by its name."""
        return next((sample for sample in self.samples if sample.sample == name), None)

    def find_sample_by_path(self, path: Path) -> Optional[Sample]:
        """Finds a Sample by its path."""
        return next(
            (
                sample
                for sample in self.samples
                if any(r_path == path for r_path in sample.raw_path)
            ),
            None,
        )

    def create_dataset_for_sample(self, sample_name: str) -> Optional[Dataset]:
        """Creates a new Dataset and associates it with a Sample by name."""
        sample = self.find_sample_by_name(sample_name)
        if sample:
            dataset = Dataset()
            sample.add_dataset(dataset)
            return dataset
        else:
            logging.info(f"Sample with name '{sample_name}' not found.")
            return None

    def list_all_samples(self):
        """Lists all Samples managed by the SampleManager."""
        return self.samples

    def list_all_datasets(self):
        """Lists all Datasets across all Samples."""
        datasets = []
        for sample in self.samples:
            datasets.extend(sample.datasets)
        return datasets

    def find_dataset_by_name(
        self, sample_name: str, dataset_name: str
    ) -> Optional[Dataset]:
        """Finds a Dataset by its name within a specific Sample."""
        sample = self.find_sample_by_name(sample_name)
        if sample:
            return next(
                (ds for ds in sample.datasets if ds.dataset == dataset_name), None
            )
        return None

    def get_datasets_by_method(self, method: str) -> list[Dataset]:
        """Gets all datasets across samples filtered by the method attribute."""
        return [ds for ds in self.list_all_datasets() if ds.method == method]

    def get_datasets_by_path(self, path: Path) -> list[Dataset]:
        """Gets all datasets across samples filtered by main path."""
        return [
            ds
            for ds in self.list_all_datasets()
            if any(
                path_is_root_of(path, spath / ds.dataset)
                for spath in merge_paths([ds.sample.raw_path, ds.sample.processed_path])
            )
        ]

    def __repr__(self) -> str:
        return f"SampleManager(samples={len(self.samples)})"
