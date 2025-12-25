from __future__ import annotations

import os
import urllib.request
from pathlib import Path
from typing import Optional, Union, Dict, Tuple

from .ase_calculator import ase_calculator

# --- Optional: use MACE's cache helper if available, else fallback ---
try:
    from mace.tools.utils import get_cache_dir
except Exception:
    def get_cache_dir() -> str:
        cache = os.path.join(os.path.expanduser("~"), ".cache", "mace")
        os.makedirs(cache, exist_ok=True)
        return cache

# -------------------------
# Registry of known models
# -------------------------
# Extend as needed; keep license tags accurate.
_MODEL_REGISTRY: Dict[str, Dict[str, str]] = {
    # MIT (safe to auto-download or vendor)
    "mpa-0-medium": {
        "url": "https://github.com/ACEsuit/mace-mp/releases/download/mace_mpa_0/mace-mpa-0-medium.model",
        "license": "MIT",
    },
    "mp-0b3-medium": {
        "url": "https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0b3/mace-mp-0b3-medium.model",
        "license": "MIT",
    },
    # ASL (Academic Software License; non-commercial; explicit consent required)
    "omat-0-small": {
        "url": "https://github.com/ACEsuit/mace-mp/releases/download/mace_omat_0/mace-omat-0-small.model",
        "license": "ASL",
    },
    "omat-0-medium": {
        "url": "https://github.com/ACEsuit/mace-mp/releases/download/mace_omat_0/mace-omat-0-medium.model",
        "license": "ASL",
    },
    "matpes-pbe-0": {
        "url": "https://github.com/ACEsuit/mace-foundations/releases/download/mace_matpes_0/MACE-matpes-pbe-omat-ft.model",
        "license": "ASL",
    },
    "matpes-r2scan-0": {
        "url": "https://github.com/ACEsuit/mace-foundations/releases/download/mace_matpes_0/MACE-matpes-r2scan-omat-ft.model",
        "license": "ASL",
    },
    "off23-medium": {
        "url": "https://github.com/ACEsuit/mace-off/raw/main/mace_off23/MACE-OFF23_medium.model?raw=true",
        "license": "ASL",
    },
}

def _resolve_model_spec(spec: Optional[Union[str, Path]]) -> Tuple[str, str, str]:
    """
    Resolve user spec into (name_or_path, license, url_or_path).

    Rules:
      - None -> default "mpa-0-medium" (MIT)
      - existing local path -> ("<path>", "LOCAL", "<path>")
      - http(s) URL -> ("<url>", "UNKNOWN", "<url>")
      - registry key -> ("<key>", license, url)
      - else -> error
    """
    if spec is None:
        entry = _MODEL_REGISTRY["mpa-0-medium"]
        return "mpa-0-medium", entry["license"], entry["url"]

    s = str(spec)
    p = Path(s)
    if p.exists() and p.is_file():
        return s, "LOCAL", s

    if s.startswith("http://") or s.startswith("https://"):
        return s, "UNKNOWN", s

    if s in _MODEL_REGISTRY:
        entry = _MODEL_REGISTRY[s]
        return s, entry["license"], entry["url"]

    # If user left the old default 'MACE_model.model' and it doesn't exist,
    # choose a sensible default instead of failing hard.
    if s == "MACE_model.model":
        entry = _MODEL_REGISTRY["mpa-0-medium"]
        return "mpa-0-medium", entry["license"], entry["url"]

    raise ValueError(
        f"Unrecognized model spec '{spec}'. Provide a local file, a URL, or one of: "
        + ", ".join(sorted(_MODEL_REGISTRY.keys()))
    )

def _assert_license_ok(license_tag: str, allow_asl: bool) -> None:
    if license_tag != "ASL":
        return
    accepted_env = os.environ.get("MACE_ACCEPT_ASL", "") == "1"
    if not (allow_asl or accepted_env):
        raise RuntimeError(
            "Requested model is under the Academic Software License (ASL). "
            "To proceed, pass allow_asl=True to mace_calculator(...) or set environment "
            "variable MACE_ACCEPT_ASL=1. Ensure your usage complies with ASL (non-commercial)."
        )

def _download_if_needed(url_or_path: str, cache_root: Optional[str] = None) -> str:
    """Return a local path; download into cache if given a URL."""
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        cache = cache_root or get_cache_dir()
        os.makedirs(cache, exist_ok=True)
        fname = os.path.basename(url_or_path.split("?")[0]) or "mace.model"
        dest = os.path.join(cache, fname)
        if not os.path.isfile(dest):
            print(f"Downloading MACE checkpoint from: {url_or_path}")
            tmp = dest + ".part"
            urllib.request.urlretrieve(url_or_path, tmp)
            os.replace(tmp, dest)
            print(f"Saved checkpoint to: {dest}")
        return dest
    # local path
    if not Path(url_or_path).exists():
        raise FileNotFoundError(f"Model file not found: {url_or_path}")
    return url_or_path

