import ipywidgets as widgets
from esrf_pathlib import ESRFPath as Path

from .MasterClass_Status import CheckFile, Experiment


class tomography_status(Experiment):
    def __init__(self, dpath: Path):
        self.main_path = Path(dpath)
        self.darks = CheckFile(self.main_path, "darks")
        self.flats = CheckFile(self.main_path, "flats")
        self.nabu = CheckFile(self.main_path, "nabu.log")
        # self.tomwer_processes = CheckFile(self.main_path, 'tomwer_processes')
        self.vol = CheckFile(self.main_path, "vol", True)
        self.plane_XY = CheckFile(self.main_path, "plane_XY", True)
        self.post_treatment: list[widgets.Widget] = [
            widgets.Label(
                "Follow the instructions to reconstruct a tomo dataset: https://confluence.esrf.fr/display/ID11KB/Reconstruction+using+Nabu+and+tomwer"
            )
        ]

        self.components: list[tuple[CheckFile, list[CheckFile], str]] = [
            (self.darks, [], "Darks"),
            (self.flats, [], "Flats"),
            (self.nabu, [], "Nabu"),
            # (self.tomwer_processes, [], 'Tomwer processes'),
            (self.vol, [], "Volume"),
            (self.plane_XY, [], "Plane XY"),
        ]
