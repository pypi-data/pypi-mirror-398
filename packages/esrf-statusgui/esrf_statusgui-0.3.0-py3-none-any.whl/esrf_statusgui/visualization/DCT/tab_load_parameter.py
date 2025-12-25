import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import h5py
import ipywidgets as widgets
import numpy as np
from IPython.display import display
from tqdm import tqdm

import esrf_statusgui
from esrf_statusgui.data_managment.dct_parameter import dct_parameter
from esrf_statusgui.data_managment.loadFile import FilterH5Dataset, loadFile
from esrf_statusgui.file_utils.paths import get_visitor_root

PERIODIC_TABLE_ELEMENTS = {
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
}


def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string into a datetime object."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            return None


def date_to_iso(date: Union[datetime, str]) -> str:
    """Convert a datetime object or string to ISO format."""
    if isinstance(date, datetime):
        return date.isoformat()
    return str(date)


class SampleDB:
    """Class to represent a sample database entry."""

    def __init__(self, dbpath: Path):
        self.dbpath = Path(dbpath)
        self.beamline: Optional[str] = None
        self.experiment: Optional[str] = None
        self.sample: Optional[str] = None
        self.dataset: Optional[str] = None
        self._date: Optional[datetime] = None
        self.year: Optional[str] = None
        self.raw_data: Optional[Path] = None
        self.sensor_type: Optional[str] = None
        self._composition: Optional[Union[list[str], str]] = None
        self._composition_name: Optional[str] = None
        self._material: Optional[str] = None
        self.space_group: Optional[str] = None
        self.crystal_system: Optional[str] = None
        self.objective: Optional[str] = None
        self.energy: Optional[float] = None
        self.hermann_mauguin: Optional[str] = None
        self.lattice_par: Optional[list[float]] = None
        self.name: Optional[str] = None
        self.dist: Optional[float] = None
        self._elements: list[str] = []

    @property
    def composition(self) -> Optional[Union[list[str], str]]:
        return self._composition

    @composition.setter
    def composition(self, value: Optional[Union[list[str], str]]):
        self._composition = value
        self._check_elements()

    @property
    def composition_name(self) -> Optional[str]:
        return self._composition_name

    @composition_name.setter
    def composition_name(self, value: Optional[str]):
        self._composition_name = value
        self._check_elements()

    @property
    def material(self) -> Optional[str]:
        return self._material

    @material.setter
    def material(self, value: Optional[str]):
        self._material = value
        self._check_elements()

    @property
    def date(self) -> Optional[datetime]:
        return self._date

    @date.setter
    def date(self, value: Optional[datetime]):
        self._date = parse_datetime(value)
        if self._date is not None:
            self.year = str(self._date.year)

    def _check_elements(self):
        """Check if composition, composition_name, or material contains valid elements."""
        for value in [self._composition, self._composition_name, self._material]:
            if value is not None:
                if isinstance(value, (list, np.ndarray)):
                    self._elements.extend(
                        [
                            item
                            for item in value
                            if item in PERIODIC_TABLE_ELEMENTS
                            and item not in self._elements
                        ]
                    )
                    if not self._elements:
                        for val in value:
                            if isinstance(val, str):
                                self._elements.extend(
                                    [
                                        item
                                        for item in PERIODIC_TABLE_ELEMENTS
                                        if item in val and item not in self._elements
                                    ]
                                )
                elif isinstance(value, str):
                    self._elements.extend(
                        [
                            item
                            for item in value.split()
                            if item in PERIODIC_TABLE_ELEMENTS
                            and item not in self._elements
                        ]
                    )
                    if not self._elements:
                        self._elements.extend(
                            [
                                item
                                for item in PERIODIC_TABLE_ELEMENTS
                                if item in value and item not in self._elements
                            ]
                        )
                    if any(item in value.lower() for item in ("superalloy", "inconel")):
                        self._elements.extend(
                            [item for item in ["Ni"] if item not in self._elements]
                        )
        for elem in self._elements:
            if any(
                [elem in elements for elements in self._elements if elem != elements]
            ):
                self._elements.remove(elem)
        self.elements = " ".join(self._elements)

    def fill_par(self):
        """Fill parameters from the database file."""
        db = loadFile(self.dbpath)
        acq_sub = self._get_acq_sub(db)
        self._fill_beamline_and_date(db, acq_sub)
        self._fill_raw_data(db, acq_sub)
        self._fill_experiment_and_sample()
        self._fill_crystal_properties(db, acq_sub)

    def _get_acq_sub(self, db) -> str:
        """Get the acquisition subpath."""
        if "collection_dir_old" not in db.get_keys("acq") and "dir" not in db.get_keys(
            "acq"
        ):
            return "/" + db.get_keys("acq")[0]
        return ""

    def _fill_beamline_and_date(self, db, acq_sub: str):
        """Fill beamline and date properties."""
        if not self.beamline and "beamline" in db.get_keys(f"acq{acq_sub}"):
            self.beamline = db.get_value(f"acq{acq_sub}/beamline")
        if not self.date:
            self.date = db.get_value(f"acq{acq_sub}/date")

    def _fill_raw_data(self, db, acq_sub: str):
        """Fill raw data path."""
        if "collection_dir_old" in db.get_keys(f"acq{acq_sub}"):
            self.raw_data = Path(
                *[
                    i
                    for i in Path(
                        db.get_value(f"acq{acq_sub}/collection_dir_old")
                    ).parts
                    if i not in {"easy", "jazzy", "ga", "gb", "mnt", "multipath-shares"}
                ]
            )
        elif "dir" in db.get_keys(f"acq{acq_sub}"):
            self.raw_data = Path(
                *[
                    i
                    for i in Path(db.get_value(f"acq{acq_sub}/dir")).parts
                    if i
                    not in {
                        "easy",
                        "jazzy",
                        "ga",
                        "gb",
                        "mnt",
                        "multipath-shares",
                        "mntdirect",
                    }
                ]
            )

    def _fill_experiment_and_sample(self):
        """Fill experiment and sample properties."""
        if self.experiment is None and self.raw_data:
            if "3dxrd" in self.raw_data.parts:
                index = self.raw_data.parts.index("3dxrd")
                if any(
                    ext in self.raw_data.parts[index + 1] for ext in ["ma", "blc", "me"]
                ):
                    self.experiment = self.raw_data.parts[index + 1]
            elif "visitor" in self.raw_data.parts:
                index = self.raw_data.parts.index("visitor")
                self.experiment = self.raw_data.parts[index + 1]
                if self.beamline is None:
                    self.beamline = self.raw_data.parts[index + 2]
                if "PROCESSED_DATA" in self.raw_data.parts:
                    index = self.raw_data.parts.index("PROCESSED_DATA")
                    self.sample = self.raw_data.parts[index + 1]

    def _fill_crystal_properties(self, db, acq_sub: str):
        """Fill crystal-related properties."""
        self.sensor_type = db.get_value(f"acq{acq_sub}/sensortype")
        if self.sensor_type:
            self.sensor_type = self.sensor_type.replace("_", " ").lower()
        self.composition = db.get_value("cryst/composition")
        self.composition_name = db.get_value("cryst/name")
        self.material = db.get_value("cryst/material")
        self.space_group = db.get_value("cryst/spacegroup")
        if "objective" in db.get_keys(f"acq{acq_sub}"):
            self.objective = db.get_value(f"acq{acq_sub}/objective")
        self.energy = db.get_value(f"acq{acq_sub}/energy")
        self.hermann_mauguin = db.get_value("cryst/hermann_mauguin")
        self.crystal_system = db.get_value("cryst/crystal_system")
        self.lattice_par = db.get_value("cryst/latticepar")
        self.dataset = db.get_value(f"acq{acq_sub}/name")
        self.dist = db.get_value(f"acq{acq_sub}/dist")

    def to_dict(self) -> dict:
        """Convert the object to a dictionary."""
        return {
            "dbpath": str(self.dbpath),
            "beamline": self.beamline,
            "experiment": self.experiment,
            "sample": self.sample,
            "dataset": self.dataset,
            "date": date_to_iso(self.date),
            "raw_data": str(self.raw_data),
            "sensor_type": self.sensor_type,
            "composition": self.composition,
            "composition_name": self.composition_name,
            "material": self.material,
            "space_group": self.space_group,
            "objective": self.objective,
            "energy": self.energy,
            "hermann_mauguin": self.hermann_mauguin,
            "lattice_par": self.lattice_par,
            "dist": self.dist,
            "crystal_system": self.crystal_system,
        }

    @classmethod
    def from_h5(cls, h5: FilterH5Dataset) -> "SampleDB":
        """Load the object from an HDF5 group."""
        if isinstance(h5, FilterH5Dataset):
            instance = cls(Path(h5.get_value("dbpath")))
            for attr in [
                "beamline",
                "experiment",
                "sample",
                "dataset",
                "sensor_type",
                "composition",
                "composition_name",
                "material",
                "space_group",
                "objective",
                "energy",
                "hermann_mauguin",
                "lattice_par",
                "dist",
                "crystal_system",
            ]:
                setattr(instance, attr, h5.get_value(attr))
            instance.date = h5.get_value("date")
            instance.raw_data = Path(h5.get_value("raw_data", ""))
            return instance
        else:
            pass

    @classmethod
    def from_dict(cls, data: dict) -> "SampleDB":
        """Load the object from a dictionary."""
        instance = cls(Path(data["dbpath"]))
        for attr in [
            "beamline",
            "experiment",
            "sample",
            "dataset",
            "sensor_type",
            "composition",
            "composition_name",
            "material",
            "space_group",
            "objective",
            "energy",
            "hermann_mauguin",
            "lattice_par",
            "dist",
            "crystal_system",
        ]:
            setattr(instance, attr, data.get(attr))
        instance.date = data.get("date")
        instance.raw_data = Path(data.get("raw_data", ""))
        return instance

    def __str__(self) -> str:
        """Pretty print the object's content."""
        return (
            f"{self.dataset}:\n"
            f"  dbpath: {self.dbpath}\n"
            f"  experiment: {self.experiment}\n"
            f"  beamline: {self.beamline}\n"
            f"  date: {date_to_iso(self.date)}\n"
            f"  sample: {self.sample}\n"
            f"  dataset: {self.dataset}\n"
            f"  energy: {self.energy}\n"
            f"  sensor_type: {self.sensor_type}\n"
            f"  objective: {self.objective}\n"
            f"  dist: {self.dist}\n"
            f"  raw_data: {self.raw_data}\n"
            f"  elements: {self._elements}\n"
            f"  composition: {self.composition}\n"
            f"  composition_name: {self.composition_name}\n"
            f"  space_group: {self.space_group}\n"
            f"  hermann_mauguin: {self.hermann_mauguin}\n"
            f"  lattice_par: {self.lattice_par}\n"
            f"  crystal_system: {self.crystal_system}\n"
        )

    def __repr__(self):
        return (
            f"Exp: {self.attributes['experiment']}, Dset {self.attributes['dataset']}"
        )