def mace_calculator(
    calc_path: str = 'MACE_model.model',


    device: str = 'cuda',
    default_dtype: str = 'float32',
    enable_cueq: bool = False,

    # --- Stage 1: MD / relaxation controls ---
    nvt_steps: Union[int, Sequence[float], None] = None,

    # --- Stage 2: relaxation controls ---
    fmax: Union[float, Sequence[float], None] = 0.05,
    steps_max: int = 100,
    hydrostatic_strain: bool = False,
    constant_volume: bool = True,
    optimizer: str = 'FIRE',

    # --- temperature schedules ---
    T: Union[float, Sequence[float]] = 300.0,
    T_ramp: bool = False,  # reserved for future use
    # --- timestep (fs) for the MD integrator ---
    md_timestep_fs: float = 1.0,

    # --- vibrational correction controls ---
    vib_correction: bool = False,
    vib_store_interval: int = 1,
    vib_min_samples: int = 200,
    remove_com_drift: bool = False,
    mass_weighted_com: bool = True,
    vacf_window: str = "hann",

    # --- logging / IO performance knobs ---
    log_interval: int = 0,          # 0 disables printing; otherwise print every k steps
    write_interval: int = 0,        # trajectory write every k steps; set 0 to disable during MD

    # --- constraint controls ---
    constraint_logic: str = "all",
    constraint_action: str = "freeze",
    freeze_components: Optional[Sequence[Union[int, str]]] = None,
    constraints: Optional[Sequence[Callable]] = None,

    # --- Stage 0: pre-MD relaxation controls ---
    pre_relax_fmax: Union[float, Sequence[float], None] = None,
    pre_relax_steps_max: int = 0,
    pre_relax_optimizer: str = 'FIRE',
    pre_relax_constant_volume: bool = True,
    pre_relax_hydrostatic_strain: bool = False,
    pre_relax_with_constraints: bool = True,

    # --- vibrational spectrum controls ---
    vib_spectrum: bool = False,
    vib_spectrum_max_lag: int = None,
    vib_spectrum_cutoff_cm1: float = 3200.0,
    vib_spectrum_mode: str = "total",   # 'total' | 'atom' | 'element' | 'all'

    # --- new optional knobs ---
    allow_asl: bool = False,         # require explicit acceptance for ASL models
    cache_dir: Optional[str] = None, # override cache directory if desired
):
    r"""
    Create an ASE calculator that uses a MACE model specified by *either*:
      - a local file path to a .model,
      - a direct URL (http/https), or
      - a registry model name (e.g., "mpa-0-medium", "mp-0b3-medium", "omat-0-medium").

    If a name/URL is provided, the model is downloaded (once) into a cache and the
    resolved local path is passed to MACECalculator(model_paths=...).

    Parameters (selected)
    ---------------------
    calc_path : str
        Path, URL, or registry key. Default keeps backward compatibility.
        If it is the legacy default ('MACE_model.model') and the file is missing,
        it falls back to 'mpa-0-medium' (MIT).
    allow_asl : bool
        Required to load ASL-licensed models (OMAT/MATPES/OFF/…).
        Alternatively set environment variable MACE_ACCEPT_ASL=1.
    cache_dir : str | None
        Custom cache directory for downloaded models.

    Other parameters are forwarded to your ase_calculator wrapper unchanged.
    """
    # Resolve spec (name/path/url) and enforce license where applicable
    name, license_tag, url_or_path = _resolve_model_spec(calc_path)
    _assert_license_ok(license_tag, allow_asl=allow_asl)

    # Ensure we have a local file we can feed to MACECalculator
    model_local_path = _download_if_needed(url_or_path, cache_root=cache_dir)

    # Lazy import to keep import time light
    from mace.calculators.mace import MACECalculator

    calculator = MACECalculator(
        model_paths=model_local_path,
        device=device,
        default_dtype=default_dtype,
        enable_cueq=enable_cueq,
    )

    return ase_calculator(
        calculator=calculator,
        device=device,
        default_dtype=default_dtype,

        # --- Stage 1: MD / relaxation controls ---
        nvt_steps=nvt_steps,

        # --- Stage 2: relaxation controls ---
        fmax=fmax,
        steps_max=steps_max,
        hydrostatic_strain=hydrostatic_strain,
        constant_volume=constant_volume,
        optimizer=optimizer,

        # --- temperature schedules ---
        T=T,
        T_ramp=T_ramp,
        # --- timestep (fs) for the MD integrator ---
        md_timestep_fs=md_timestep_fs,
        # --- vibrational correction controls ---
        vib_correction      =   vib_correction,
        vib_store_interval  =   vib_store_interval,     # record every k MD steps -> effective dt = k * md_timestep_fs
        vib_min_samples     =   vib_min_samples,      # need at least this many stored samples to compute spectrum
        remove_com_drift    =   remove_com_drift,   # remove COM velocity before storing
        mass_weighted_com   =   mass_weighted_com,  # COM uses masses if True; else arithmetic mean
        vacf_window         =   vacf_window,

        # --- logging / IO performance knobs ---
        log_interval = log_interval,          # 0 disables printing; otherwise print every k steps
        write_interval = write_interval,        # trajectory write every k steps; set 0 to disable during MD

        # --- constraint controls ---
        constraint_logic=constraint_logic,
        constraint_action=constraint_action,
        freeze_components=freeze_components,
        constraints=constraints,

        # --- Stage 0: pre-MD relaxation controls ---
        pre_relax_fmax = pre_relax_fmax,
        pre_relax_steps_max = pre_relax_steps_max,
        pre_relax_optimizer = pre_relax_optimizer,
        pre_relax_constant_volume = pre_relax_constant_volume,
        pre_relax_hydrostatic_strain = pre_relax_hydrostatic_strain,
        pre_relax_with_constraints = pre_relax_with_constraints,

        # --- vibrational spectrum controls ---
        vib_spectrum=vib_spectrum,
        vib_spectrum_max_lag=vib_spectrum_max_lag,
        vib_spectrum_cutoff_cm1=vib_spectrum_cutoff_cm1,
        vib_spectrum_mode=vib_spectrum_mode,   # 'total' | 'atom' | 'element' | 'all'

    )

