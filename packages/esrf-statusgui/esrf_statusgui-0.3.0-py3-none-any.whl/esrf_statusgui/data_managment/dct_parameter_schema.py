"""Parameter schema definitions for DCT parameters."""

import logging
from typing import Any, Optional, Union

import numpy as np

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path


class InformationField:
    """Descriptor that lazily materializes Information nodes on instances."""

    def __init__(
        self,
        info: str = "",
        type_: Any = bool,
        default: Any = None,
        hdf5_attributes: Optional[dict[str, Any]] = None,
        python_type: Optional[type] = None,
    ):
        self.info = info
        self.matlab_class = type_ if isinstance(type_, str) else None
        self.python_type = python_type
        if self.matlab_class is None and self.python_type is None:
            self.python_type = type_
        self.default = default
        self.hdf5_attributes = dict(hdf5_attributes or {})
        self.name: Optional[str] = None
        self.storage_name: Optional[str] = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.storage_name = f"_{name}"

    def __get__(self, instance: Any, owner: Optional[type] = None) -> Any:
        if instance is None:
            return self
        if self.storage_name not in instance.__dict__:
            matlab_type = (
                self.matlab_class if self.matlab_class is not None else self.python_type
            )
            instance.__dict__[self.storage_name] = Information(
                self.info,
                matlab_type,
                self.default,
                dict(self.hdf5_attributes),
                python_type=self.python_type,
            )
        return instance.__dict__[self.storage_name]

    def __set__(self, instance: Any, value: Any) -> None:
        if isinstance(value, Information):
            instance.__dict__[self.storage_name] = value
        else:
            self.__get__(instance, type(instance)).value = value


