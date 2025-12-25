import logging
import os
import re
from collections.abc import Mapping
from enum import Enum, auto
from typing import Any, Optional, Union

import h5py
import numpy as np
import scipy.io as scio

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path
from silx.io import open as silx_open

logger = logging.getLogger(__name__)


class FileType(Enum):
    """Enumeration of supported file types."""

    HDF5 = auto()
    MAT = auto()
    CIF = auto()
    REFLECTION = auto()
    UNKNOWN = auto()


class genericFile:
    """Base class for generic file loading and processing."""

    def __init__(self, data=None):
        self.data = data or {}
        self.sRaw = None

    def get_value(self, key, default=None):
        try:
            keys = key.split("/")
            value = self.data
            for attr in keys:
                value = value[attr]
            if isinstance(value, dict):
                if self.__class__.__name__ == "LoadMatFile":
                    if any(
                        "FilterMATDataset" in base.__name__
                        for base in self.__class__.__bases__
                    ):
                        return FilterMATDataset(value)
                    elif any(
                        "genericFile" in base.__name__
                        for base in self.__class__.__bases__
                    ):
                        return genericFile(value)
                else:
                    return genericFile(value)
            elif isinstance(value, list) and all(isinstance(i, dict) for i in value):
                if self.__class__.__name__ == "LoadMatFile":
                    if any(
                        "FilterMATDataset" in base.__name__
                        for base in self.__class__.__bases__
                    ):
                        return [FilterMATDataset(i) for i in value]
                    elif any(
                        "genericFile" in base.__name__
                        for base in self.__class__.__bases__
                    ):
                        return [genericFile(i) for i in value]
                else:
                    return [genericFile(i) for i in value]

            if (
                isinstance(value, np.ndarray)
                and value.ndim == 2
                and value.shape[1] == 1
            ):
                value = value.flatten()
            if (
                isinstance(value, np.ndarray) or isinstance(value, h5py.Dataset)
            ) and value.dtype == np.object_:
                value = self._decode_if_bytes(value)
            return np.squeeze(value).item() if np.size(value) == 1 else value
        except Exception:
            # logging.warning(f"Failed to get value for key: {key}")
            return default

    def _decode_if_bytes(self, array: np.ndarray) -> np.ndarray:
        """Helper function to decode byte strings in an array if needed."""
        return np.vectorize(lambda x: x.decode("utf-8") if isinstance(x, bytes) else x)(
            array
        )

    def get_keys(self, key=None) -> list[str]:
        return list(self.get_value(key).data.keys()) if key else list(self.data.keys())

    def display_struct(self, max_level=None) -> str:
        return self.sRaw if self.sRaw else ""

    def to_dict(self) -> dict[str, Any]:
        """Convert object data to a dictionary."""
        return {key: self.get_value(key) for key in self.get_keys()}

    def _dereference_node(self, node: Any) -> Any:
        """Unwrap helper classes to expose their underlying data containers."""
        while isinstance(node, genericFile):
            node = node.data
        return node

    @staticmethod
    def _parse_sequence_index(token: Union[str, int]) -> Optional[int]:
        """Parse a token representing a sequence index (e.g. '0' or '[0]')."""
        if isinstance(token, int):
            return token
        if not isinstance(token, str):
            return None
        if token.isdigit():
            return int(token)
        if token.startswith("[") and token.endswith("]"):
            inner = token[1:-1]
            if inner.isdigit():
                return int(inner)
        return None

    def _resolve_metadata_target(self, key: str) -> Any:
        """Traverse the data hierarchy without materializing datasets."""
        if key in (None, ""):
            return self._dereference_node(self.data)

        parts = [part for part in key.split("/") if part]
        current: Any = self._dereference_node(self.data)

        for part in parts:
            current = self._dereference_node(current)
            if current is None:
                return None

            if isinstance(current, (h5py.Group, h5py.File)):
                if part in current:
                    current = current[part]
                    continue
                attrs = getattr(current, "attrs", None)
                if attrs is not None and part in attrs:
                    current = attrs[part]
                    continue
                return None

            if isinstance(current, Mapping):
                current = current.get(part)
                continue

            if isinstance(current, (list, tuple)):
                index = self._parse_sequence_index(part)
                if index is None or index >= len(current):
                    return None
                current = current[index]
                continue

            if hasattr(current, "keys"):
                keys = current.keys()
                if part in keys:
                    getter = getattr(current, "get", None)
                    if callable(getter):
                        current = getter(part)
                    else:
                        try:
                            current = current[part]
                        except Exception:
                            return None
                    continue

            if hasattr(current, part):
                current = getattr(current, part)
                continue

            return None

        return self._dereference_node(current)

    def get_size(self, key: str) -> Union[Optional[tuple[int, ...]], Optional[int]]:
        """Get the size/dimensions of a table, numpy array, or HDF5 group in the file.

        Args:
            key: Key/identifier for the data structure or group

        Returns:
            Tuple of dimensions if the key points to a table/array with multiple dimensions,
            int if it's a single dimension,
            number of members if it's a group,
            None otherwise
        """

        if self.data is None:
            return None

        try:
            target = self._resolve_metadata_target(key)
            target = self._dereference_node(target)

            if target is None:
                return None

            if isinstance(target, h5py.Dataset):
                shape = tuple(target.shape)
                if len(shape) == 1:
                    return shape[0]
                return shape

            if isinstance(target, (h5py.Group, h5py.File)):
                children = len(target.keys()) if hasattr(target, "keys") else 0
                attrs = getattr(target, "attrs", None)
                attr_count = len(attrs) if attrs is not None else 0
                return children + attr_count

            shape_attr = getattr(target, "shape", None)
            if shape_attr is not None and not isinstance(
                target, (h5py.Group, h5py.File)
            ):
                try:
                    shape_iter = tuple(shape_attr)
                except TypeError:
                    shape_iter = (shape_attr,)
                shape = tuple(
                    int(dim) if isinstance(dim, np.integer) else dim
                    for dim in shape_iter
                )
                if len(shape) == 1:
                    return shape[0]
                return shape

            if isinstance(target, Mapping):
                return len(target)

            if isinstance(target, (list, tuple)):
                if not target:
                    return 0
                if all(hasattr(item, "__len__") for item in target):
                    try:
                        first_len = len(target[0])
                        if all(len(item) == first_len for item in target):
                            return (len(target), first_len)
                    except Exception as exc:  # pragma: no cover - defensive guard
                        logger.debug(
                            "Unable to infer consistent lengths for %s sequence: %s",
                            type(target).__name__,
                            exc,
                        )
                return len(target)

            # Handle single values
            if hasattr(target, "__len__") and not isinstance(target, (str, bytes)):
                return len(target)

            return None

        except Exception as e:
            logging.warning(f"Error getting size for key '{key}': {str(e)}")

        return None


