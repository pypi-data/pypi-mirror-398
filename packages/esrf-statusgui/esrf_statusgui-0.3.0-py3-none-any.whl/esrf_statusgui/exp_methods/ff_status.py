from esrf_pathlib import ESRFPath as Path

from .MasterClass_Status import CheckFile, Experiment


class ff_status(Experiment):
    def __init__(self, dpath: Path):
        self.main_path = Path(dpath)
        self.sparse = CheckFile(self.main_path, "sparse")
        self.peaks_3d = CheckFile(self.main_path, "peaks_3d")
        self.peaks_table = CheckFile(self.main_path, "peaks_table")
        self.grains = CheckFile(self.main_path, "grains")
        self.dataset = CheckFile(self.main_path, "dataset")

        self.components: list[tuple[CheckFile, list[CheckFile], str]] = [
            (self.sparse, [], "Sparse"),
            (self.peaks_3d, [], "Peaks 3D"),
            (self.peaks_table, [], "Peaks table"),
            (self.grains, [], "Grains"),
            (self.dataset, [], "Dataset"),
        ]
