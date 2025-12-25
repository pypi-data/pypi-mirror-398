# Add the 'lib' folder to the Python path
from __future__ import annotations

import logging
import os
import shutil
from functools import lru_cache
from importlib import resources
from importlib.abc import Traversable
from os import fspath

import nbformat
from esrf_pathlib import ESRFPath as Path

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _resolve_nb_path(method: str, resource_name: str) -> Traversable:
    """
    Locate the canonical processing notebook from the installed package.
    """
    package = f"esrf_statusgui.notebooks.{method}"
    try:
        notebook = resources.files(package).joinpath(resource_name)
    except ModuleNotFoundError as error:
        raise FileNotFoundError(
            f"Package '{package}' is not available; cannot locate {method} template notebook."
        ) from error

    if not notebook.is_file():
        raise FileNotFoundError(
            f"{method} template notebook '{resource_name}' not found in package '{package}'."
        )
    return Path(notebook)


def create_processing_nb_DCT(out_folder: Path, dataset_name: str) -> None:
    """
    Create a customized copy of the DCT tutorial notebook with environment-specific paths.
    """

    nb_path = _resolve_nb_path("dct", "Tuto_2_ProcessDCT.ipynb")

    # ---------- 0_segment_frelon.ipynb ----------
    nb = _nb_load(nb_path)
    _nb_replace_in_cell(
        nb,
        cell_index=4,
        replacements={
            "dataset = Path('')": f"dataset = Path('{str(out_folder)}')",
        },
    )
    logger.info("Creating directory %s (parents=True, exist_ok=True)", out_folder)
    out_folder.mkdir(parents=True, exist_ok=True)
    _nb_save(nb, out_folder / f"{dataset_name}.ipynb")
    nb = None