class BaseParameters:
    """A base class for parameter management with comparison, merging, and content inspection capabilities."""

    def __init__(self) -> None:
        self._initialize_information_fields()

    def _initialize_information_fields(self) -> None:
        """Instantiate all declared Information fields for this instance."""
        for name in self._iter_information_field_names():
            getattr(self, name)

    @classmethod
    def _iter_information_field_names(cls) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()
        for klass in reversed(cls.__mro__):
            for attr_name, attr_value in klass.__dict__.items():
                if isinstance(attr_value, InformationField) and attr_name not in seen:
                    names.append(attr_name)
                    seen.add(attr_name)
        return names

    def compare(self, other: "BaseParameters") -> dict[str, tuple[Any, Any]]:
        """Compare this object with another instance of the same class.

        Args:
            other: Another instance of BaseParameters to compare with

        Returns:
            Dictionary of differences where keys are attribute paths and values are tuples of differing values
        """
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Can only compare with other {self.__class__.__name__} instances"
            )

        differences = {}
        self._compare_attributes(self, other, differences)
        return differences

    def _compare_attributes(
        self,
        obj1: Any,
        obj2: Any,
        differences: dict[str, tuple[Any, Any]],
        path: str = "",
    ) -> None:
        """Recursively compare attributes between two objects.

        Args:
            obj1: First object to compare
            obj2: Second object to compare
            differences: Dictionary to store found differences
            path: Current attribute path for nested comparisons
        """
        attrs = set(vars(obj1).keys() | set(vars(obj2).keys()))

        for attr in sorted(attrs):
            current_path = f"{path}.{attr}" if path else attr

            # Handle cases where attribute exists in only one object
            if attr not in vars(obj1):
                differences[current_path] = (None, getattr(obj2, attr))
                continue
            if attr not in vars(obj2):
                differences[current_path] = (getattr(obj1, attr), None)
                continue

            value1 = getattr(obj1, attr)
            value2 = getattr(obj2, attr)

            # Handle Information objects specially
            if isinstance(value1, Information) and isinstance(value2, Information):
                self._compare_information_objects(
                    value1, value2, differences, current_path
                )
                continue

            # Handle numpy arrays and lists
            if isinstance(value1, (np.ndarray, list)) or isinstance(
                value2, (np.ndarray, list)
            ):
                self._compare_sequences(value1, value2, differences, current_path)
                continue

            # Default comparison
            if value1 != value2:
                differences[current_path] = (value1, value2)

    def _compare_information_objects(
        self,
        info1: "Information",
        info2: "Information",
        differences: dict[str, tuple[Any, Any]],
        path: str,
    ) -> None:
        """Special comparison for Information objects."""
        # Handle cases where one value is None and the other isn't
        if (info1.value is None) ^ (info2.value is None):
            differences[path] = (info1, info2)
            return

        # Skip if both values are None
        if info1.value is None and info2.value is None:
            return

        # Handle sequence types differently
        if isinstance(info1.value, (list, np.ndarray)) or isinstance(
            info2.value, (list, np.ndarray)
        ):
            self._compare_sequences(info1.value, info2.value, differences, path)
        elif info1.value != info2.value:
            differences[path] = (info1.value, info2.value)

    def _compare_sequences(
        self,
        seq1: Union[list, np.ndarray],
        seq2: Union[list, np.ndarray],
        differences: dict[str, tuple[Any, Any]],
        path: str,
    ) -> None:
        """Compare sequence-like objects (lists, numpy arrays)."""
        # Handle case where one is sequence and other isn't
        if isinstance(seq1, (list, np.ndarray)) ^ isinstance(seq2, (list, np.ndarray)):
            differences[path] = (seq1, seq2)
            return

        # Compare numpy arrays
        if isinstance(seq1, np.ndarray) and isinstance(seq2, np.ndarray):
            if seq1.shape != seq2.shape or not np.array_equal(seq1, seq2):
                differences[path] = (seq1, seq2)
        # Compare lists
        elif isinstance(seq1, list) and isinstance(seq2, list):
            if len(seq1) != len(seq2) or any(x != y for x, y in zip(seq1, seq2)):
                differences[path] = (seq1, seq2)

    def merge(self, to_merge: "BaseParameters") -> None:
        """Merge attributes from another instance into this one.

        Args:
            to_merge: Another instance to merge attributes from
        """
        if not isinstance(to_merge, self.__class__):
            raise TypeError(
                f"Can only merge with other {self.__class__.__name__} instances"
            )

        for attr_name, attr_value in vars(to_merge).items():
            if attr_name == "get_keys":
                continue

            if hasattr(self, attr_name):
                self._merge_existing_attribute(attr_name, attr_value)
            else:
                self._merge_new_attribute(attr_name, attr_value)
                logging.info(
                    f"The parameter {attr_name} was added to the class {type(self).__name__}"
                )

    def _merge_existing_attribute(self, attr_name: str, new_value: Any) -> None:
        """Handle merging of an attribute that already exists."""
        current_value = getattr(self, attr_name)

        if isinstance(new_value, Information):
            if new_value() is not None:
                if isinstance(current_value, Information):
                    current_value.value = new_value()
                else:
                    setattr(self, attr_name, new_value())
        elif isinstance(new_value, BaseParameters):
            current_value.merge(new_value)
        elif isinstance(current_value, Information):
            if hasattr(new_value, "value") and new_value.value is not None:
                current_value.value = new_value.value
            elif new_value is not None:
                current_value.value = new_value
        elif hasattr(new_value, "value") and new_value.value is not None:
            setattr(self, attr_name, new_value.value)
        elif new_value is not None:
            setattr(self, attr_name, new_value)

    def _merge_new_attribute(self, attr_name: str, new_value: Any) -> None:
        """Handle merging of a new attribute that doesn't exist yet."""
        if isinstance(new_value, Information):
            if new_value() is not None:
                setattr(self, attr_name, new_value)
        elif hasattr(new_value, "value") and new_value.value is not None:
            setattr(
                self, attr_name, Information("", type(new_value.value), new_value.value)
            )
        elif new_value is not None:
            setattr(self, attr_name, Information("", type(new_value), new_value))

    def print_index(
        self, as_string: bool = False, max_depth: int = 3, local_root: str = "/"
    ) -> Optional[str]:
        """Print or return a formatted index of the dataset content.

        Args:
            as_string: If True, return as string instead of printing
            max_depth: Maximum depth to display (currently not fully implemented)
            local_root: Root path to display (currently not fully implemented)

        Returns:
            Formatted string if as_string=True, otherwise None
        """
        s = [
            "Dataset Content Index:",
            "------------------------",
            f"index printed with max depth `{max_depth}` and under local root `{local_root}`\n",
        ]

        if not hasattr(self, "content_index"):
            s.append("No content index available")
            return self._format_output(s, as_string)

        for key, value in sorted(self.content_index.items()):
            path = value[0] if isinstance(value, list) else value
            s.append(f"\tName : {key:40}  H5_Path : {path}")

            if hasattr(self, "aliases") and key in self.aliases:
                aliases = " ".join(f"`{alias}`" for alias in self.aliases[key])
                s.append(f"\t        {key} aliases --> {aliases}")

        return self._format_output(s, as_string)

    def print_dataset_content(
        self, as_string: bool = False, max_depth: int = 3, short: bool = False
    ) -> Optional[str]:
        """Print or return a structured overview of the dataset content.

        Args:
            as_string: If True, return as string instead of printing
            max_depth: Maximum depth to display
            short: If True, use shorter format

        Returns:
            Formatted string if as_string=True, otherwise None
        """
        s = [
            "Dataset Content:",
            "-----------------",
            f"Content printed with max depth `{max_depth}`\n",
        ]

        if not hasattr(self, "content_index"):
            s.append("No content available")
            return self._format_output(s, as_string)

        for key, value in sorted(self.content_index.items()):
            path = value[0] if isinstance(value, list) else value
            if short:
                s.append(f"\tName: {key:40} H5_Path: {path}")
            elif max_depth > 0:
                s.append(f"\tName: {key:40} H5_Path: {path}")

        return self._format_output(s, as_string)

    def _format_output(self, lines: list, as_string: bool) -> Optional[str]:
        """Helper method to format output for print methods."""
        output = "\n".join(lines)
        if not as_string:
            print(output)
            return None
        return output

    def items(self) -> list:
        """Get items from content_index if available.

        Returns:
            List of items from content_index or empty list if not available
        """
        return (
            list(self.content_index.items()) if hasattr(self, "content_index") else []
        )

    def __contains__(self, name: str) -> bool:
        """Check if a name refers to an existing HDF5 node in the dataset.

        Args:
            name: Name or path to check

        Returns:
            True if the name exists in the dataset, False otherwise
        """
        path = self._name_or_node_to_path(name)
        return (
            path is not None and hasattr(self, "h5_dataset") and path in self.h5_dataset
        )

    def __getitem__(self, key: str) -> Any:
        """Implement dictionary-like access to the parameters.

        Args:
            key: Key to access

        Returns:
            The requested item in the appropriate format

        Raises:
            KeyError: If the key doesn't exist
            AttributeError: If required attributes are missing
        """
        if not hasattr(self, "h5_dataset"):
            raise AttributeError("h5_dataset attribute not available")

        if self._is_field(key):
            return self.get_field(key)
        elif self._is_array(key):
            return self.get_node(key, as_numpy=True)
        elif self._is_group(key):
            return self.get_node(key, as_numpy=False)
        else:
            raise KeyError(f"Key '{key}' not found")

    def __repr__(self) -> str:
        """Return a comprehensive string representation of the dataset."""
        parts = []

        try:
            parts.append(self.print_index(as_string=True, max_depth=3))
        except Exception as e:
            parts.append(f"Error printing index: {str(e)}")

        parts.append("")  # Add empty line between sections

        try:
            parts.append(
                self.print_dataset_content(as_string=True, max_depth=3, short=True)
            )
        except Exception as e:
            parts.append(f"Error printing dataset content: {str(e)}")

        return "\n".join(parts)

    def __call__(self) -> str:
        """Allow the instance to be called like a function to get its representation."""
        return self.__repr__()


class Version(BaseParameters):
    number = InformationField(
        "Version number of this parameters structure",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )

    def __init__(self):
        super().__init__()
        self.info = "Version number of parameters file"


class Diffractometer(BaseParameters):
    angles_basetilt = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )
    angles_rotation = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )
    angles_samtilt_bot = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )
    angles_samtilt_top = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )
    origin_basetilt = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    origin_rotation = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    origin_samtilt_bot = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    origin_samtilt_top = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    axes_basetilt = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    axes_rotation = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    axes_samtilt_bot = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    axes_samtilt_top = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    limits_samtilt_bot = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 2)}
    )
    limits_samtilt_top = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 2)}
    )
    motor_basetilt = InformationField(
        "", "char", None, {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 6)}
    )
    motor_rotation = InformationField(
        "", "char", None, {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 6)}
    )
    motor_samtilt_bot = InformationField(
        "", "char", None, {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 5)}
    )
    motor_samtilt_top = InformationField(
        "", "char", None, {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 5)}
    )
    motor_samtx = InformationField(
        "", "char", None, {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 5)}
    )
    motor_samty = InformationField(
        "", "char", None, {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 5)}
    )
    motor_samtz = InformationField(
        "", "char", None, {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 5)}
    )
    num_axes = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )
    shifts_sam_stage = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )

    def __init__(self):
        super().__init__()
        self.info = ""