class FilterH5Dataset(genericFile):
    """A helper class to manage data within HDF5 structures."""

    def __init__(self, data: Union[h5py.Group, h5py.Dataset], from_mat: bool = None):
        self.data = data
        if from_mat is None:
            self._is_matlab_v73 = self._check_matlab_v73()
        else:
            self._is_matlab_v73 = from_mat
        super().__init__(data)

    def _check_matlab_v73(self) -> bool:
        """Safely check if this is a MATLAB v7.3 file by traversing up to root."""
        if not hasattr(self.data, "parent"):
            return False

        try:
            # Start with current object
            current = self.data
            visited = set()

            # Traverse up to root group with loop protection
            while hasattr(current, "parent") and current.parent not in visited:
                visited.add(current)
                if isinstance(current, h5py.File):
                    return "MATLAB_version" in current.attrs
                current = current.parent

            return False
        except Exception:
            return False

    def get_value(self, key: str, default: Optional[Any] = None) -> Any:
        """Retrieve value by key with structured handling for different data types."""
        try:
            if key in self.data.attrs.keys():
                value = self.data.attrs.get(key)
            elif key in self.data.keys():
                value = self.data.get(key)

            if self._is_matlab_v73:
                if isinstance(value, (h5py.Dataset, np.ndarray)):
                    value = self._fix_matlab_orientation(value)
            if isinstance(value, h5py.Group):
                return FilterH5Dataset(value)
            if (
                isinstance(value, np.ndarray)
                and value.ndim == 2
                and value.shape[1] == 1
            ):
                value = value.flatten()
            if (
                isinstance(value, np.ndarray) or isinstance(value, h5py.Dataset)
            ) and value.dtype == np.object_:
                value = self._decode_if_bytes(value)
                if (
                    isinstance(value, np.ndarray)
                    and value.ndim == 2
                    and value.shape[1] == 1
                ):
                    value = value.flatten()
            if isinstance(value, h5py.Dataset) and value.dtype == "<f8":
                if value.ndim == 2 and (
                    value.shape[1] == 1 or (value.shape[0] == 1 and value.shape[1] > 1)
                ):
                    value = value[()].flatten()
                else:
                    value = value[()]
            return np.squeeze(value).item() if np.size(value) == 1 else value
        except Exception:
            # logging.warning(f"Failed to get value for key: {key}")
            return default

    def _fix_matlab_orientation(
        self, value: Union[h5py.Dataset, np.ndarray]
    ) -> np.ndarray:
        """
        Properly convert MATLAB v7.3 arrays to correct NumPy orientation.

        MATLAB stores arrays in column-major order (Fortran-style) while NumPy uses
        row-major order (C-style). This method ensures proper array orientation.
        """
        arr = value[()] if isinstance(value, h5py.Dataset) else value
        # For higher dimensional arrays, we need to reverse the axes
        if arr.ndim > 1:
            return np.array([list(row) for row in zip(*arr)])
        return arr

    def _decode_if_bytes(
        self, value: Union[np.ndarray, h5py.Dataset]
    ) -> Union[str, np.ndarray]:
        """Decode byte strings in numpy arrays or datasets."""
        if value.shape == ():
            return value[()].decode("utf-8")
        elif value.size == 1 and isinstance(value[0], bytes):
            return value[0].decode("utf-8")
        return np.array(
            [d.decode("utf-8") if isinstance(d, bytes) else d for d in value]
        )

    def get_keys(self, key=None) -> list[str]:
        """Retrieve keys in the dataset."""
        if key:
            return list(self.get_value(key).data.keys()) + list(
                self.get_value(key).data.attrs.keys()
            )
        elif isinstance(self.data, (h5py.Group, h5py.File)):
            return list(self.data.keys()) + list(self.data.attrs.keys())
        return []

    def __repr__(self) -> str:
        return f"FilterH5Dataset({self.data})"

    def display_struct(self, max_level: int = 3) -> str:
        """Display the structure of the dataset up to a specified level of nesting."""
        return "\n".join(self._print_recursive(self, max_level=max_level))

    @staticmethod
    def _normalize_description_value(value: Any) -> Optional[Union[str, list[str]]]:
        """Convert raw attribute values to sensible string outputs."""
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if isinstance(value, str):
            return value
        if isinstance(value, np.generic):
            return FilterH5Dataset._normalize_description_value(value.item())
        if isinstance(value, np.ndarray):
            if value.shape == ():
                return FilterH5Dataset._normalize_description_value(value[()])
            flattened = [
                FilterH5Dataset._normalize_description_value(item)
                for item in value.ravel()
            ]
            flattened = [item for item in flattened if item is not None]
            if not flattened:
                return None
            if len(flattened) == 1:
                return flattened[0]
            return flattened
        if isinstance(value, (list, tuple)):
            converted = [
                FilterH5Dataset._normalize_description_value(item) for item in value
            ]
            converted = [item for item in converted if item is not None]
            if not converted:
                return None
            if len(converted) == 1:
                return converted[0]
            return converted
        return str(value)

    def _extract_description(self, target: Any) -> Optional[Union[str, list[str]]]:
        """Return the Description attribute (if present) from a resolved node."""
        target = self._dereference_node(target)
        if target is None:
            return None

        if isinstance(target, h5py.Dataset):
            attrs = getattr(target, "attrs", None)
            if attrs is not None and "Description" in attrs:
                return self._normalize_description_value(attrs["Description"])
            try:
                value = target[()]
            except Exception:
                return None
            return self._normalize_description_value(value)

        if isinstance(target, (h5py.Group, h5py.File)):
            attrs = getattr(target, "attrs", None)
            if attrs is not None:
                if "Description" in attrs:
                    return self._normalize_description_value(attrs["Description"])

                nx_class = attrs.get("NX_class")
                nx_class_name = self._normalize_description_value(nx_class)
                if (
                    isinstance(nx_class_name, str)
                    and nx_class_name.lower() == "nxentry"
                ):
                    if "title" in attrs:
                        return self._normalize_description_value(attrs["title"])
                    if hasattr(target, "keys") and "title" in target.keys():
                        try:
                            title_node = target.get("title")
                        except Exception:
                            title_node = None
                        if title_node is not None:
                            return self._extract_description(title_node)

            return None

        return self._normalize_description_value(target)

    def get_description(
        self, key: Optional[str] = None, default: Optional[Any] = None
    ) -> Optional[Union[str, list[str]]]:
        """Retrieve the `Description` attribute for the specified node."""
        try:
            # Try the provided key directly
            targets = []
            if key in (None, ""):
                targets.append(self.data)
            else:
                targets.append(self._resolve_metadata_target(key))

                parts = [part for part in key.split("/") if part]
                if parts and parts[-1].lower() != "description":
                    description_key = "/".join(parts + ["Description"])
                    targets.append(self._resolve_metadata_target(description_key))

            for candidate in targets:
                description = self._extract_description(candidate)
                if description is not None:
                    return description

            return default
        except Exception as error:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Failed to retrieve Description for key '%s': %s", key, error
                )
            return default

    def _print_recursive(
        self, group: "FilterH5Dataset", level: int = 0, max_level: int = 3
    ) -> list[str]:
        """Recursive helper function to print HDF5 keys and values/shapes with indentation."""
        out = []
        if level < max_level:
            indent = "    " * level
            if isinstance(group.data, (h5py.Group, h5py.File)):
                for key in group.get_keys():
                    value = group.data.get(key)
                    if isinstance(value, h5py.Group):
                        out.append(f"{indent}{key}:")
                        out.extend(
                            self._print_recursive(
                                group.get_value(key), level + 1, max_level
                            )
                        )
                    elif isinstance(value, h5py.Dataset):
                        if not all(dim < 5 for dim in value.shape):
                            out.append(f"{indent}{key}: {str(value)}")
                        else:
                            out.append(f"{indent}{key}: {group.get_value(key)}")
                    else:
                        out.append(f"{indent}{key}: {group.get_value(key)}")
        return out