def create_processing_nb_FF(
    raw_path: Path,
    processed_path: Path,
    sample: str,
    dataset: str,
) -> None:
    """
    Prepare ImageD11 processing notebooks by injecting run-specific parameters and
    saving the modified notebooks to `processed_path`.

    Parameters
    ----------
    raw_path : Path
        Root directory containing raw data. Expected to contain a `<sample>/` subdir.
    processed_path : Path
        Destination directory where modified notebooks will be written.
    sample : str
        Sample name (e.g., "mysample").
    dataset : str
        Dataset name (e.g., "mysample_ff1").
    """
    canonical_nb = _resolve_nb_path("imaged11.TDXRD", "0_segment_frelon.ipynb")
    notebook_dir = canonical_nb.parent
    notebooks = [
        "0_segment_frelon.ipynb",
        "1_index_default.ipynb",
        "1_index_friedel.ipynb",
        "1_index_grid.ipynb",
        "2_run_papermill.ipynb",
        "3_merge_slices.ipynb",
        "0_segment_eiger.ipynb",
    ]

    created_dir = False
    try:
        if not processed_path.exists():
            logger.info(
                "Creating directory %s (parents=True, exist_ok=True)", processed_path
            )
            processed_path.mkdir(parents=True, exist_ok=True)
            created_dir = True

        # Derived fields
        analysis_root = processed_path.parent.parent
        dataset_h5 = processed_path / f"{dataset}_dataset.h5"
        ds_prefix = dataset.replace(f"{sample}_", "", 1)
        par_path = _safe_guess_par_file(processed_path)

        # ---------- 0_segment_frelon.ipynb ----------
        nb = _nb_load(notebook_dir / notebooks[0])
        _nb_replace_in_cell(
            nb,
            cell_index=3,
            replacements={
                "dataroot = None": f"dataroot = '{raw_path}'",
                "analysisroot = None": f"analysisroot = '{analysis_root}'",
                "sample = None": f"sample = '{sample}'",
                "dataset = None": f"dataset = '{ds_prefix}'",
            },
        )
        _nb_save(nb, processed_path / notebooks[0])
        nb = None

        # ---------- 1_index_* notebooks (indices 1..3) ----------
        for idx in range(1, 4):
            nb = _nb_load(notebook_dir / notebooks[idx])
            repl = {
                "dset_path = ''": f"dset_path = '{dataset_h5}'",
                "dset_prefix = 'ff'": f"dset_prefix = '{ds_prefix}'",
            }
            if par_path is not None:
                repl["parfile = ''"] = f"parfile = '{par_path}'"
            _nb_replace_in_cell(nb, cell_index=2, replacements=repl)
            _nb_save(nb, processed_path / notebooks[idx])
            nb = None

        # ---------- 2_run_papermill.ipynb ----------
        nb = _nb_load(notebook_dir / notebooks[4])
        datasets_for_sample: list[str] = []
        sample_dir = raw_path / sample
        try:
            with os.scandir(sample_dir) as entries:
                for entry in entries:
                    if not entry.is_dir():
                        continue
                    if entry.name == dataset or "_ff" not in entry.name:
                        continue
                    datasets_for_sample.append(entry.name.replace(f"{sample}_", "", 1))
        except OSError:
            logger.debug("Failed to list datasets in %s", sample_dir, exc_info=True)
        samples_dict_literal = f"{{'{sample}': {datasets_for_sample}}}"
        _nb_replace_in_cell(
            nb,
            cell_index=2,
            replacements={
                'dset_path = "path/to/dataset.h5"': f"dset_path = '{dataset_h5}'",
                "dset_prefix = 'ff'": f"dset_prefix = '{ds_prefix}'",
                "skips_dict = {'sample':['ff1']}": f"skips_dict = {{'{sample}':['{ds_prefix}']}}",
                "samples_dict = None": f"samples_dict = {samples_dict_literal}",
                "notebooks_to_run = None": (
                    "notebooks_to_run = [\n"
                    "        ('0_segment_frelon.ipynb', {}),\n"
                    "        ('1_index_default.ipynb', {}),\n"
                    "    ]"
                ),
            },
        )
        _nb_save(nb, processed_path / notebooks[4])
        nb = None

        # ---------- 3_merge_slices.ipynb ----------
        nb = _nb_load(notebook_dir / notebooks[5])
        _nb_replace_in_cell(
            nb,
            cell_index=2,
            replacements={
                "dset_path = ''": f"dset_path = '{dataset_h5}'",
                "dset_prefix = 'ff'": f"dset_prefix = '{ds_prefix}'",
            },
        )
        _nb_save(nb, processed_path / notebooks[5])
        nb = None

        # ---------- 0_segment_eiger.ipynb ----------
        if (notebook_dir / notebooks[6]).exists():
            nb = _nb_load(notebook_dir / notebooks[6])
            _nb_replace_in_cell(
                nb,
                cell_index=2,
                replacements={
                    "dataroot = None": f"dataroot = '{raw_path}'",
                    "analysisroot = None": f"analysisroot = '{analysis_root}'",
                    "sample = None": f"sample = '{sample}'",
                    "dataset = None": f"dataset = '{ds_prefix}'",
                },
            )
            _nb_save(nb, processed_path / notebooks[6])
            nb = None

        try:
            src = notebook_dir / "use_only_if_needed"
            if src.exists():
                shutil.copytree(
                    src, processed_path / "use_only_if_needed", dirs_exist_ok=True
                )
        except Exception:
            logger.debug("Copying helper notebooks failed", exc_info=True)

    except Exception:
        if created_dir and processed_path.exists():
            try:
                shutil.rmtree(processed_path)
            except Exception:
                logger.debug("Cleanup of %s failed", processed_path, exc_info=True)
        raise