class Acq(BaseParameters):
    collection_dir = InformationField(
        "Collection directory",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 84)},
        python_type=Path,
    )
    name = InformationField(
        "Name of the dataset",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 20)},
    )
    dir = InformationField(
        "Directory in which to analyse the data",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 94)},
        python_type=Path,
    )
    dir_new = InformationField("Directory in which to analyse the data", Path, None)
    date = InformationField(
        "Date of self.acquisition",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 32)},
    )
    xdet = InformationField(
        "Detector ROI size X or U (raw image size in pixels)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    ydet = InformationField(
        "Detector ROI size Y or V (raw image size in pixels)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    nproj = InformationField(
        "Number of images in *180 DEGREES* of scan",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    refon = InformationField(
        "References after how many images",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    nref = InformationField(
        "How many reference images in a group",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    ndark = InformationField(
        "How many dark images taken",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    pixelsize = InformationField(
        "Detector pixelsize (mm/pixel)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    count_time = InformationField(
        "Image integration time (s)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    energy = InformationField(
        "Beam energy (keV)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    dist = InformationField(
        "Sample-detector distance (mm) [computed]",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    sensortype = InformationField(
        "Camera type ('frelon'/'kodak4mv1'/'marana')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 7)},
    )
    objective = InformationField(
        "Camera objective (5.0 7.5 10.0 20.0)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    eyepiece = InformationField("Camera eyepiece (0.9 1.0 2.0 2.5)", float, None)
    type = InformationField(
        "DCT scan type ('360degree','180degree', etc)",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 9)},
    )
    interlaced_turns = InformationField(
        "Interlaced scan? 0 for normal scan, 1 for one extra turn, etc",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    mono_tune = InformationField(
        "Monochromator was tuned after N reference groups, or 0 for not tuned",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    rotation_axis = InformationField(
        "Rotation axis orientation ('vertical'/'horizontal')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 8)},
    )
    distortion = InformationField(
        "Distortion correction file with path (or 'none')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 54)},
        python_type=Path,
    )
    beamchroma = InformationField(
        "Beam chromaticity ('mono'/'poly')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 4)},
    )
    no_direct_beam = InformationField(
        "Special scan with no direct beam (taper frelon, offset detector)?",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    rotation_direction = InformationField(
        "Horizontal axis scan - rotate images ('clockwise'/'counterclockwise')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 8)},
    )
    detector_definition = InformationField(
        "Definition of the detector type ('inline'/'vertical')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 6)},
    )
    collection_dir_old = InformationField(
        "[Computed] Old collection directory",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 94)},
        python_type=Path,
    )
    rotu = InformationField(
        "U coordinate of rotation axis projection in image [computed] ??? equals to rotx ???",
        float,
        None,
    )
    rotx = InformationField(
        "V coordinate of rotation axis projection in image [computed] ??? equals to rotu ???",
        float,
        None,
    )
    bb = InformationField(
        "Sample bbox symm. around rot. axis [umin vmin usize vsize]}; reconstructed sample volume has size [bb(3) bb(3) bb(4)]",
        float,
        None,
    )
    bbdir = InformationField(
        "Direct beam bounding box [umin vmin usize vsize]",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 4)},
    )
    nof_phases = InformationField(
        "Number of phases in sample to be analysed",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    true_detsizeu = InformationField(
        "True detector X or U size before cropping (pixels)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    true_detsizev = InformationField(
        "True detector Y or V size before cropping (pixels)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    detroi_u_off = InformationField(
        "X or U offset of cropped detector ROI (the corner pixel)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    detroi_v_off = InformationField(
        "Y or V offset of cropped detector ROI (the corner pixel)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    pair_tablename = InformationField(
        "Table name for spot pairs",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 25)},
    )
    calib_tablename = InformationField(
        "[not used] Table name for calibration of spot pairs matching",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 25)},
    )
    flip_images = InformationField(
        "Do you want to flip the images left-right for some reason?",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    maxradius = InformationField(
        "[Computed] Maximum active radius of the detector, for example in case of vignetting",
        float,
        None,
    )
    online = InformationField(
        "Is the analysis online?",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    sample_tilts = InformationField(
        "Sample tilts (samr): y, x (in order)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 2)},
    )
    sample_shifts = InformationField(
        "Sample shifts (samt): x, y, z (in order)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    nproj_basetilt = InformationField("Topotomo number of basetilt steps", int, None)
    range_basetilt = InformationField("Topotomo basetilt range", float, None)
    pl_ind = InformationField(
        "Topotomo plane normal index, with respect to first self.acquisition",
        float,
        None,
    )
    masterdir = InformationField("Parameters copied from directory", Path, None)
    scan_type = InformationField(
        "Acquisition macro: {'ebs_tomo','fscan_v1','finterlaced'}",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 8)},
    )
    rotation_name = InformationField(
        "", "char", None, {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 6)}
    )
    start_grp = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )
    beamline = InformationField(
        "Beamline of acquisition",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 9)},
    )
    flat = InformationField(
        "Group number for flats in the raw h5 file",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 2)},
        python_type=list,
    )
    dark = InformationField(
        "Group number for darks in the raw h5 file",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        python_type=list,
    )
    projections = InformationField(
        "Group number for DCT projectionss in the raw h5 file",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        python_type=list,
    )

    def __init__(self):
        super().__init__()
        self.info = "Acquisition parameters"
        self.motors = self.Motors("Scan motor information")

    class Motors(BaseParameters):
        R2Mh = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        R2Mv = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        RMh = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        RMv = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        attrz = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        atty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        benddh = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        benddv = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        benduh = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        benduv = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        bigy = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        blowx = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        cpm18 = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        cpm18t = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d1focus = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d1rotc = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d1rz = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d1ty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d1tz = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d1x = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d1y = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d1z = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d2focus = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d2rotc = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d2ty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d2tz = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d3focus = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d3rotc = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d3tx = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d3ty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d3tz = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d3x = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d3y = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d3z = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        d4focus = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        diffry = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        diffrz = InformationField(
            "",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (7200, 1)},
        )
        diffty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        difftz = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        diodey = InformationField("", float, None)
        ffdtx1 = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        ffdtx2 = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        ffdty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        ffdty1 = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        ffdty2 = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        ffdtyrot = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        ffdtz1 = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        fshuty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        furnace_z = InformationField("", float, None)
        kbz = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        nfdtx = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s7hg = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s7vg = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s7y = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s7z = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8b = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8d = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8f = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8hg = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8ho = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8pit = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8u = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8vg = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8vo = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8x = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8y = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8yaw = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        s8z = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        samrx = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        samry = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        samtx = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        samty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        samtz = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        samx = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        samy = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        scint = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        tfpitch = InformationField("", float, None)
        tfy = InformationField("", float, None)
        tfz = InformationField("", float, None)
        tfz1 = InformationField("", float, None)
        tfz2 = InformationField("", float, None)
        u22 = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        xroty = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        xtransy = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        stress = InformationField("", float, None)

        def __init__(self, info=None):
            super().__init__()
            self.info = info


