# Help & How-To

This note collects the day-to-day recipes for running the Status GUI inside notebooks, configuring data roots, and reusing the helper functions shipped with the package.

## Launching the widget

- Install with GUI extras in your virtualenv: `pip install -e ".[gui]"`.
- Start Jupyter (Notebook or Lab) on an ID11 host that can see the ESRF storage tree.
- In a new cell:

  ```python
  from esrf_statusgui.visualization.statusGUI import DatasetSelectionTab

  tab = DatasetSelectionTab()
  tab.display()  # or simply DatasetSelectionTab() in a Notebook cell
  ```

- The `statusgui`/`statusGUI` console scripts wrap the same entrypoint but still require an IPython kernel; prefer using them from within Jupyter.

## Pointing to the right visitor root

- Default root is `/data/visitor`. Override before instantiating the GUI:

  ```python
  from esrf_statusgui.file_utils.paths import set_visitor_root
  set_visitor_root("/mnt/id11_archive")
  ```

- Environment alternative: export `ESRF_VISITOR_ROOT=/mnt/id11_archive`.
- To inspect how a path is parsed (proposal, beamline, session date):

  ```python
  from esrf_statusgui.file_utils.paths import describe
  info = describe("/data/visitor/ma1234/id11/20240101/RAW_DATA")
  print(info.proposal, info.beamline, info.session_date)
  ```

## Navigating datasets in the GUI

- Use the proposal/beamline/date selectors at the top to populate the folder tree. Breadcrumb buttons let you jump back up the hierarchy quickly.
- Four columns show per-technique state: Tomography (PCT), DCT, FF, s3DXRD. Colors: red = not processed, orange = in progress/partial, green = complete.
- Expanding a dataset accordion lists the files probed for that step and exposes quick actions (open generated notebooks, refresh status, launch processing).
- Use the `Data root` field + `Use path` button when you want to browse a mirror without changing `ESRF_VISITOR_ROOT`.

## Creating or preparing processing notebooks

Programmatic helpers under `esrf_statusgui.file_utils.createProcessingNotebook` inject run-specific paths into checked-in notebook templates:

```python
from esrf_pathlib import ESRFPath as Path
from esrf_statusgui.file_utils.createProcessingNotebook import (
    create_processing_nb_DCT,
    create_processing_nb_FF,
    create_processing_nb_SFF,
)

# DCT tutorial notebook tailored to your dataset folder
create_processing_nb_DCT(Path("/data/visitor/.../PROCESSED_DATA/MyDataset"), "MyDataset")

# ImageD11 FF notebooks
create_processing_nb_FF(
    raw_path=Path("/data/visitor/.../RAW_DATA"),
    processed_path=Path("/data/visitor/.../PROCESSED_DATA/sample/sample_ff1"),
    sample="sample",
    dataset="sample_ff1",
)

# S3DXRD notebooks
create_processing_nb_SFF(
    raw_path=Path("/data/visitor/.../RAW_DATA"),
    processed_path=Path("/data/visitor/.../PROCESSED_DATA/sample/sample_s3dxrd"),
    sample="sample",
    dataset="sample_s3dxrd",
)
```

The helpers derive analysis roots, dataset prefixes, and known parameter files (`pars.json`) when present, then write the modified notebooks under the target `PROCESSED_DATA` path.

## Seeding DCT preprocessing from Python

`pySetupH5.setup_pre_processing` builds the DCT-ready HDF5 structure and reports missing groups inline:

```python
from esrf_statusgui.visualization.DCT.pySetupH5 import pySetupH5

setup = pySetupH5()
setup.setup_pre_processing(
    {
        "raw_path": "/data/visitor/.../RAW_DATA/dataset.h5",
        "dataset_name": "dataset_clean",
        "projections_group": 5,
        "flat_groups": [1, 3],
        "dark_group": 4,
    }
)
```

Group defaults are 1-3/4/2 (flats/darks/projections); pass explicit values when the acquisition differs.

## Scaffolding experiment folders

- Create a new date layout with processed/scripts folders: `newExperimentDate(Path("/data/visitor/ma1234/id11/20250101"))`.
- Build DCT processing directories (rawdata, difspot, grains, reconstruction, etc.) with `create_DCT_directories(base_dir, name)`. Permissions are normalised for the proposal group when possible.

## Quick troubleshooting

- Empty lists: ensure the host can see the visitor root; override via `set_visitor_root` if you are on a mirror.
- No widgets rendered: check that the `ipywidgets` extension is enabled and that you are running inside Jupyter/IPython.
- DCT MATLAB hooks: start MATLAB through the facility module (`module load dct`), add the DCT code to the MATLAB path, and share the engine with `matlab.engine.shareEngine` before triggering processing from the GUI.