class LoadH5File(FilterH5Dataset):
    """Class to load and display HDF5 file structures."""

    def __init__(self, filepath: str, from_mat: bool = None):
        self.filepath = Path(filepath)
        if self.filepath.exists():
            try:
                self.data = silx_open(str(self.filepath))
            except Exception as error:
                logging.warning(
                    "File path '%s' could not be opened: %s", filepath, error
                )
                self.data = None
        else:
            logging.warning(f"File path '{filepath}' not found.")
            self.data = None
        super().__init__(self.data, from_mat)


class FilterMATDataset(genericFile):
    """Helper class for structured access to data from MAT files."""

    def __init__(self, data: dict):
        super().__init__(data)

    def __repr__(self) -> str:
        keys = list(self.__dict__.keys())[:5]  # Show a sample of 5 keys
        return f"FilterMATDataset(keys={keys}, ...)"

    def display_struct(self, max_level: int = 3) -> str:
        """Display the structure of the dataset up to a specified level of nesting."""
        return "\n".join(self._print_recursive(self, level=0, max_level=max_level))

    def _print_recursive(
        self, dataset: "FilterMATDataset", level: int = 0, max_level: int = 3
    ) -> list[str]:
        """Recursive helper function to print keys and values with indentation."""
        out = []
        if level < max_level:
            indent = "    " * level
            for key in dataset.get_keys():
                value = dataset.get_value(key)
                if isinstance(value, FilterMATDataset):
                    out.append(f"{indent}{key}:")
                    out.extend(self._print_recursive(value, level + 1, max_level))
                elif isinstance(value, np.ndarray):
                    out.append(
                        f"{indent}{key}: Array with shape {value.shape} of dtype {value.dtype}"
                    )
                else:
                    out.append(f"{indent}{key}: {str(value)[:20]}...")
        return out