class Xop(BaseParameters):
    twotheta = InformationField("Twotheta angle (2*Bragg angle)", float, None)
    dspacing = InformationField("d-spacing", float, None)
    int = InformationField("Intensity", float, None)
    formfactor = InformationField("Form factor", float, None)
    mult = InformationField("Multiplicity", int, None)
    hkl = InformationField("hkl Miller indexes", int, None)
    filename = InformationField("XOP/Diamond crystallographic file", str, None)
    xop_dir = InformationField("Directory for the XOP input file", Path, None)

    def __init__(self):
        super().__init__()
        self.info = "xop for phase 1}; if necessary the same for other phases"


class Cryst(BaseParameters):
    name = InformationField(
        "Name of phase to display (e.g. Al, Austenite, Beta_Titanium)",
        str,
        None,
    )
    composition = InformationField(
        "Chemical composition of phase (e.g BaTiO3)", str, None
    )
    material = InformationField(
        "Distinctive reference name of sample material (e.g AlLi_July2010_recrystallized)",
        str,
        None,
    )
    latticepar = InformationField(
        "Lattice parameters [a b c alpha beta gamma] (angstrom, deg)",
        float,
        None,
    )
    spacegroup = InformationField("Crystallographic spacegroup", float, None)
    hermann_mauguin = InformationField(
        "[Computed] Hermann Mauguin short symbol", str, None
    )
    crystal_system = InformationField(
        "[Computed] Crystallographic crystal system", str, None
    )
    lattice_system = InformationField(
        "[Computed] Crystallographic lattice system", str, None
    )
    opsym = InformationField(
        "[Computed] Symmetry operators read from .dsv/.dat file (Diamond/XOP calculation)",
        list,
        None,
    )
    hkl = InformationField(
        "[Computed] List of {hkl} families list to be considered", float, None
    )
    hklsp = InformationField(
        "[Computed] List of signed (specific) {hkl} families to be considered",
        float,
        None,
    )
    theta = InformationField(
        "[Computed] Bragg angles theta corresponding to hkl and self.acq. energy",
        float,
        None,
    )
    thetasp = InformationField(
        "[Computed] Bragg angles theta corresponding to hklsp and self.acq. energy",
        float,
        None,
    )
    dspacing = InformationField(
        "[Computed] D-spacings corresponding to hkl", float, None
    )
    dspacingsp = InformationField(
        "[Computed] D-spacings corresponding to hklsp", float, None
    )
    thetatype = InformationField(
        "[Computed] Scalar indices of the hkl families (and theta-s)",
        float,
        None,
    )
    thetatypesp = InformationField(
        "[Computed] Scalar index of the given hkl family (one of thetatype)",
        float,
        None,
    )
    int = InformationField(
        "[Computed] Intensity of reflection corresponding to hkl", float, None
    )
    intsp = InformationField(
        "[Computed] Intensity of reflection corresponding to hklsp", float, None
    )
    mult = InformationField(
        "[Computed] Multiplicity of reflections from the given hkl family",
        float,
        None,
    )
    usedfam = InformationField("[Computed] Used hkl family in matching", bool, None)
    formfactor = InformationField(
        "[Computed] Formfactor of the hkl families", float, None
    )

    def __init__(self):
        super().__init__()
        self.info = "Crystallography - Data of all phases are stored in the array list.cryst: \n list.cryst(1), list.cryst(2), etc.\n In case of one phase only, both list.cryst(1) and list.cryst can be used in Matlab to refer to that phase."
        self.symm = self.Symm(
            "[Computed] Symmetry operators for the given crystal system"
        )

    class Symm(BaseParameters):
        g3 = InformationField("[Computed] Set of symmetry operators (3x3)", float, None)
        g = InformationField("[Computed] Set of symmetry operators (4x4)", float, None)

        def __init__(self, g3=None, g=None, info=None):
            super().__init__()
            self.info = info


class LabGeo(BaseParameters):
    beamdir = InformationField(
        "Beam direction in LAB reference (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    rotdir = InformationField(
        "Rotation axis direction in LAB (unit row vector); omega is right-handed rotation",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    rotpos = InformationField(
        "Rotation axis position (arbitrary point on axis) in LAB",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    samenvtop = InformationField(
        "[Computed] Distance from rotpos to top of sample envelope along rotdir (signed scalar in lab units)",
        float,
        None,
    )
    samenvbot = InformationField(
        "[Computed] Distance from rotpos to bottom of sample envelope along rotdir (signed scalar in lab units)",
        float,
        None,
    )
    samenvrad = InformationField(
        "[Computed] Radius of sample envelope (in lab units)", float, None
    )
    labunit = InformationField(
        "LAB units (default is mm) [for records only]",
        "char",
        "mm",
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 2)},
    )
    deflabX = InformationField(
        "Description how Lab X direction was chosen [for records only]",
        "char",
        "Along the beam direction.",
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 25)},
    )
    deflabY = InformationField(
        "Description how Lab Y direction was chosen [for records only]",
        "char",
        "Right-handed from Y=cross(Z,X).",
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 31)},
    )
    deflabZ = InformationField(
        "Description how Lab Z direction was chosen [for records only]",
        "char",
        "Along rotation axis. Positive away from sample stage.",
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 53)},
    )
    detsizeu = InformationField("Number of pixels along the u direction", float, None)
    detsizev = InformationField("Number of pixels along the v direction", float, None)
    pixelsizeu = InformationField(
        "Detector pixel size in direction U (lab unit/pixel)", float, None
    )
    pixelsizev = InformationField(
        "Detector pixel size in direction V (lab unit/pixel)", float, None
    )
    detrefu = InformationField(
        "Detector reference point U coordinate in pixels", float, None
    )
    detrefv = InformationField(
        "Detector reference point V coordinate in pixels", float, None
    )
    detanglemin = InformationField(
        "[Computed] Detector minimum 2Theta angle to consider", float, None
    )
    detanglemax = InformationField(
        "[Computed] Detector maximum 2Theta angle to consider", float, None
    )
    detrefpos = InformationField(
        "Detector reference point (usually center) position in LAB", float, None
    )
    detdiru = InformationField(
        "Detector U direction in LAB (unit row vector)", float, None
    )
    detdirv = InformationField(
        "Detector V direction in LAB (unit row vector)", float, None
    )
    detscaleu = InformationField("", float, None)
    detscalev = InformationField("", float, None)
    readout_delay_sec = InformationField(
        "Readout delay between the extremities across the detector image [sec]",
        float,
        None,
    )
    readout_delay = InformationField(
        "Readout delay between the extremities across the detector image [sec]",
        float,
        None,
    )
    readout_direction = InformationField(
        "Readout direction across the detector image towards the pixels that are read out later (''/''-u''/''+u''/''-v''/''+v'')",
        str,
        None,
    )
    Qdet = InformationField("", float, None)
    omstep = InformationField("", float, None)

    def __init__(self):
        super().__init__()
        self.info = "Parameters to describe the setup geometry - coordinates are given in the Lab reference"