class ParametersDB:
    """Class to manage a database of sample parameters."""

    def __init__(self, dbpath: Optional[Path] = None):
        self.sample: list[SampleDB] = []
        self.path_folder = Path("/data/id11/archive")
        self.path_db = dbpath or self._get_default_db_path()

    def _get_default_db_path(self) -> Path:
        """Get the default path for the database file."""
        module_path = Path(dct_parameter.__module__.replace(".", "/"))
        module_file_path = Path(esrf_statusgui.__file__).parent.parent / module_path
        return module_file_path.parent / "DCT_parametersDB.h5"

    def add_sample(self, sample_db: SampleDB):
        """Add a SampleDB instance to the list of samples."""
        self.sample.append(sample_db)

    def to_dict(self) -> dict:
        """Convert the object to a dictionary."""
        return {
            "dbpath": str(self.path_db),
            "sample": [sample.to_dict() for sample in self.sample],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ParametersDB":
        """Load the object from a dictionary."""
        instance = cls(Path(data["dbpath"]))
        for sample_data in data.get("sample", []):
            instance.add_sample(SampleDB.from_dict(sample_data))
        return instance

    def __str__(self) -> str:
        """Pretty print the object's content."""
        samples_str = "\n".join(str(sample) for sample in self.sample)
        return f"ParametersDB:\n  dbpath: {self.path_db}\n  samples:\n{samples_str}"

    def build_DB(self, save=True):
        """Build the database by scanning the folder for parameter files."""
        for spath in tqdm(self.path_folder.rglob("*parameters.h5")):
            sample = SampleDB(spath)
            sample.fill_par()
            self.add_sample(sample)
        if save:
            self.save_to_h5()

    def add_experiment_to_DB(self, experiment, save=True):
        for spath in tqdm((get_visitor_root() / experiment).rglob("*parameters.h5")):
            if not any(
                sample is not None and sample.dbpath == spath for sample in self.sample
            ):
                sample = SampleDB(spath)
                sample.fill_par()
                self.add_sample(sample)
        if save:
            self.save_to_h5()

    def save_to_h5(self):
        """Save the ParametersDB to an HDF5 file."""
        with h5py.File(self.path_db, "w") as h5file:
            h5file.attrs["dbpath"] = str(self.path_db)
            for i, sample in enumerate(self.sample):
                if sample is not None:
                    group = h5file.create_group(f"sample{i:04d}")
                    for key, value in sample.to_dict().items():
                        if value is not None:
                            group.attrs[key] = value

    def load_from_h5(self, filepath: Optional[Path] = None):
        """Load the ParametersDB from an HDF5 file."""
        filepath = filepath or self.path_db
        self.sample = []
        h5file = loadFile(filepath)
        for sample_key in h5file.get_keys():
            self.add_sample(SampleDB.from_h5(h5file.get_value(sample_key)))

    def filter_samples(self, filter_func) -> list[SampleDB]:
        """Filter samples based on a function."""
        return [
            sample
            for sample in self.sample
            if sample is not None and filter_func(sample)
        ]


class ParametersSelector(widgets.VBox):
    def __init__(self, experiment=None, exp_list=None):
        self.db = ParametersDB()
        if self.db.path_db.exists():
            self.db.load_from_h5()
        else:
            self.db.build_DB()
        if experiment is not None:
            self.db.add_experiment_to_DB(experiment)
        self.filters = {}
        self.filter_attributes = [
            "year",
            "experiment",
            "elements",
            "crystal_system",
            "space_group",
        ]
        self.output = widgets.Output()

        # Initialize filters
        self.filter_widgets = self.create_filter_widgets()
        if exp_list is None:
            self.visitor_path = get_visitor_root()
            self.exp_dirs = [
                self.visitor_path / item
                for item in os.listdir(self.visitor_path)
                if (self.visitor_path / item).is_dir()
                and any(
                    sitem in os.listdir(self.visitor_path / item)
                    for sitem in ["id11", "id3"]
                )
            ]
            self.exp_list = sorted([item.stem for item in self.exp_dirs])
        else:
            self.exp_list = exp_list
        self.add_experiment_widget = widgets.Combobox(
            description="Enter the experiment name you wish to add to the DB",
            options=self.exp_list,
            ensure_option=False,
            layout=widgets.Layout(width="auto"),
        )
        self.add_experiment_button = widgets.Button(description="Add to DB")
        self.add_experiment = widgets.HBox(
            [self.add_experiment_widget, self.add_experiment_button]
        )
        self.path_selector = widgets.Dropdown(description="Select Path:", options=[])
        self.path_selector.options = [
            sample.dbpath for sample in self.db.sample if sample is not None
        ]
        self.load_button = widgets.Button(description="Display")

        self.add_experiment_button.on_click(self.add_experiment_click)
        self.load_button.on_click(self.load_and_display)
        self.setup_observers()

        # Layout
        filter_boxes = [
            widgets.VBox(
                [
                    widgets.Label(
                        value=f"Select {label}:", layout=widgets.Layout(width="auto")
                    ),
                    widget,
                ]
            )
            for label, widget in self.filter_widgets.items()
        ]

        self.filter_box = widgets.HBox(
            filter_boxes, layout=widgets.Layout(justify_content="space-between")
        )
        self.selection_box = widgets.HBox([self.path_selector, self.load_button])

        if experiment is not None:
            if experiment in self.filter_widgets["experiment"].options:
                self.filter_widgets["experiment"].value = (experiment,)

        super().__init__(
            [self.add_experiment, self.filter_box, self.selection_box, self.output]
        )

    def create_filter_widgets(self):
        """Create filter selection widgets."""
        return {
            attr: widgets.SelectMultiple(
                options=[""] + self.get_unique_values(attr),
                layout=widgets.Layout(width="auto"),
            )
            for attr in self.filter_attributes
        }

    def setup_observers(self):
        """Set up observers for filter widgets."""
        for widget in self.filter_widgets.values():
            widget.observe(self.update_filters, names="value")

    def update_filters(self, change=None):
        """Update filter options and path selector based on current selections."""
        self.remove_observers()

        self.filters = {
            attr: tuple(filter(None, widget.value))
            for attr, widget in self.filter_widgets.items()
        }

        filtered_samples = self.db.filter_samples(
            lambda sample: self.sample_matches_filters(sample)
        )

        for attr, widget in self.filter_widgets.items():
            widget.options = [""] + self.get_unique_values(attr, filtered_samples)
            if self.filters[attr]:
                widget.value = self.filters[attr]

        self.path_selector.options = [sample.dbpath for sample in filtered_samples]

        self.setup_observers()

    def sample_matches_filters(self, sample):
        """Check if a sample matches the current filters."""
        return all(
            not self.filters[attr] or getattr(sample, attr, None) in self.filters[attr]
            for attr in self.filter_attributes
        )

    def remove_observers(self):
        """Remove observers temporarily to avoid redundant calls."""
        for widget in self.filter_widgets.values():
            widget.unobserve(self.update_filters, names="value")

    def load_and_display(self, button):
        """Display the selected sample."""
        selected_path = self.path_selector.value
        if selected_path:
            selected_sample = next(
                (sample for sample in self.db.sample if sample.dbpath == selected_path),
                None,
            )
            if selected_sample:
                with self.output:
                    self.output.clear_output()
                    print(selected_sample)

    def add_experiment_click(self, button):
        if self.add_experiment_widget.value:
            self.db.add_experiment_to_DB(self.add_experiment_widget.value)
            if (
                self.add_experiment_widget.value
                in self.filter_widgets["experiment"].options
            ):
                self.filter_widgets["experiment"].value = (
                    self.add_experiment_widget.value,
                )
            self.add_experiment_widget.value = ""

    def get_unique_values(self, attribute, sample_filtered=None):
        """Get unique values for a given attribute from the database."""
        unique_values = set()
        year_map = {}
        for sample in self.db.sample if sample_filtered is None else sample_filtered:
            value = getattr(sample, attribute, None)
            if isinstance(value, datetime):
                value = str(value.year)
            if value is not None:
                to_add = (
                    " ".join(value) if isinstance(value, (list, np.ndarray)) else value
                )
                if to_add != "":
                    unique_values.add(to_add)
                    year_map[to_add] = max(
                        year_map.get(to_add, 0),
                        int(sample.year) if sample.year is not None else 2000,
                    )

        if attribute in ["experiment"]:
            return sorted(unique_values, key=lambda x: (-year_map.get(x, 0), x))

        return sorted(unique_values, reverse=(attribute == "year"))

    def display(self):
        display(self)


if __name__ == "__main__":
    selector = ParametersSelector()
    selector.display()