class LoadMatFile(FilterMATDataset):
    """Class to load and display MATLAB .mat file structures."""

    def __init__(self, file_path: str, *args):
        flattened_data = self._load_and_process(file_path)
        super().__init__(flattened_data)

    def _load_and_process(self, file_path: str) -> FilterMATDataset:
        data = scio.loadmat(file_path, struct_as_record=False, squeeze_me=True)
        return self._flatten_nested(data)

    def _flatten_nested(self, item: Any) -> Any:
        """Recursively process nested structures, wrapping dictionaries as FilterMATDataset instances."""
        if isinstance(item, np.ndarray) and item.dtype == object:
            # Process numpy arrays with object dtype recursively
            return [self._flatten_nested(sub_item) for sub_item in item.ravel()]
        elif isinstance(item, dict):
            # Wrap nested dictionaries as FilterMATDataset instances, leave the root dictionary unwrapped
            return {key: self._flatten_nested(value) for key, value in item.items()}
        elif hasattr(item, "_fieldnames"):
            # Wrap structures with field names as FilterMATDataset instances
            return {
                field: self._flatten_nested(getattr(item, field))
                for field in item._fieldnames
            }
        elif isinstance(item, list):
            return [self._flatten_nested(sub_item) for sub_item in item]
        elif isinstance(item, bytes):
            # Decode bytes to strings
            return item.decode("utf-8")
        return item

    def display_struct(self, max_level: int = 3) -> str:
        """Display the structure of the loaded .mat file data."""
        if isinstance(self.data, FilterMATDataset):
            return self.data.display_struct(max_level=max_level)
        return str(self.data)