def create_processing_nb_SFF(
    raw_path: Path, processed_path: Path, sample: str, dataset: str
) -> None:
    """
    Prepare SFF notebooks by injecting run parameters and writing them to `processed_path`.

    Parameters
    ----------
    raw_path : Path
        Root directory for raw data (expects `<raw_path>/<sample>/...`).
    processed_path : Path
        Output directory for modified notebooks.
    sample : str
        Sample name (e.g., "mysample").
    dataset : str
        Dataset name (e.g., "mysample_ff1").
    """
    canonical_nb = _resolve_nb_path("imaged11.S3DXRD", "0_segment_frelon.ipynb")
    notebook_dir = canonical_nb.parent
    notebooks: list[str] = [
        "0_segment_and_label.ipynb",  # 0
        "0_segment_frelon.ipynb",  # 1
        "tomo_1_index.ipynb",  # 2
        "tomo_1_index_minor_phase.ipynb",  # 3
        "tomo_2_map.ipynb",  # 4
        "tomo_2_map_minor_phase.ipynb",  # 5
        "tomo_3_refinement.ipynb",  # 6
        "pbp_1_indexing.ipynb",  # 7
        "pbp_2_visualise.ipynb",  # 8
        "pbp_3_refinement.ipynb",  # 9
        "4_visualise.ipynb",  # 10
        "5_combine_phases.ipynb",  # 11
        "6_run_papermill.ipynb",  # 12
        "7_stack_layers.ipynb",  # 13
        "friedel_pair_map.ipynb",  # 14
        "import_test_data.ipynb",  # 15
        "run_astra_recon.py",  # 16
        "run_mlem_recon.py",  # 17
        "run_pbp_recon.py",  # 18
        "run_pbp_refine.py",  # 19
        "select_for_index_unknown.ipynb",  # 20
    ]

    created_dir = False
    try:
        if not processed_path.exists():
            logger.info(
                "Creating directory %s (parents=True, exist_ok=True)", processed_path
            )
            processed_path.mkdir(parents=True, exist_ok=True)
            created_dir = True

        # Derived values
        analysis_root = processed_path.parent.parent
        ds_prefix = dataset.replace(f"{sample}_", "", 1)
        dataset_h5 = processed_path / f"{dataset}_dataset.h5"
        par_path = _safe_guess_par_file(processed_path)

        common_replacements = {
            "dataroot = None": f"dataroot = '{raw_path}'",
            "analysisroot = None": f"analysisroot = '{analysis_root}'",
            "sample = None": f"sample = '{sample}'",
            "dataset = None": f"dataset = '{ds_prefix}'",
        }

        # ---------- 0_segment_and_label.ipynb ----------
        nb = _nb_load(notebook_dir / notebooks[0])
        _nb_replace_in_cell(
            nb, cell_index=2, replacements=common_replacements, required_type="code"
        )
        _nb_save(nb, processed_path / notebooks[0])
        nb = None

        # ---------- 0_segment_frelon.ipynb ----------
        nb = _nb_load(notebook_dir / notebooks[1])
        _nb_replace_in_cell(
            nb, cell_index=3, replacements=common_replacements, required_type="code"
        )
        _nb_save(nb, processed_path / notebooks[1])
        nb = None

        # ---------- tomo_1_index.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[2])
        repl = {
            "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            "dset_prefix = 'ff'": f"dset_prefix = '{ds_prefix}'",
        }
        if par_path is not None:
            repl["parfile = ''"] = f"parfile = '{par_path}'"
        _nb_replace_in_cell(nb, cell_index=3, replacements=repl, required_type="code")
        _nb_save(nb, processed_path / notebooks[2])
        nb = None

        # ---------- tomo_1_index_minor_phase.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[3])
        _nb_replace_in_cell(
            nb,
            cell_index=3,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[3])
        nb = None

        # ---------- tomo_2_map.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[4])
        _nb_replace_in_cell(
            nb,
            cell_index=4,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[4])
        nb = None

        # ---------- tomo_2_map_minor_phase.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[5])
        _nb_replace_in_cell(
            nb,
            cell_index=4,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[5])
        nb = None

        # ---------- tomo_3_refinement.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[6])
        _nb_replace_in_cell(
            nb,
            cell_index=4,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[6])
        nb = None

        # ---------- pbp_1_indexing.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[7])
        repl = {
            "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
        }
        if par_path is not None:
            repl["parfile = ''"] = f"parfile = '{par_path}'"
        _nb_replace_in_cell(nb, cell_index=4, replacements=repl, required_type="code")
        _nb_save(nb, processed_path / notebooks[7])
        nb = None

        # ---------- pbp_2_visualise.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[8])
        _nb_replace_in_cell(
            nb,
            cell_index=4,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[8])
        nb = None

        # ---------- pbp_3_refinement.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[9])
        _nb_replace_in_cell(
            nb,
            cell_index=4,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[9])
        nb = None

        # ---------- 4_visualise.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[10])
        _nb_replace_in_cell(
            nb,
            cell_index=4,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[10])
        nb = None

        # ---------- 5_combine_phases.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[11])
        _nb_replace_in_cell(
            nb,
            cell_index=2,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[11])
        nb = None

        # ---------- 6_run_papermill.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[11])
        datasets_for_sample = []
        sample_dir = raw_path / sample
        try:
            with os.scandir(sample_dir) as entries:
                for entry in entries:
                    if not entry.is_dir():
                        continue
                    if entry.name == dataset or "_ff" not in entry.name:
                        continue
                    datasets_for_sample.append(entry.name.replace(f"{sample}_", "", 1))
        except OSError:
            logger.debug("Failed to list datasets in %s", sample_dir, exc_info=True)
        samples_dict_literal = f"{{'{sample}': {datasets_for_sample}}}"
        _nb_replace_in_cell(
            nb,
            cell_index=2,
            replacements={
                'dset_path = "path/to/dataset.h5"': f"dset_path = '{dataset_h5}'",
                "dset_prefix = 'ff'": f"dset_prefix = '{ds_prefix}'",
                "skips_dict = {'sample':['ff1']}": f"skips_dict = {{'{sample}':['{ds_prefix}']}}",
                "samples_dict = None": f"samples_dict = {samples_dict_literal}",
                "notebooks_to_run = None": (
                    "notebooks_to_run = [\n"
                    "        ('0_segment_and_label.ipynb', {}),\n"
                    "        ('tomo_1_index.ipynb', {}),\n"
                    "        ('tomo_2_map.ipynb', {}),\n"
                    "        ('tomo_3_refinement.ipynb', {}),\n"
                    "        ('4_visualise.ipynb', {}),\n"
                    "    ]"
                ),
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[11])
        nb = None

        # ---------- 7_stack_layers.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[13])
        _nb_replace_in_cell(
            nb,
            cell_index=2,
            replacements={
                "dset_path = 'si_cube_test/processed/Si_cube/Si_cube_S3DXRD_nt_moves_dty/Si_cube_S3DXRD_nt_moves_dty_dataset.h5'": f"dset_path = '{dataset_h5}'",
                'dset_prefix = "top_"': f"dset_prefix = '{ds_prefix}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[13])
        nb = None

        # ---------- friedel_pair_map.ipynb ----------#
        nb = _nb_load(notebook_dir / notebooks[14])
        _nb_replace_in_cell(
            nb,
            cell_index=1,
            replacements={
                'dset_file ="/path/to/dataset"': f"dset_path = '{dataset_h5}'",
            },
            required_type="code",
        )
        _nb_save(nb, processed_path / notebooks[14])
        nb = None

    except Exception:
        if created_dir and processed_path.exists():
            try:
                shutil.rmtree(processed_path)
            except Exception:
                logger.debug("Cleanup of %s failed", processed_path, exc_info=True)
        raise


def guess_par_file(proccessed_path: Path):
    """
    Best-effort search for a pars.json file under the PROCESSED_DATA folder.
    """
    if "PROCESSED_DATA" in str(proccessed_path):
        proc_main_path = (
            Path(str(proccessed_path).split("PROCESSED_DATA")[0]) / "PROCESSED_DATA"
        )
        if (proc_main_path / "pars.json").is_file():
            return proc_main_path / "pars.json"
        for path in proc_main_path.rglob("*par*"):
            if path.is_dir() and (path / "pars.json").is_file():
                return path / "pars.json"


# ---------- helpers ----------
def _nb_load(nb_path: Traversable | Path | str) -> nbformat.NotebookNode:
    opener = getattr(nb_path, "open", None)
    if opener is not None:
        with opener("r", encoding="utf-8") as fh:
            return nbformat.read(fh, as_version=4)  # type: ignore[reportUnknownMemberType]

    with open(fspath(nb_path), encoding="utf-8") as fh:
        return nbformat.read(fh, as_version=4)  # type: ignore[reportUnknownMemberType]


def _nb_save(nb: nbformat.NotebookNode, out_path: Path):
    with open(out_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)  # type: ignore[reportUnknownMemberType]


def _nb_replace_in_cell(
    nb: nbformat.NotebookNode,
    cell_index: int | None,
    replacements: dict[str, str],
    required_type: str | None = "code",
    *,
    _allow_fallback: bool = True,
) -> None:
    """
    Replace literal substrings in the source of a given cell if it exists and (optionally) matches `required_type`.
    If `required_type` is None, we skip type checking.
    """
    indices: list[int]
    if cell_index is None:
        indices = list(range(len(nb.cells)))  # type: ignore[reportUnknownMemberType]
    else:
        indices = [cell_index] if 0 <= cell_index < len(nb.cells) else []

    replaced = False
    for idx in indices:
        cell = nb.cells[idx]
        if required_type and getattr(cell, "cell_type", None) != required_type:
            continue
        src = cell.source or ""
        updated = src
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != src:
            cell.source = updated
            replaced = True

    if not replaced and cell_index is not None and _allow_fallback:
        _nb_replace_in_cell(
            nb,
            cell_index=None,
            replacements=replacements,
            required_type=required_type,
            _allow_fallback=False,
        )


def _nb_set_cell_source_if_type(nb, idx: int, cell_type: str, new_source: str) -> None:
    """Set cell source only if the target cell exists and is of the specified type."""
    if (
        0 <= idx < len(nb.cells)
        and getattr(nb.cells[idx], "cell_type", None) == cell_type
    ):
        nb.cells[idx].source = new_source


def _safe_guess_par_file(path: Path) -> Path | None:
    """Call user-provided guess_par_file if available; otherwise return None."""
    try:
        # Provided by the caller's environment
        return guess_par_file(path)  # type: ignore[name-defined]
    except Exception as error:
        logger.debug("guess_par_file failed for %s: %s", path, error, exc_info=True)
        return None
