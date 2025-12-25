import logging
from datetime import datetime
from typing import Any, Optional

import h5py
import numpy as np

try:
    from esrf_pathlib import ESRFPath as Path
except ImportError:
    from pathlib import Path
try:
    from esrf_loadFile import loadFile
except ImportError:
    from esrf_statusgui.data_managment.loadFile import loadFile
try:
    from esrf_statusgui.data_managment import dct_parameter_schema as schema
    from esrf_statusgui.data_managment.dct_parameter_config import (
        apply_default_values,
    )
    from esrf_statusgui.data_managment.dct_parameter_template import (
        get_dataset_attributes,
    )
except ImportError:
    import dct_parameter_schema as schema
    from dct_parameter_config import apply_default_values
    from dct_parameter_template import get_dataset_attributes

logger = logging.getLogger(__name__)
InformationField = schema.InformationField
Information = schema.Information
BaseParameters = schema.BaseParameters


class dct_parameter(BaseParameters):
    """
    This class is used to store all the parameters of a DCT dataset.

    Args:
        path (str): Path to the parameter file. If provided, the parameters will be
            loaded from the file. Otherwise, they will be initialized to default values.

    Attributes:
        self.acq (Acq): self.acquisition parameters.
        cryst (Cryst): Crystallography parameters.
        detgeo (DetGeo): Detector geometry parameters.
        diffractometer (Diffractometer): Diffractometer parameters.
        fed (Fed): FED parameters.
        fsim (Fsim): FSIM parameters.
        index (Index): Index parameters.
        labgeo (LabGeo): Laboratory geometry parameters.
        match (Match): Match parameters.
        prep (Prep): Preparation parameters.
        rec (Rec): Reconstruction parameters.
        recgeo (RecGeo): Reconstruction geometry parameters.
        samgeo (SamGeo): Sample geometry parameters.
        seg (Seg): Segmentation parameters.
        version (Version): Version number of the parameters file.
        xop (Xop): XOP parameters.

    """

    Version = schema.Version
    Diffractometer = schema.Diffractometer
    Acq = schema.Acq
    Xop = schema.Xop
    Cryst = schema.Cryst
    LabGeo = schema.LabGeo
    DetGeo = schema.DetGeo
    SamGeo = schema.SamGeo
    RecGeo = schema.RecGeo
    Prep = schema.Prep
    Seg = schema.Seg
    Match = schema.Match
    Index = schema.Index
    Fsim = schema.Fsim
    Rec = schema.Rec
    Fed = schema.Fed
    IndexSpots = schema.IndexSpots
    GlobalFit = schema.GlobalFit
    FRecon = schema.FRecon

    expert_mode = InformationField(
        "Expert mode to prevent from displaying unnecessary comments, widgets and interractions",
        "logical",
        False,
        {"MATLAB_Class": "logical", "MATLAB_Dimensions": (1, 1)},
    )

    def __init__(self, path=None):
        super().__init__()
        self.acq = self.Acq()
        self.cryst = self.Cryst()
        self.detgeo = self.DetGeo()
        self.diffractometer = self.Diffractometer()
        self.fed = self.Fed()
        self.fsim = self.Fsim()
        self.index = self.Index()
        self.labgeo = self.LabGeo()
        self.match = self.Match()
        self.prep = self.Prep()
        self.rec = self.Rec()
        self.recgeo = self.RecGeo()
        self.samgeo = self.SamGeo()
        self.seg = self.Seg()
        self.version = self.Version()
        self.xop = self.Xop()
        self.index_spots = self.IndexSpots()
        self.globalfit = self.GlobalFit()
        self.frecon = self.FRecon()
        self._apply_template_metadata()
        if path:
            self.path = Path(path)
            if self.path.exists():
                self.load_parameter(self.path)

    def _set_default(self):
        apply_default_values(self)

    def _apply_template_metadata(self) -> None:
        """Attach MATLAB metadata from the template file to every Information node."""
        try:
            self._assign_metadata_recursive(self, "")
        except Exception as error:
            logger.debug("Failed to apply template metadata: %s", error)

    def _assign_metadata_recursive(self, node: Any, current_path: str) -> None:
        """Recursively assign metadata by aligning attribute paths with the template."""
        if isinstance(node, BaseParameters):
            for field_name in node._iter_information_field_names():
                attr_path = self._join_h5_path(current_path, field_name)
                information = getattr(node, field_name)
                metadata = get_dataset_attributes(attr_path)
                if metadata:
                    information.set_hdf5_attributes(metadata.asdict())

        for attr, value in vars(node).items():
            if attr in {"internal"} or attr.startswith("_") or attr.startswith("__"):
                continue
            attr_path = self._join_h5_path(current_path, attr)
            if isinstance(value, list):
                for index, item in enumerate(value):
                    if hasattr(item, "__dict__"):
                        self._assign_metadata_recursive(
                            item, self._join_h5_path(attr_path, f"{index:02d}")
                        )
            elif hasattr(value, "__dict__"):
                self._assign_metadata_recursive(value, attr_path)

    def _init_detgeo(self):
        self.detgeo.pixelsizeu.value = self.acq.pixelsize()
        self.detgeo.pixelsizev.value = self.acq.pixelsize()
        self.detgeo.detsizeu.value = self.acq.xdet()
        self.detgeo.detsizev.value = self.acq.ydet()

        if self.detgeo.detsizeu():
            self.detgeo.detrefu.value = (self.detgeo.detsizeu() / 2) + 0.5
        if self.detgeo.detsizev():
            self.detgeo.detrefv.value = (self.detgeo.detsizev() / 2) + 0.5

        # Detector angular coverage limits (in degrees)
        self.detgeo.detanglemin.value = 0
        self.detgeo.detanglemax.value = 45

        if self.acq.no_direct_beam() and self.acq.detector_definition() == "vertical":
            # Vertical setup, detector above sample
            logging.warning(
                "No direct beam case with a vertical detector. Check if any flip was applied."
            )
            self.detgeo.detrefpos.value = [0, self.acq.dist(), 0]
            self.detgeo.detdiru.value = [0, 0, -1]
            self.detgeo.detdirv.value = [1, 0, 0]

            if self.acq.rotation_direction() == "counterclockwise":
                self.detgeo.detrefpos.value = [-x for x in self.detgeo.detrefpos()]
                self.detgeo.detdiru.value = [-x for x in self.detgeo.detdiru()]

        elif not self.acq.no_direct_beam():
            # Inline detector setup (direct beam HR scan)
            logging.info("High resolution direct beam scan...")
            self.detgeo.detrefpos.value = [self.acq.dist(), 0, 0]
            self.detgeo.detdiru.value = [0, 1, 0]
            self.detgeo.detdirv.value = [0, 0, -1]

            if self.acq.rotation_direction() == "counterclockwise":
                self.detgeo.detdiru.value = [-x for x in self.detgeo.detdiru()]
                self.detgeo.detdirv.value = [-x for x in self.detgeo.detdirv()]

            # Handle sample bounding box if available
            if self.acq.bb():
                self.detgeo.detrefpos.value[1:3] = self.sf_detrefpos(
                    self.acq.bb(), self.detgeo
                )

        elif self.acq.no_direct_beam() and self.acq.detector_definition() == "inline":
            logging.info("Taper scan detected...")
            self.detgeo.detrefpos.value = [self.acq.dist(), 0, 0]
            self.detgeo.detdiru.value = [0, 1, 0]
            self.detgeo.detdirv.value = [0, 0, -1]

            if self.acq.bb() is None:
                self.acq.bb.value = [
                    self.acq.xdet() / 2 - 50,
                    self.acq.ydet() / 2 - 50,
                    100,
                    100,
                ]
            self.detgeo.detrefpos.value[1:3] = self.sf_detrefpos(
                self.acq.bb(), self.detgeo
            )

        # Apply readout delay for Marana detectors
        if self.acq.sensortype()[:6].lower() == "marana":
            self.detgeo.readout_delay_sec.value = 0.042
            self.detgeo.readout_direction.value = "-v"
        else:
            self.detgeo.readout_delay_sec.value = 0
            self.detgeo.readout_direction.value = "-v"

        self.detgeo.detorig = (
            self.detgeo.detrefpos()
            - self.detgeo.detdiru() * self.detgeo.detrefu() * self.detgeo.pixelsizeu()
            - self.detgeo.detdirv() * self.detgeo.detrefv() * self.detgeo.pixelsizev()
        )

    def _init_labgeo(self):
        if self.acq.rotation_name():
            if self.acq.rotation_name() in ["pmo", "srot", "unknown", "omega"]:
                self.labgeo.rotdir.value = [0, 0, -1]
            if self.acq.rotation_name() in ["diffrz"]:
                self.labgeo.rotdir.value = [0, 0, 1]
        if (
            self.acq.rotation_axis() == "horizontal"
            and self.acq.rotation_direction() == "clockwise"
        ):
            self.labgeo.rotdir.value = -self.labgeo.rotdir()
        if self.acq.no_direct_beam() and self.acq.detector_definition() == "vertical":
            logging.warning(
                "No direct beam case with a vetical detector.\nAny flip was applied during the scan... Please check if it is true"
            )
            self.labgeo.samenvtop.value = []
            self.labgeo.samenvbot.value = []
            self.labgeo.samenvrad.value = []
        elif not self.acq.no_direct_beam():
            logging.info("High resolution direct beam scan...")
            if self.acq.bb():
                self.gtGeoSamEnvFromAcq()
            else:
                self.labgeo.samenvtop.value = []
                self.labgeo.samenvbot.value = []
                self.labgeo.samenvrad.value = []

        elif self.acq.no_direct_beam() and self.acq.detector_definition() == "inline":
            logging.warning("This looks like a taper scan...")
            if not self.acq.bb():
                self.acq.bb.value = [
                    self.acq.xdet() / 2 - 50,
                    self.acq.ydet() / 2 - 50,
                    100,
                    100,
                ]

            self.gtGeoSamEnvFromAcq()
            logging.info(
                "Choose a squared sample bounding box in the center of the image..."
            )

    def _init_recgeo(self):
        # If samgeo exists, set origin and axis directions from samgeo
        if self.samgeo.orig() is not None:
            self.recgeo.orig.value = self.samgeo.orig()
            self.recgeo.dirx.value = self.samgeo.dirx()
            self.recgeo.diry.value = self.samgeo.diry()
            self.recgeo.dirz.value = self.samgeo.dirz()
        else:
            # Default axis-aligned directions if no samgeo provided
            self.recgeo.orig.value = [0, 0, 0]
            self.recgeo.dirx.value = [1, 0, 0]
            self.recgeo.diry.value = [0, 1, 0]
            self.recgeo.dirz.value = [0, 0, 1]

        # Calculate pixel size using detgeo or acq
        if (
            self.detgeo.pixelsizeu() is not None
            and self.detgeo.pixelsizev() is not None
        ):
            det_pixel_size = np.mean(
                [self.detgeo.pixelsizeu(), self.detgeo.pixelsizev()]
            )
        else:
            det_pixel_size = self.acq.pixelsize()

        # Set the vertical position (z) of the origin based on acq and self.detgeo
        if self.acq.bb() is not None:
            self.recgeo.orig.value[2] = (
                np.sign(self.detgeo.detdirv()[2])
                * (
                    self.acq.bb()[1]
                    + self.acq.bb()[3] / 2
                    - self.detgeo.detrefv()
                    - 0.5
                )
                * self.detgeo.pixelsizev()
            )

        # Set voxel size, assuming isotropic voxels based on detector pixel size
        self.recgeo.voxsize.value = [det_pixel_size, det_pixel_size, det_pixel_size]

    def _init_recAbsorption(self):
        if self.rec.absorption.algorithm().upper() in ["SIRT", "2DFBP"]:
            self.rec.absorption.num_iter.value = 100
            self.rec.absorption.interval.value = 10
            self.rec.absorption.padding.value = 5
            self.rec.absorption.psf.value = []
        elif self.rec.absorption.algorithm().upper() in ["3DTV"]:
            self.rec.absorption.num_iter.value = 100
            self.rec.absorption.interval.value = 10
            self.rec.absorption.padding.value = 5
            self.rec.absorption.psf.value = []
            self.rec.absorption.options.verbose.value = False
            self.rec.absorption.options.detector_norm.value = "l2"
            self.rec.absorption.options.lambda_.value = 1e-2
            self.rec.absorption.options.epsilon.value = 1e-4

    def _init_recGrains(self):
        if self.rec.absorption.algorithm().upper() in ["3DTV"]:
            self.rec.grains.options.lambda_l1.value = 1e-2
            self.rec.grains.options.epsilon.value = 0
            self.rec.grains.options.rspace_oversize.value = 1
            self.rec.grains.options.rspace_super_sampling.value = 1
            self.rec.grains.options.detector_norm.value = "l2"
            self.rec.grains.options.verbose.value = False
        elif self.rec.absorption.algorithm().upper() in [
            "6DLS",
            "6DL1",
            "6DTV",
            "6DTVL1",
        ]:
            self.rec.grains.options.ospace_resolution.value = 0.25
            self.rec.grains.options.max_grid_edge_points.value = 15
            self.rec.grains.options.num_interp.value = 0
            self.rec.grains.options.lambda_l1.value = 1e-2
            self.rec.grains.options.lambda_tv.value = 1
            self.rec.grains.options.volume_downscaling.value = 1
            self.rec.grains.options.ospace_super_sampling.value = 1
            self.rec.grains.options.rspace_super_sampling.value = 1
            self.rec.grains.options.ospace_oversize.value = 1.1
            self.rec.grains.options.rspace_oversize.value = 1.1
            self.rec.grains.options.shape_functions_type.value = None
            self.rec.grains.options.detector_norm.value = "l2"
            self.rec.grains.options.tv_norm.value = "l12"
            self.rec.grains.options.tv_strategy.value = "groups"
            self.rec.grains.options.use_predicted_scatter_ints.value = False
            self.rec.grains.options.use_matrix_row_rescaling.value = False
        self.rec.grains.algorithm.value = self.rec.absorption.algorithm()
        self.rec.grains.num_iter.value = 100

    def _init_prep(self):
        self.prep.bbox.value = self.acq.bb()
        if self.acq.type() == "360degree":
            self.prep.totproj.value = 2 * self.acq.nproj()
        elif self.acq.type == "180degree":
            self.prep.totproj.value = self.acq.nproj()
        else:
            logging.warning(
                f'Unknown type of scan: "{self.acq.type()}". Check parameters.acq.type!'
            )
        self.prep.udrift.value = [0] * self.prep.totproj()
        self.prep.vdrift.value = [0] * self.prep.totproj()
        self.prep.udriftabs.value = [0] * self.prep.totproj()
        tproj = float(self.prep.totproj() / (self.acq.interlaced_turns() + 1))
        test = [i for i in range(1, 101) if tproj % i == 0]
        test10 = [abs(x - 10) for x in test]
        ind10 = test10.index(min(test10))
        test50 = [abs(x - 50) for x in test]
        ind50 = test50.index(min(test50))
        self.prep.absint.value = test[ind10]
        self.prep.absrange.value = 10 * self.prep.absint()
        self.prep.fullint.value = test[ind50]
        self.prep.fullrange.value = 10 * self.prep.fullint()
        if self.acq.no_direct_beam() is not None and self.acq.no_direct_beam() is False:
            self.prep.correct_drift.value = "not_required"

    def _init_diffractometer(self):
        if self.acq.beamline():
            if "id11" in self.acq.beamline().lower():
                self.diffractometer.motor_rotation.value = "diffrz"
                self.diffractometer.motor_samtilt_bot.value = "samry"
                self.diffractometer.motor_basetilt.value = "diffry"
                self.diffractometer.motor_samtilt_top.value = "samrx"
            elif "id03" in self.acq.beamline().lower():
                self.diffractometer.motor_rotation.value = "omega"
                self.diffractometer.motor_samtilt_bot.value = "chi"
                self.diffractometer.motor_basetilt.value = "mu"
                self.diffractometer.motor_samtilt_top.value = "phi"
                self.diffractometer.axes_basetilt.value = [0, -1, 0]
                self.diffractometer.axes_samtilt_bot.value = [1, 0, 0]
                self.diffractometer.axes_samtilt_top.value = [0, 1, 0]
                self.diffractometer.motor_samtx.value = "samx"
                self.diffractometer.motor_samty.value = "samy"
                self.diffractometer.motor_samtz.value = "samz"
                self.diffractometer.limits_samtilt_bot = [-8, 8]
                self.diffractometer.limits_samtilt_top = [-10, 10]
        self.diffractometer.origin_basetilt.value = [0, 0, self.acq.motors.difftz()]
        self.diffractometer.angles_rotation.value = self.acq.motors.diffrz()[0]
        self.diffractometer.angles_samtilt_bot.value = getattr(
            self.acq.motors, self.diffractometer.motor_samtilt_bot()
        )()
        self.diffractometer.angles_samtilt_top.value = getattr(
            self.acq.motors, self.diffractometer.motor_samtilt_top()
        )()
        self.diffractometer.shifts_sam_stage.value = self.acq.sample_shifts()

    def _init_parameters(self):
        self._set_default()
        self.acq.pair_tablename.value = f"{self.acq.name()}spotpairs"
        self.acq.calib_tablename.value = f"{self.acq.name()}paircalib"
        self._init_labgeo()
        self._init_detgeo()
        self._init_recgeo()
        self._init_recAbsorption()
        self._init_recGrains()
        self.match.thetalimits.value = [
            self.detgeo.detanglemin() / 2,
            self.detgeo.detanglemax() / 2,
        ]
        self.acq.start_grp.value = 1  # TODO: incorporate to the dct_parameters tab
        self._init_diffractometer()
        self._init_prep()

    def save_parameter(self, path=None):
        if path is None:
            path = Path(self.acq.dir()) / "parameters.h5"
        else:
            path = Path(path)
        with h5py.File(path, "w") as h5file:
            # Recursively save all attributes
            self._save_group(h5file, "/", self)

    def load_parameter(self, path=None):
        if path is None:
            path = Path.cwd() / "parameters.h5"
        else:
            path = Path(path)
        h5file = loadFile(path)
        self.load_group(h5file, self)

    def _save_group(
        self,
        h5group: h5py.Group,
        group_name: str,
        instance: Any,
        current_path: str = "",
    ) -> None:
        """Recursively save a group's data from the instance into the HDF5 file."""
        group = h5group.create_group(group_name) if group_name != "/" else h5group
        # Resolve the attributes we want to persist: public Information fields first,
        # then other public attributes (e.g. nested BaseParameters or lists).
        info_fields = (
            instance._iter_information_field_names()
            if hasattr(instance, "_iter_information_field_names")
            else []
        )
        handled = set()

        def iter_public_attributes():
            # Yield Information fields with their declared (non-underscored) names.
            for name in info_fields:
                handled.add(name)
                yield name, getattr(instance, name)

            # Yield other non-private attributes from the instance dictionary.
            for attr, value in vars(instance).items():
                if attr == "internal" or attr.startswith("__"):
                    continue
                if attr.startswith("_") and attr.lstrip("_") in info_fields:
                    # Skip storage backing of InformationField descriptors.
                    continue
                if attr in handled:
                    continue
                yield attr, value

        for attr, value in iter_public_attributes():
            attr_path = self._join_h5_path(current_path, attr)
            if hasattr(value, "__dict__") and not isinstance(value, Information):
                self._save_group(group, attr, value, attr_path)
            elif isinstance(value, list) and value and hasattr(value[0], "__dict__"):
                s_group = group.create_group(attr)
                for index, item in enumerate(value):
                    list_path = self._join_h5_path(attr_path, f"{index:02d}")
                    self._save_group(s_group, f"{index:02d}", item, list_path)
            else:
                data, metadata_source = self._prepare_dataset_entry(value)
                dataset = self._create_dataset(group, attr, data)
                self._attach_dataset_attributes(dataset, attr_path, metadata_source)

    def _create_dataset(self, group, attr, data):
        """
        Helper method to create a dataset with error handling.
        """
        if data is None:
            data = np.nan
        try:
            return group.create_dataset(attr, data=data)
        except Exception as error:
            raise RuntimeError(f"Failed to create dataset '{attr}': {error}") from error
        return None

    def _prepare_dataset_entry(self, value: Any) -> tuple[Any, Optional["Information"]]:
        """Normalize values before serialization and capture metadata source."""
        metadata_source: Optional[Information] = (
            value if isinstance(value, Information) else None
        )
        actual_value = value() if isinstance(value, Information) else value
        if isinstance(actual_value, (Path, datetime)):
            actual_value = str(actual_value)
        elif isinstance(actual_value, np.ndarray):
            actual_value = actual_value.tolist()
        return actual_value, metadata_source

    def _attach_dataset_attributes(
        self,
        dataset: Optional[h5py.Dataset],
        path: str,
        metadata_source: Optional["Information"],
    ) -> None:
        """Write MATLAB metadata to the dataset if it is available."""
        if dataset is None:
            return
        attributes: dict[str, Any] = {}
        if isinstance(metadata_source, Information):
            attributes.update(metadata_source.hdf5_attributes)
        if not attributes:
            template = get_dataset_attributes(path)
            if template:
                attributes.update(template.asdict())

        for attr_name, attr_value in attributes.items():
            if attr_value is None:
                continue
            if attr_name == "MATLAB_Dimensions":
                attr_value = np.array(attr_value, dtype=np.int64)
            dataset.attrs[attr_name] = attr_value

    @staticmethod
    def _join_h5_path(prefix: str, name: str) -> str:
        """Normalize HDF5 paths to ensure a single leading slash."""
        normalized_prefix = (prefix or "").rstrip("/")
        if not normalized_prefix:
            return f"/{name}"
        if normalized_prefix == "/":
            return f"/{name}"
        return f"{normalized_prefix}/{name}"

    def load_group(self, h5group, instance):
        """
        Recursively load a group's data from the HDF5 file into the instance.
        """
        for key in h5group.get_keys():
            if isinstance(
                h5group.data.get(key), h5py.Group
            ):  # If it's a group, it's a nested class
                # Instantiate the class if it exists, otherwise create an empty class
                # If it's a group, we need to recursively load it
                if not hasattr(instance, key):
                    setattr(
                        instance, key, type("EmptyClass", (object,), {})()
                    )  # Create an empty dynamic class
                sub_instance = getattr(instance, key)
                self.load_group(h5group.get_value(key), sub_instance)
            else:
                data = h5group.get_value(key)
                if not hasattr(instance, key):
                    if hasattr(data, "dtype"):
                        dtype_name = data.dtype.name
                    else:
                        dtype_name = type(data).__name__
                    setattr(instance, key, Information("", dtype_name, None))
                target = getattr(instance, key)
                if hasattr(target, "value"):
                    target.value = data
                else:
                    setattr(instance, key, data)
        return instance


IndexStrategy_det = schema.IndexStrategy_det

if __name__ == "__main__":
    path = "/data/id11/inhouse1/DCT_round_robin/PROCESSED_DATA/sam_19/Parameters/parameters_ref.h5"
    dct_para = dct_parameter(path)
    pass