class LoadCIFFile(genericFile):
    """Class to load and process CIF (Crystallographic Information Framework) files."""

    def __init__(self, file: Path, *args):
        super().__init__()
        self.file = Path(file)
        if self.file.suffix != ".cif":
            if logger.isEnabledFor(logging.DEBUG):
                logger.error(f"The file {self.file.name} is not a CIF file.")
        else:
            self._loadFile()

    def _loadFile(self) -> None:
        encodings = ["utf-8", "ISO-8859-1", "windows-1252"]
        for encoding in encodings:
            try:
                self.sRaw = self.file.read_text(encoding=encoding)
                self.data = {
                    "latticepar": self._extract_lattice_params(),
                    "opsym": self._extract_symmetry_ops(),
                    "spacegroup": self._extract_spacegroup(),
                    "hermann_mauguin": self._extract_hm_symbol(),
                    "crystal_system": self._extract_crystal_system(),
                }
                break
            except UnicodeDecodeError:
                logging.info(f"Error decoding with {encoding}, trying next encoding...")
            except Exception as e:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.error(f"Error loading CIF file {self.file.name}: {e}")

    def grep(self, pattern, file_content, group_index=0):
        match = re.search(pattern, file_content)
        if match:
            return match.group(group_index)
        return None

    # Function to extract lattice parameters
    def _extract_lattice_params(self):
        a = self.grep(r"_cell_length_a\s+([\d.]+)", self.sRaw, 1)
        b = self.grep(r"_cell_length_b\s+([\d.]+)", self.sRaw, 1)
        c = self.grep(r"_cell_length_c\s+([\d.]+)", self.sRaw, 1)
        alpha = self.grep(r"_cell_angle_alpha\s+([\d.]+)", self.sRaw, 1)
        beta = self.grep(r"_cell_angle_beta\s+([\d.]+)", self.sRaw, 1)
        gamma = self.grep(r"_cell_angle_gamma\s+([\d.]+)", self.sRaw, 1)

        try:
            latticepar = [
                float(a),
                float(b),
                float(c),
                float(alpha),
                float(beta),
                float(gamma),
            ]
        except TypeError:
            if logger.isEnabledFor(logging.DEBUG):
                logger.error("Error converting lattice parameters to floats")
            return None
        return latticepar

    # Function to extract symmetry operators
    def _extract_symmetry_ops(self):
        op_start = self.sRaw.find("loop_")
        if op_start != -1:
            symmetry_ops = self.sRaw[op_start:].splitlines()
            ops_cleaned = [op.strip() for op in symmetry_ops if re.match(r".*x.*", op)]
            return ops_cleaned
        return None

    # Function to extract spacegroup number
    def _extract_spacegroup(self):
        sg = self.grep(r"_symmetry_Int_Tables_number\s+(\d+)", self.sRaw, 1)
        return int(sg) if sg else None

    # Function to extract Hermann-Mauguin symbol
    def _extract_hm_symbol(self):
        hm = self.grep(r"_symmetry_space_group_name_H-M\s+(.+)", self.sRaw, 1)
        if hm:
            hm = hm.strip().replace("'", "")
            return hm[0].upper() + hm[1:].lower()
        return None

    # Function to extract crystal system
    def _extract_crystal_system(self):
        cellname = self.grep(r"_symmetry_cell_setting\s+(\w+)", self.sRaw, 1)
        return cellname.strip() if cellname else None


