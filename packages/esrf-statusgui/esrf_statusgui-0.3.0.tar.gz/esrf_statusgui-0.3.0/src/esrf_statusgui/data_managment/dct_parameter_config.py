"""Configuration helpers for DCT parameter defaults."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

DEFAULT_PARAMETER_VALUES: Mapping[str, Any] = {
    "acq": {
        "type": "360degree",
        "true_detsizeu": 2048,
        "true_detsizev": 2048,
        "mono_tune": 0,
        "rotation_axis": "vertical",
        "flip_images": False,
        "no_direct_beam": False,
        "rotation_direction": "clockwise",
        "detector_definition": "inline",
        "beamchroma": "mono",
        "beamline": "ESRF-ID11",
        "flat": (1, 3),
        "dark": (4,),
        "projections": (2,),
    },
    "labgeo": {
        "beamdir": [1, 0, 0],
        "rotpos": [0, 0, 0],
        "rotdir": [0, 0, 1],
        "deflabX": "Along the beam direction.",
        "deflabY": "Right-handed from Y=cross(Z,X).",
        "deflabZ": "Along rotation axis. Positive away from sample stage.",
        "labunit": "mm",
    },
    "detgeo": {
        "detanglemin": 0,
        "detanglemax": 45,
        "detdiru": [0, 1, 0],
        "detdirv": [0, 0, -1],
    },
    "recgeo": {
        "voxsize": [1, 1, 1],
    },
    "samgeo": {
        "orig": [0, 0, 0],
        "dirx": [1, 0, 0],
        "diry": [0, 1, 0],
        "dirz": [0, 0, 1],
        "voxsize": [1, 1, 1],
    },
    "seg": {
        "method": "doublethr",
        "thr_single": 3,
        "thr_seed": 50,
        "thr_grow_rat": 0.1,
        "thr_grow_low": 7,
        "thr_grow_high": 20,
        "seedminarea": 10,
        "minsize": 50,
        "omintlimmin": 0.0005,
        "omintlimtail": 0.0005,
        "minblobsize": [10, 10, 0],
        "maxblobsize": [300, 300, 40],
        "extendblobinc": [30, 30, 2],
        "background_subtract": True,
        "overlaps_removed": False,
        "difspotmask": "blob3Dsoft",
        "debug": False,
        "writeblobs": True,
        "writespots": True,
        "writeedfs": False,
        "writehdf5": True,
        "wrapping": True,
        "segmentation_stack_size": 1000,
        "background_subtract_accelerate": True,
        "write_sub_volumes": "matfile",
        "write_same_size": True,
    },
    "match": {
        "thr_theta": 0.2,
        "thr_theta_scale": 0,
        "thr_max_offset": 2,
        "thr_ext_offset": 10,
        "thr_genim_offset": 2,
        "thr_intint": 6,
        "thr_area": 1.6,
        "thr_bbsize": 1.5,
        "minsizeu": 5,
        "minsizev": 5,
        "addconstr": "",
        "thr_meanerror": float("inf"),
        "thetalimits": [0, 22.5],
        "uniquetheta": 0.1,
    },
    "index": {
        "strategy": {
            "iter": 5,
            "rfzext": 0.005,
            "b": {
                "beg": {
                    "ang": 0.05,
                    "int": 5,
                    "bbxs": 1.3,
                    "bbys": 1.3,
                    "distf": 0.1,
                    "distmax": 0.002,
                    "ming": 5,
                },
                "end": {
                    "ang": 1,
                    "int": 50,
                    "bbxs": 3,
                    "bbys": 2,
                    "distf": 0.3,
                    "distmax": 0.02,
                    "ming": 4,
                },
            },
            "m": {
                "beg": {
                    "int": 5,
                    "bbxs": 1.3,
                    "bbys": 1.3,
                    "distf": 0.5,
                    "distmin": 0,
                    "distmax": float("inf"),
                    "angf": 0,
                    "angmin": 1,
                    "angmax": 1,
                },
                "end": {
                    "int": 50,
                    "bbxs": 3,
                    "bbys": 2,
                    "distf": 0.5,
                    "distmin": 0,
                    "distmax": float("inf"),
                    "angf": 0,
                    "angmin": 1.5,
                    "angmax": 1.5,
                },
            },
            "s": {"stdf": 4},
            "x": {"stdf": 4},
        }
    },
    "fsim": {
        "check_spot": False,
        "omegarange": 0.5,
        "MaxOmegaOffset": 1,
        "assemble_figure": True,
        "display_figure": True,
        "clims": [-50, 800],
        "Rdist_factor": 3,
        "bbsize_factor": 2,
        "oversize": 1.6,
        "oversizeVol": 1.2,
        "use_th": True,
        "verbose": False,
        "save_grain": True,
        "sel_lh_stdev": 1,
        "sel_int_stdev": 1,
        "sel_avint_stdev": 1,
        "mode": "indexter",
        "thr_check": 0.1,
    },
    "rec": {
        "absorption": {
            "algorithm": "SIRT",
            "num_iter": 100,
            "interval": 10,
            "padding": 5,
        },
        "grains": {
            "algorithm": "SIRT",
            "num_iter": 100,
        },
        "thresholding": {
            "percentile": 20,
            "percent_of_peak": 2.5,
            "do_morph_recon": True,
            "do_region_prop": True,
            "num_iter": 0,
            "iter_factor": 1,
            "mask_border_voxels": 5,
            "use_levelsets": False,
        },
    },
    "diffractometer": {
        "motor_basetilt": "diffry",
        "axes_basetilt": [0, 1, 0],
        "motor_rotation": "diffrz",
        "axes_rotation": [0, 0, 1],
        "motor_samtilt_bot": "samry",
        "axes_samtilt_bot": [0, 1, 0],
        "motor_samtilt_top": "samrx",
        "axes_samtilt_top": [1, 0, 0],
        "origin_rotation": [0, 0, 0],
        "origin_samtilt_bot": [0, 0, 0],
        "origin_samtilt_top": [0, 0, 0],
        "limits_samtilt_bot": [-15, 15],
        "limits_samtilt_top": [-20, 20],
        "angles_basetilt": 0,
        "angles_rotation": 0,
        "angles_samtilt_bot": 0,
        "angles_samtilt_top": 0,
        "origin_basetilt": [0, 0, 0],
        "shifts_sam_stage": [0, 0, 0],
        "num_axes": 4,
        "motor_samtx": "samtx",
        "motor_samty": "samty",
        "motor_samtz": "samtz",
    },
    "prep": {
        "margin": 5,
        "intensity": 1800,
        "filtsize": [1, 1],
        "drifts_pad": "av",
        "renumbered": False,
        "normalisation": "none",
    },
}


def apply_default_values(parameters: Any) -> None:
    """Populate unset `Information` fields with the configured defaults."""

    def set_defaults_recursive(target: Any, defaults: Mapping[str, Any]) -> None:
        for attr_name, default_value in defaults.items():
            attr = getattr(target, attr_name, None)
            if attr is None:
                continue
            if isinstance(default_value, Mapping):
                set_defaults_recursive(attr, default_value)
            elif hasattr(attr, "value") and attr.value is None:
                attr.value = default_value

    for group_name, attrs in DEFAULT_PARAMETER_VALUES.items():
        group = getattr(parameters, group_name, None)
        if group is not None:
            set_defaults_recursive(group, attrs)
