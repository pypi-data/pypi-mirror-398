import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import h5py
import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatasetAttributes:
    """Metadata associated with a dataset in the template parameter file."""

    matlab_class: Optional[str] = None
    matlab_dimensions: Optional[tuple[int, ...]] = None

    def asdict(self) -> dict[str, Any]:
        """Return the attributes in a format that can be directly written to HDF5."""
        attributes: dict[str, Any] = {}
        if self.matlab_class:
            attributes["MATLAB_Class"] = self.matlab_class
        if self.matlab_dimensions:
            attributes["MATLAB_Dimensions"] = tuple(self.matlab_dimensions)
        return attributes


class DCTParameterSchema:
    """Loads and provides dataset metadata from the 0_parameters.h5 template."""

    def __init__(self, template_file: Path):
        self.template_file = template_file
        self._attributes = self._load_metadata()

    def _load_metadata(self) -> dict[str, DatasetAttributes]:
        metadata: dict[str, DatasetAttributes] = {}
        if not self.template_file.exists():
            logger.warning(
                "Reference DCT parameter template %s not found.", self.template_file
            )
            return metadata

        try:
            with h5py.File(self.template_file, "r") as handle:
                self._collect_metadata(handle, metadata, prefix="")
        except OSError as error:
            logger.warning(
                "Unable to load DCT parameter template %s: %s",
                self.template_file,
                error,
            )

        return metadata

    def _collect_metadata(
        self, node: h5py.Group, metadata: dict[str, DatasetAttributes], prefix: str
    ) -> None:
        for name, item in node.items():
            path = _normalize_path(f"{prefix}/{name}" if prefix else f"/{name}")
            if isinstance(item, h5py.Dataset):
                metadata[path] = DatasetAttributes(
                    matlab_class=_decode_text_attribute(item.attrs.get("MATLAB_Class")),
                    matlab_dimensions=_normalize_dimensions(
                        item.attrs.get("MATLAB_Dimensions")
                    ),
                )
            elif isinstance(item, h5py.Group):
                self._collect_metadata(item, metadata, path)

    def get(self, path: str) -> Optional[DatasetAttributes]:
        return self._attributes.get(_normalize_path(path))


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        return "/" + path
    return path


def _decode_text_attribute(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, str):
        return value
    array = np.array(value)
    if array.size == 1:
        element = array.item()
        if isinstance(element, bytes):
            return element.decode("utf-8")
        return str(element)
    return str(array)


def _normalize_dimensions(value: Any) -> Optional[tuple[int, ...]]:
    if value is None:
        return None
    dims = np.array(value).astype(int).tolist()
    return tuple(int(dim) for dim in dims)


_TEMPLATE_FILE = Path(__file__).with_name("0_parameters.h5")
DEFAULT_SCHEMA = DCTParameterSchema(_TEMPLATE_FILE)


def get_dataset_attributes(path: str) -> Optional[DatasetAttributes]:
    """Return the template metadata for a dataset path."""
    return DEFAULT_SCHEMA.get(path)