class LoadReflexionFile(genericFile):
    """Class to load and process CIF (Crystallographic Information Framework) files."""

    def __init__(self, file: Path, *args):
        super().__init__()
        self.file = Path(file)
        if self.file.suffix not in [".csv", ".dat"]:
            if logger.isEnabledFor(logging.DEBUG):
                logger.error(f"The file {self.file.name} is not a reflexion file.")
        else:
            self._loadFile()

    def _loadFile(self) -> None:
        if self.file.suffix == ".csv":
            delim = ";"
        elif self.file.suffix == ".dat" and self.file.name.lower() != "spacegroups.dat":
            delim = "space"

        logging.info(f"Opening file {self.file.name}...")
        encodings = ["utf-8", "ISO-8859-1", "windows-1252"]  # Try multiple encodings
        for encoding in encodings:
            try:
                with self.file.open("r", encoding=encoding) as fid:
                    if delim == "space":
                        lines = fid.readlines()
                        self.sRaw = [line.split() for line in lines]
                    else:
                        self.sRaw = [line.strip().split(delim) for line in fid]

                # Extract header and process the data
                headers = self.sRaw[0]

                # Clean headers and assign to reflection dictionary
                for i, header in enumerate(headers):
                    title = header.strip().lower()
                    title = re.sub(r"\.", "", title)
                    title = re.sub(r"[^a-zA-Z]", "", title)
                    title = re.sub(r"theta", "twotheta", title)
                    if len(title) == 1:
                        title = re.sub(r"^m", "mult", title)
                        title = re.sub(r"^f", "formfactor", title)
                    title = title.replace("dspc", "dspacing")

                    if title != "no":
                        self.data[title] = [row[i] for row in self.sRaw[1:]]

                # Convert h, k, l columns to 'hkl'
                self.data["hkl"] = np.array(
                    [
                        [
                            int(self.data["h"][i]),
                            int(self.data["k"][i]),
                            int(self.data["l"][i]),
                        ]
                        for i in range(len(self.data["h"]))
                    ]
                )
                for i in [
                    "hkl",
                    "h",
                    "k",
                    "l",
                    "twotheta",
                    "mult",
                    "dspacing",
                    "int",
                    "formfactor",
                ]:
                    self.data[i] = np.array(self.data[i], dtype=float)

                break
            except UnicodeDecodeError:
                logging.info(f"Error decoding with {encoding}, trying next encoding...")
            except Exception as e:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.error(
                        f"Error opening or processing the file {self.file.name}: {e}"
                    )
                break

    def display_struct(self, max_level=None) -> str:
        return "\n".join(["\t".join(row) for row in self.sRaw]) if self.sRaw else ""