class DetGeo(BaseParameters):
    detrefpos = InformationField(
        "Detector reference point (usually center) position in LAB",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    detrefu = InformationField(
        "Detector reference point U coordinate in pixels",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    detrefv = InformationField(
        "Detector reference point V coordinate in pixels",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    detdiru = InformationField(
        "Detector U direction in LAB (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    detdirv = InformationField(
        "Detector V direction in LAB (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    pixelsizeu = InformationField(
        "Detector pixel size in direction U (lab unit/pixel)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    pixelsizev = InformationField(
        "Detector pixel size in direction V (lab unit/pixel)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    detanglemin = InformationField(
        "[Computed] Detector minimum 2Theta angle to consider",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    detanglemax = InformationField(
        "[Computed] Detector maximum 2Theta angle to consider",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    detsizeu = InformationField(
        "Number of pixels along the u direction",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    detsizev = InformationField(
        "Number of pixels along the v direction",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    readout_delay_sec = InformationField(
        "Readout delay between the extremities across the detector image [sec]",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    readout_delay = InformationField(
        "Readout delay between the extremities across the detector image [sec]",
        float,
        None,
    )
    readout_direction = InformationField(
        "Readout direction across the detector image towards the pixels that are read out later (''/''-u''/''+u''/''-v''/''+v'')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 2)},
    )
    Qdet = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (2, 3)}
    )
    detnorm = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    detorig = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)}
    )
    detscaleu = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )
    detscalev = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )

    def __init__(self):
        super().__init__()
        self.info = "Parameters to describe the detector geometry"


class SamGeo(BaseParameters):
    orig = InformationField(
        "Lab coordinates of the origin of Sample reference",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    dirx = InformationField(
        "Lab coordinates of Sample axis X (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    diry = InformationField(
        "Lab coordinates of Sample axis Y (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    dirz = InformationField(
        "Lab coordinates of Sample axis Z (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    voxsize = InformationField(
        "Voxel sizes of the Sample reference along X,Y,Z (lab unit/voxel); size(1,3)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )

    def __init__(self):
        super().__init__()
        self.info = "Sample geometry parameters for matching and indexing"


class RecGeo(BaseParameters):
    orig = InformationField(
        "Lab coordinates of the origin of Reconstruction reference",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    dirx = InformationField(
        "Lab coordinates of Reconstruction axis X (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    diry = InformationField(
        "Lab coordinates of Reconstruction axis Y (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    dirz = InformationField(
        "Lab coordinates of Reconstruction axis Z (unit row vector)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    voxsize = InformationField(
        "Voxel sizes of the Reconstruction reference along X,Y,Z (lab unit/voxel); size(1,3)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )

    def __init__(self):
        super().__init__()
        self.info = "Reconstruction geometry parameters"


class Prep(BaseParameters):
    normalisation = InformationField(
        "How to normalise images ('none'/'margin'/'fullbeam')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 4)},
    )
    absint = InformationField(
        "Moving median interval in images for the direct beam (mod(total no. of projections, absint)=0)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    absrange = InformationField(
        "Moving median range in images for the direct beam (=n*2*absint)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    fullint = InformationField(
        "Moving median interval in images for the diffracted image (mod(total no. of projections, fullint)=0)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    fullrange = InformationField(
        "Moving median range in images for the diffracted image (=n*2*fullint)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    margin = InformationField(
        "Margin width for normalisation in direct beam (pixels)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    intensity = InformationField(
        "Assumed direct beam intensity of normalisation",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    filtsize = InformationField(
        "2D median filter size for full images [pixels x pixels]",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 2)},
    )
    drifts_pad = InformationField(
        "How to pad shifted images ('av' or value)",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 2)},
    )
    renumbered = InformationField(
        "[Computed] ...for interlaced scans",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    bbox = InformationField("[Computed] Sample bounding box in the images", float, None)
    correct_drift = InformationField(
        "we will shift images at the end of preprocessing, no shifting before flatfielding... ('required'/'not_required')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 12)},
    )
    udrift = InformationField(
        "[Computed] Values for shifting images in U direction to compensate sample drifts",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 7200)},
    )
    udriftabs = InformationField(
        "[Computed] Values for shifting abs images in U direction to compensate sample drifts",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 7200)},
    )
    vdrift = InformationField(
        "[Computed] Values for shifting images in V direction to compensate sample drifts",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 7200)},
    )
    totproj = InformationField("", float, None)

    def __init__(self):
        super().__init__()
        self.info = "Preprocessing"


