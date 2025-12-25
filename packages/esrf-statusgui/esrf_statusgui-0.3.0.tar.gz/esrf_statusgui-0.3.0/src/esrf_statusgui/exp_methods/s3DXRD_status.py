from esrf_pathlib import ESRFPath as Path

from .MasterClass_Status import CheckFile, Experiment


class s3DXRD_status(Experiment):
    def __init__(self, dpath: Path):
        self.main_path = Path(dpath)
        self.sparse = CheckFile(self.main_path, "sparse")
        self.peaks_table = CheckFile(self.main_path, "peaks_table")
        self.peaks_4d = CheckFile(self.main_path, "peaks_4d")
        self.refine = CheckFile(self.main_path, "refine")
        self.grains = CheckFile(self.main_path, "grains")
        self.dataset = CheckFile(self.main_path, "dataset")

        self.components: list[tuple[CheckFile, list[CheckFile], str]] = [
            (self.sparse, [], "Sparse"),
            (self.peaks_table, [], "Peaks table"),
            (self.peaks_4d, [], "Peaks 4D"),
            (self.refine, [], "Refine"),
            (self.grains, [], "Grains"),
            (self.dataset, [], "Dataset"),
        ]