class loadFile:
    """Unified interface for loading and interacting with different file types.

    Args:
        filepath: Path to the file to be loaded

    Attributes:
        filepath: Path object representing the file location
        handler: The file-specific handler instance
    """

    # Define supported file extensions for each type
    EXTENSION_MAP = {
        ".h5": "HDF5",
        ".hdf5": "HDF5",
        ".mat": "MAT",
        ".cif": "CIF",
        ".csv": "REFLECTION",
        ".dat": "REFLECTION",
    }

    HANDLERS = {
        "HDF5": LoadH5File,
        "MAT": LoadMatFile,
        "CIF": LoadCIFFile,
        "REFLECTION": LoadReflexionFile,
    }

    def __init__(self, filepath: Union[str, Path], from_mat: bool = False) -> None:
        """Initialize the loader with the specified file path."""
        self.filepath = Path(filepath)
        self._validate_file()
        self.file_type = self._detect_file_type()
        self.handler = self._create_handler(from_mat)

    def _validate_file(self) -> None:
        """Validate that the file exists and is readable."""
        # TODO: debug mode to display such kind of errors
        if not self.filepath.exists():
            if logger.isEnabledFor(logging.DEBUG):
                logger.error(FileNotFoundError(f"File not found: {self.filepath}"))
            return
        if not self.filepath.is_file():
            if logger.isEnabledFor(logging.DEBUG):
                logger.error(ValueError(f"Path is not a file: {self.filepath}"))
            return
        if not os.access(self.filepath, os.R_OK):
            if logger.isEnabledFor(logging.DEBUG):
                logger.error(PermissionError(f"File not readable: {self.filepath}"))

    def _detect_file_type(self) -> FileType:
        """Detect file type from extension and content."""
        suffix = self.filepath.suffix.lower()
        if suffix in self.EXTENSION_MAP:
            output = FileType[self.EXTENSION_MAP[suffix]]
        else:
            output = None

        if output and output is not FileType.MAT:
            return output

        # Fallback content detection
        with open(self.filepath, "rb") as f:
            header = f.read(1024)
            if b"HDF" in header or b"MATLAB 7.3" in header:
                return FileType.HDF5
            elif b"MATLAB" in header:
                return FileType.MAT

        return FileType.UNKNOWN

    def _create_handler(self, from_mat: bool = None):
        """Create appropriate file handler."""
        if self.file_type == FileType.UNKNOWN:
            return None

        handler_class = self.HANDLERS.get(self.file_type.name)
        if not handler_class:
            return None

        try:
            return handler_class(self.filepath, from_mat)
        except Exception as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.error(f"Failed to create handler: {str(e)}")
            return None

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying handler.

        Args:
            name: Name of the attribute to access

        Returns:
            The requested attribute from the handler

        Raises:
            AttributeError: If the handler doesn't exist or doesn't have the attribute
        """
        if self.handler is None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.error(
                    AttributeError(
                        f"'{self.__class__.__name__}' object has no handler for '{self.filepath}'"
                    )
                )
        try:
            return getattr(self.handler, name)
        except AttributeError:
            if logger.isEnabledFor(logging.DEBUG):
                logger.error(
                    AttributeError(
                        f"'{self.__class__.__name__}' object and its handler have no attribute '{name}'"
                    )
                )

    def get_size(self, key: str) -> Union[Optional[tuple[int, ...]], Optional[int]]:
        """Get the size/dimensions of a table, numpy array, or HDF5 group in the file.

        Args:
            key: Key/identifier for the data structure or group

        Returns:
            Tuple of dimensions if the key points to a table/array with multiple dimensions,
            int if it's a single dimension,
            number of members if it's a group,
            None otherwise
        """
        if self.handler is None:
            return None

        try:
            if hasattr(self.handler, "get_size"):
                return self.handler.get_size(key)
        except Exception as e:
            logging.warning(f"Error getting size for key '{key}': {str(e)}")

        return None

    def get_description(
        self, key: Optional[str] = None, default: Optional[Any] = None
    ) -> Optional[Union[str, list[str]]]:
        """Retrieve the Description attribute for a given key if available."""
        if self.handler is None:
            return default

        try:
            if hasattr(self.handler, "get_description"):
                return self.handler.get_description(key, default)
        except Exception as e:
            logging.warning(f"Error getting description for key '{key}': {str(e)}")

        return default

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the file data.

        Args:
            key: Key/identifier for the value to retrieve
            default: Default value to return if key not found

        Returns:
            The requested value or default if not found
        """
        if self.handler is None:
            return default

        try:
            if hasattr(self.handler, "get_value"):
                return self.handler.get_value(key, default)
        except Exception as e:
            logging.warning(f"Error getting value for key '{key}': {str(e)}")

        return default

    def get_keys(self, key: Optional[str] = None) -> list[str]:
        """Get available keys from the file data.

        Args:
            key: Optional specific key to query for subkeys

        Returns:
            List of available keys (empty list if none available)
        """
        if self.handler is None:
            return []

        try:
            if hasattr(self.handler, "get_keys"):
                return self.handler.get_keys(key)
        except Exception as e:
            logging.warning(f"Error getting keys for '{key}': {str(e)}")

        return []

    def display_struct(self, max_level: int = 3) -> str:
        """Display the structure of the loaded file.

        Args:
            max_level: Maximum depth level to display

        Returns:
            String representation of the file structure (empty string if unavailable)
        """
        if self.handler is None:
            return ""

        try:
            if hasattr(self.handler, "display_struct"):
                return self.handler.display_struct(max_level=max_level)
        except Exception as e:
            logging.warning(f"Error displaying structure: {str(e)}")

        return ""

    def __repr__(self) -> str:
        """Return a string representation of the loader."""
        return f"{self.__class__.__name__}(filepath='{self.filepath}')"

    def validate(self) -> bool:
        """Validate the file content matches its type."""
        try:
            if self.file_type == FileType.HDF5:
                with h5py.File(self.filepath, "r") as f:
                    return True
            elif self.file_type == FileType.MAT:
                with open(self.filepath, "rb") as f:
                    return scio.whosmat(f) is not None
            # Add other validations...
            return True
        except Exception:
            return False


# Example usage
if __name__ == "__main__":
    from esrf_statusgui.file_utils.paths import visitor_path

    h5_file_path = "/data/id11/inhouse2/test_data_DCT/Ti7Al_Round_robin/PROCESSED_DATA/sam_19/2024_10_18_sam_19_redo_dct1_REF/parameters.h5"
    # h5_file_path = '/data/id11/inhouse2/test_data_DCT/Ti7Al_Round_robin/PROCESSED_DATA/sam_19/2024_10_18_sam_19_redo_dct1_REF/4_grains/sample.h5'
    h5_file_path = visitor_path(
        "ma6062",
        "id11",
        "20240711",
        "PROCESSED_DATA",
        "Ti_06_d",
        "Ti_06_d_dct_160N",
        "parameters.h5",
    )
    h5_handler = loadFile(h5_file_path)
    print(h5_handler.get_value("cryst/latticepar"))
    print(h5_handler.display_struct())
    print("phases" in h5_handler.get_keys())

    pass