class Seg(BaseParameters):
    bbox = InformationField(
        "Segmentation Bounding Box; segmentation is done excluding this area",
        float,
        None,
    )
    method = InformationField(
        "Segmentation method: 'singlethr' - single threshold; 'doublethr' - double threshold",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 9)},
    )
    thr_single = InformationField(
        "Threshold for 'single threshold' segmentation",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_seed = InformationField(
        "Seed threshold to find potential blobs (for double threshold)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_grow_rat = InformationField(
        "Relative intensity threshold for growing seeds (for double threshold)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_grow_low = InformationField(
        "Lower absolute limit of thr_grow_rat for growing seeds (for double threshold)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_grow_high = InformationField(
        "Upper absolute limit of thr_grow_rat for growing seeds (for double threshold)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    seedminarea = InformationField(
        "Minimum seed size, in pixels, that will be considered (for double threshold). For the new segmentation, it is the number of connected pixels in 3D!",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    minsize = InformationField(
        "Minimum accepted volume of a blob in voxels (for single threshold)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    omintlimmin = InformationField(
        "Min. relative intensity in omega image stack to create difspots from blobs",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    omintlimtail = InformationField(
        "Relative integrated intensity for tail cut off to create difspots from blobs",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    minblobsize = InformationField(
        "Minimum accepted blob size (for double threshold)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    maxblobsize = InformationField(
        "Maximum accepted blob size (for double threshold)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    extendblobinc = InformationField(
        "Size of incremental blob bbox extension (for double threshold)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 3)},
    )
    background_subtract = InformationField(
        "Offset the remaining median value of each full image to zero (computed and applied outside seg.bbox)",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    overlaps_removed = InformationField(
        "Removing of overlaps",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    difspotmask = InformationField(
        "Mask used to create difspot.edf from blob ('none'/'blob2D'/'blob3D')",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 10)},
    )
    debug = InformationField(
        "Display messages",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    writeblobs = InformationField(
        "Write difblobs to the table",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    writespots = InformationField(
        "Write difspot metadata to the table",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    writeedfs = InformationField(
        "Save difspots as edf files",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    writehdf5 = InformationField(
        "Save difspots as hdf5 files",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    wrapping = InformationField(
        "For 360degree data, wrap from the last image back to the first image",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    segmentation_stack_size = InformationField(
        "How many images in memory? (1000 images approx 32Gb)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    background_subtract_accelerate = InformationField(
        "Calculate median on a subset of pixels (faster)",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    skip = InformationField(
        "Skip interactive part",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    write_sub_volumes = InformationField(
        "Output the segmentation results as 3D volumes",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 7)},
    )
    write_same_size = InformationField("", bool, None)

    def __init__(self):
        super().__init__()
        self.info = "Segmentation"


class Match(BaseParameters):
    thr_theta = InformationField(
        "Max. theta angular deviation for a match (in degrees)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_theta_scale = InformationField(
        "Linear scaling for thr_theta: thr = thr_theta + thr_theta_scale*theta",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_max_offset = InformationField(
        "Max. centroid image offset for a match (in no. of images)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_ext_offset = InformationField(
        "Max. offset of first and last image in omega stack (in no. of images)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_genim_offset = InformationField(
        "Max. offset for at least one of (centroid,first,last) image (in no. of images)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_intint = InformationField(
        "Max. intensity ratio for a match (>1)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_area = InformationField(
        "Max. area ratio for a match (>1)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thr_bbsize = InformationField(
        "Max. bbox size ratio (for both U and V) for a match (>1)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    minsizeu = InformationField(
        "Min. bbox U size in pixels for spots to be considered for matching",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    minsizev = InformationField(
        "Min. bbox V size in pixels for spots to be considered for matching",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    addconstr = InformationField(
        "Additional constraints for spots to be considered (mysql command text)",
        str,
        None,
    )
    thr_meanerror = InformationField(
        "Mean error under which a match is accepted",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    thetalimits = InformationField(
        "Allowed theta subranges in degrees: [min max] size (n,2)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 2)},
    )
    uniquetheta = InformationField(
        "Theta tolerance for distinguishing overlapping {hkl} reflections (in degrees)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )

    def __init__(self):
        super().__init__()
        self.info = "Friedel pair matching"


class Index(BaseParameters):
    discard = InformationField(
        "Vector of pair id-s to be discarded in indexing", float, None
    )
    forcemerge = InformationField("Cell array of grain id-s to be merged", float, None)

    def __init__(self):
        super().__init__()
        self.info = "Indexter"
        self.strategy = self.Strategy("Strategy for indexter containing all parameters")

    class Strategy(BaseParameters):
        iter = InformationField(
            "Number of iteration loops",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )
        rfzext = InformationField(
            "Extension of Rodrigues space for input reflections to account for projections errors",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )

        def __init__(self, info=None):
            super().__init__()
            self.info = info
            self.b = self.B("Parameters for finding grains")
            self.m = self.M("Parameters for merging grains")
            self.s = self.S("Parameters for adding pairs to grains based on statistics")
            self.x = self.X(
                "Parameters for excluding pairs from grains based on statistics"
            )

        class B(BaseParameters):
            def __init__(self, info=None):
                super().__init__()
                self.info = info
                self.beg = IndexStrategy_det(
                    "Tolerances in the first iteration loop for finding grains"
                )
                self.end = IndexStrategy_det(
                    "Tolerances in the last iteration loop for finding grains"
                )

        class M(BaseParameters):
            def __init__(self, info=None):
                super().__init__()
                self.info = info
                self.beg = IndexStrategy_det(
                    "Tolerances in the first iteration loop for grains to be merged"
                )
                self.end = IndexStrategy_det(
                    "Tolerances in the last iteration loop for grains to be merged"
                )

        class S(BaseParameters):
            stdf = InformationField(
                "Max. deviation from average grain properties for a new reflection to be included in grain (in std)",
                "double",
                None,
                {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
            )

            def __init__(self, info=None):
                super().__init__()
                self.info = info

        class X(BaseParameters):
            stdf = InformationField(
                "Max. deviation from average grain properties for a reflection to be kept in grain (in std)",
                "double",
                None,
                {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
            )

            def __init__(self, info=None):
                super().__init__()
                self.info = info


class Fsim(BaseParameters):
    check_spot = InformationField(
        "Check if there is not-segmented intensity in full images",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    omegarange = InformationField(
        "Check for spots and intensity in +/- omega_range (deg)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    MaxOmegaOffset = InformationField(
        "Maximum omega offset (deg)",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    bb_size = InformationField(
        "Dimensions of search bb - if left empty the projection size will be used",
        float,
        None,
    )
    assemble_figure = InformationField(
        "Assemble the results of forward simulation into a full image saved in the grain_04%d.mat file",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    display_figure = InformationField(
        "Display the assembled full image (function gtShowFsim)",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    clims = InformationField(
        "Colorlimits for display of results",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 2)},
    )
    Rdist_factor = InformationField(
        "Allow for Rdist_factor times dangstd in calulcation of angular deviation",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    bbsize_factor = InformationField(
        "Allow for bbsize_factor times bbx(y)sstd variation of BoundingBox size",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    oversize = InformationField(
        "Projections are zeropadded to this size before reconstruction",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    use_th = InformationField(
        "Use theoretically predicted diffraction angles for new detected spots",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    verbose = InformationField(
        "Display the search criteria for each of the spots",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    save_grain = InformationField(
        "Flag to save grain_####.mat files",
        "logical",
        None,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )
    oversizeVol = InformationField(
        "Grain reconstruction volumes are zeropadded to this size",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    sel_lh_stdev = InformationField(
        "Selects spots for reconsruction that are in the top 4.5 sigma of the likelihood rankings",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    sel_int_stdev = InformationField(
        "Selects spots for reconsruction that are in the top 4 sigma of the intensity rankings",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    sel_avint_stdev = InformationField(
        "Selects spots for reconsruction that are in the top 3.5 sigma of the average intensity per pixel rankings",
        "double",
        None,
        {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
    )
    mode = InformationField(
        "Mode of operation {''indexter''}/''farfield''/''global_fit''",
        "char",
        None,
        {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 8)},
    )
    Fsim = InformationField("", str, None)
    thr_check = InformationField(
        "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
    )

    def __init__(self):
        super().__init__()
        self.info = "forward simulation of diffraction spots"


class Rec(BaseParameters):
    def __init__(self):
        super().__init__()
        self.info = "Reconstruction"
        self.absorption = self.Absorption(
            "Absorption volume reconstruction information"
        )
        self.grains = self.Grains("Grains volume reconstruction information")
        self.thresholding = self.Thresholding("Grains volume segmentation information")

    class Absorption(BaseParameters):
        algorithm = InformationField(
            "Algorithm for the absorption reconstruction {''SIRT''}/''2DFBP''/''3DTV''",
            "char",
            "SIRT",
            {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 4)},
        )
        num_iter = InformationField(
            "Number of iterations used in SIRT reconstruction of absorption volume",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )
        interval = InformationField(
            "Interval between radiographs used for reconstruction of absorption scan",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )
        padding = InformationField(
            "Pixels padding around the projection data and volume",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )
        psf = InformationField()

        def __init__(self, info=None):
            super().__init__()
            self.info = info
            self.options = self.Option()

        class Option(BaseParameters):
            verbose = InformationField("", bool, None)
            detector_norm = InformationField("", str, None)
            lambda_ = InformationField("", float, None)
            epsilon = InformationField("", float, None)

            def __init__(self, info=None):
                super().__init__()
                self.info = info

    class Grains(BaseParameters):
        algorithm = InformationField(
            "Algorithm for the absorption reconstruction {''SIRT''}/''3DTV''/''6DL1''/''6DTV''/''6DTVL1''",
            "char",
            None,
            {"MATLAB_Class": "char", "MATLAB_Dimensions": (1, 4)},
        )
        num_iter = InformationField(
            "Number of iterations used in the reconstruction of each grain volume",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )
        list = InformationField("list of grain IDs to be reconstructed", float, None)

        def __init__(self, info=None):
            super().__init__()
            self.info = info
            self.slurm = self.Slurm()
            self.options = self.Option()

        class Slurm(BaseParameters):
            mem = InformationField("Memory", float, None)
            tasks_per_node = InformationField("Number of tasks", float, None)
            gpu = InformationField("Number of gpu", float, None)
            nodes = InformationField("Number of tasks", float, None)

            def __init__(self):
                super().__init__()

        class Option(BaseParameters):
            option = InformationField("", float, None)
            ospace_resolution = InformationField("", float, None)
            ospace_lims = InformationField("", float, None)
            max_grid_edge_points = InformationField("", float, None)
            num_interp = InformationField("", float, None)
            lambda_l1 = InformationField("", float, None)
            lambda_tv = InformationField("", float, None)
            volume_downscaling = InformationField("", float, None)
            ospace_super_sampling = InformationField("", float, None)
            rspace_super_sampling = InformationField("", float, None)
            ospace_oversize = InformationField("", float, None)
            rspace_oversize = InformationField("", float, None)
            shape_functions_type = InformationField("", float, None)
            detector_norm = InformationField("", str, None)
            tv_norm = InformationField("", str, None)
            tv_strategy = InformationField("", str, None)
            use_predicted_scatter_ints = InformationField("", bool, None)
            use_matrix_row_rescaling = InformationField("", bool, None)
            verbose = InformationField("", bool, None)
            epsilon = InformationField("", float, None)

            def __init__(self, info=None):
                super().__init__()
                self.info = info
                self.detector_l2_norm_weight = self.DetectorL2NormWeight()

            class DetectorL2NormWeight(BaseParameters):
                type = InformationField("", str, None)
                coefficient = InformationField("", float, None)
                images_used_for_direct_beam_scattering = InformationField("", str, None)
                use_dark_image_variance = InformationField("", float, None)
                add_weights_in_6D_algo = InformationField("", float, None)

                def __init__(self, info=None):
                    super().__init__()
                    self.info = info

    class Thresholding(BaseParameters):
        percentile = InformationField(
            "Threshold: percentile/100 * std",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )
        percent_of_peak = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        do_morph_recon = InformationField(
            "Perform morphological reconstruction during segmentation",
            "logical",
            None,
            {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
        )
        do_region_prop = InformationField(
            "",
            "logical",
            None,
            {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
        )
        num_iter = InformationField(
            "Number of iterations used in thresholding grains' volume",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )
        iter_factor = InformationField(
            "Weight factor for the iterative segmentation",
            "double",
            None,
            {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)},
        )
        mask_border_voxels = InformationField(
            "", "double", None, {"MATLAB_Class": "double", "MATLAB_Dimensions": (1, 1)}
        )
        use_levelsets = InformationField(
            "",
            "logical",
            None,
            {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
        )

        def __init__(self, info=None):
            super().__init__()
            self.info = info


class Fed(BaseParameters):
    dir = InformationField("Data analysis directory", Path, None)
    dct_vol = InformationField("Dct reconstructed volume filename (.edf)", str, None)
    dct_offset = InformationField(
        "Offset to be applied to the volume [x y z]", float, None
    )
    renumber_list = InformationField("Renumbering list for grainID", float, None)

    def __init__(self):
        super().__init__()
        self.info = "fed"


class IndexSpots(BaseParameters):
    difspot_source = InformationField("", str, None)
    include_conflict_spots = InformationField("", float, None)
    hkl_max_mult = InformationField("", float, None)
    deactivate_grain = InformationField("", float, None)
    lim_equi_grain = InformationField("", float, None)
    lim_std = InformationField("", float, None)
    lim_pix_u = InformationField("", float, None)
    lim_pix_v = InformationField("", float, None)
    lim_im_w = InformationField("", float, None)

    def __init__(self, info=None):
        super().__init__()
        self.info = info


class GlobalFit(BaseParameters):
    phaseID = InformationField("", float, None)
    detectorindex = InformationField("", float, None)
    fit_global_detposX = InformationField("", float, None)
    fit_global_detposY = InformationField("", float, None)
    fit_global_detposZ = InformationField("", float, None)
    fit_global_detroll = InformationField("", float, None)
    fit_global_detangUV = InformationField("", float, None)
    fit_global_dettiltU = InformationField("", float, None)
    fit_global_dettiltV = InformationField("", float, None)
    fit_global_pixmean = InformationField("", float, None)
    fit_global_pixratio = InformationField("", float, None)
    fit_global_energy = InformationField("", float, None)
    fit_global_rotwedge = InformationField("", float, None)
    fit_global_strain = InformationField("", float, None)
    fit_grain_position = InformationField("", float, None)
    fit_grain_orientation = InformationField("", float, None)
    fit_grain_strain = InformationField("", float, None)
    fit_drift_posX = InformationField("", float, None)
    fit_drift_posY = InformationField("", float, None)
    fit_drift_posZ = InformationField("", float, None)
    fit_drift_rotX = InformationField("", float, None)
    fit_drift_rotY = InformationField("", float, None)
    fit_drift_rotZ = InformationField("", float, None)
    fit_drift_energy = InformationField("", float, None)
    fit_grain_energy = InformationField("", float, None)
    algorithm = InformationField("", str, None)
    tolfun = InformationField("", float, None)
    tolvar = InformationField("", float, None)
    maxiter = InformationField("", float, None)
    maxfunevals = InformationField("", float, None)
    plotfun = InformationField("", str, None)
    finitediff = InformationField("", float, None)
    drift_omega = InformationField("", float, None)
    drift_method = InformationField("", str, None)
    niter_drift = InformationField("", float, None)
    use_readout_corr = InformationField("", float, None)
    use_motor_pos = InformationField("", float, None)
    warning_lim_u = InformationField("", float, None)
    warning_lim_v = InformationField("", float, None)
    warning_lim_w = InformationField("", float, None)
    usebest = InformationField("", float, None)
    deactivate_grain = InformationField("", float, None)
    weight_uvw = InformationField("", float, None)
    plot_error_bin_width = InformationField("", float, None)
    plot_error_bin_lim = InformationField("", float, None)
    plot_strain_bin_width = InformationField("", float, None)
    plot_strain_bin_lim = InformationField("", float, None)

    def __init__(self, info=None):
        super().__init__()
        self.info = info


class FRecon(BaseParameters):
    Binning = InformationField("", float, None)
    OutputFolder = InformationField("", str, None)
    S = InformationField("", float, None)
    TrustComp = InformationField("", float, None)
    drop_off = InformationField("", float, None)
    fitted_geo_already = InformationField("", float, None)
    minComp = InformationField("", float, None)
    minEucDis = InformationField("", float, None)
    maxD = InformationField("", float, None)
    maxDmedian = InformationField("", float, None)
    hklnumber = InformationField("", float, None)
    BeamStopY = InformationField("", float, None)
    BeamStopX = InformationField("", float, None)
    LoG_para = InformationField("", float, None)

    def __init__(self, info=None):
        super().__init__()
        self.info = info


class IndexStrategy_det(BaseParameters):
    ang = InformationField(
        "Max. angular deviation between two reflections in a grain (in degrees)",
        float,
        None,
    )
    angf = InformationField("", float, None)
    angmin = InformationField("", float, None)
    angmax = InformationField("", float, None)
    int = InformationField(
        "Max. relative intensity ratio of two reflections in a grain", float, None
    )
    bbxs = InformationField(
        "Max. relative bounding box X (U) size ratio in a grain", float, None
    )
    bbys = InformationField(
        "Max. relative bounding box Y (V) size ratio in a grain", float, None
    )
    distf = InformationField(
        "Max. distance between two diffraction paths (dmax = distf*grain_size)",
        float,
        None,
    )
    distmin = InformationField(
        "Min. absolut distance between two diffraction paths (in lab unit)",
        float,
        None,
    )
    distmax = InformationField(
        "Max. absolut distance between two diffraction paths (in lab unit)",
        float,
        None,
    )
    ming = InformationField("Min. no. of Friedel pairs in a grain", float, None)

    def __init__(self, info=None):
        super().__init__()
        self.info = info


class Information:
    """
    A class to store information about a specific parameter.

    Attributes
    ----------
    info : str
        A description of the parameter.
    type : type
        The Python data type of the parameter.
    matlab_type : Optional[str]
        The MATLAB class name associated with this parameter.
    value : any
        The value of the parameter.
    hdf5_attributes : dict
        Optional metadata such as MATLAB class/dimensions used when writing HDF5.
    """

    def __init__(
        self,
        info: str = "",
        type_: Any = bool,
        value: Any = None,
        hdf5_attributes: Optional[dict[str, Any]] = None,
        python_type: Optional[type] = None,
    ):
        self.info = info
        self.matlab_type = type_ if isinstance(type_, str) else None
        self.python_type = self._resolve_python_type(type_, python_type)
        self.type = self.python_type
        self._value = self._convert_value(value) if value is not None else value
        self.hdf5_attributes: dict[str, Any] = (
            dict(hdf5_attributes) if hdf5_attributes else {}
        )

    def _convert_value(self, value):
        if self.python_type == Path:
            if isinstance(value, bytes):
                path: Path = np.array(value).item().decode("utf-8")
            else:
                path = str(np.array(value).item())
            substrings_to_remove = ["/gpfs/", "/easy/", "/jazzy/", "/ga/", "/gb/"]
            path: str = Path(path).as_posix()
            for substring in substrings_to_remove:
                path = path.replace(substring, "/")
            return Path(path)
        # 1. Check if it's a single-column array and flatten it
        if isinstance(value, np.ndarray) and value.ndim == 2 and value.shape[1] == 1:
            value = value.flatten()
        # 2. Check if it's a byte string (dtype=object) and decode
        if isinstance(value, np.ndarray) and value.dtype == np.object_:
            # If it's a byte string, decode to a normal string
            if value.size == 1 and isinstance(value[0], bytes):
                value = value[0].decode("utf-8")
            else:
                # Decode each element if it's an array of byte strings
                value = np.array(
                    [d.decode("utf-8") if isinstance(d, bytes) else d for d in value]
                )
        value = np.array(value).squeeze()
        if value.size == 1:
            value = value.item()
        return value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = self._convert_value(new_value)

    def __call__(self):
        return self.value

    def set_hdf5_attributes(self, attributes: Optional[dict[str, Any]]) -> None:
        """Assign or update the metadata associated with this field."""
        if attributes is None:
            return
        if hasattr(attributes, "asdict"):
            attributes = attributes.asdict()
        normalized: dict[str, Any] = {}
        for key, value in attributes.items():
            if value is None:
                continue
            if key == "MATLAB_Dimensions":
                normalized[key] = tuple(value)
            else:
                normalized[key] = value
        self.hdf5_attributes.update(normalized)

    def _resolve_python_type(
        self, declared_type: Any, explicit_python_type: Optional[type]
    ) -> Any:
        if explicit_python_type is not None:
            return explicit_python_type
        if isinstance(declared_type, str):
            return self._map_matlab_to_python(declared_type)
        if declared_type is None:
            return type(None)
        return declared_type

    @staticmethod
    def _map_matlab_to_python(matlab_type: Optional[str]) -> type:
        lookup = {
            "double": float,
            "single": float,
            "char": str,
            "string": str,
            "logical": bool,
            "int8": int,
            "int16": int,
            "int32": int,
            "int64": int,
            "uint8": int,
            "uint16": int,
            "uint32": int,
            "uint64": int,
            "cell": list,
        }
        if matlab_type is None:
            return float
        return lookup.get(matlab_type.lower(), float)
