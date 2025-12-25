# ezga/utils/chemistry.py
from __future__ import annotations

from math import gcd, isfinite
from functools import reduce
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

# Minimal covalent radii set; extend as needed for your systems.
RCOV: Dict[str, float] = {
    'H' :  .31, 'He':  .28, 'Li': 1.28, 'Be':  .96, 'B' :  .84, 'C' :  .76, 'N' :  .71, 'O' :  .66, 'F': .57,
    'Ne':  .58, 'Na': 1.66, 'Mg': 1.41, 'Al': 1.21, 'Si': 1.11, 'P' : 1.07, 'S' : 1.05, 'Cl': 1.02,
    'Ar': 1.06, 'K' : 1.03, 'Ca': 1.76, 'Sc': 1.70, 'Ti': 1.60, 'V' : 1.53, 'Cr': 1.39, 'Mn': 1.39,
    'Fe': 1.32, 'Co': 1.26, 'Ni': 1.24, 'Cu': 1.32, 'Zn': 1.22, 'Ga': 1.22, 'Ge': 1.20, 'As': 1.19,
    'Se': 1.20, 'Br': 1.20, 'Kr': 1.16, 'Rb': 2.20, 'Sr': 1.95, 'Y' : 1.90, 'Zr': 1.75, 'Nb': 1.64,
    'Mo': 1.54, 'Tc': 1.47, 'Ru': 1.46, 'Rh': 1.42, 'Pd': 1.39, 'Ag': 1.45, 'Cd': 1.44, 'In': 1.42,
    'Sn': 1.39, 'Sb': 1.39, 'Te': 1.38, 'I' : 1.39, 'Xe': 1.40, 'Cs': 2.44, 'Ba': 2.15, 'La': 2.07,
    'Ce': 2.04, 'Pr': 2.03, 'Nd': 2.01, 'Pm': 1.99, 'Sm': 1.98, 'Eu': 1.98, 'Gd': 1.96, 'Tb': 1.94,
    'Dy': 1.92, 'Ho': 1.92, 'Er': 1.89, 'Tm': 1.90, 'Yb': 1.87, 'Lu': 1.87, 'Hf': 1.75, 'Ta': 1.70,
    'W' : 1.62, 'Re': 1.51, 'Os': 1.44, 'Ir': 1.41, 'Pt': 1.36, 'Au': 1.36, 'Hg': 1.32, 'Tl': 1.45,
    'Pb': 1.46, 'Bi': 1.48, 'Th': 1.79, 'Pa': 1.63, 'U' : 1.56, 'Np': 1.55, 'Pu': 1.53, 'Am': 1.51,
    'Cm': 1.50, 'Bk': 1.50, 'Cf': 1.50, 'Es': 1.50, 'Fm': 1.50, 'Md': 1.50, 'No': 1.50, 'Lr': 1.50,
    'Rf': 1.50, 'Db': 1.50, 'Sg': 1.50, 'Bh': 1.50, 'Hs': 1.50, 'Mt': 1.50, 'Ds': 1.50, 'Rg': 1.50,
    'Cn': 1.50, 'Nh': 1.50, 'Fl': 1.50, 'Mc': 1.50, 'Lv': 1.50, 'Ts': 1.50, 'Og': 1.50
}

AMASS: Dict[str, float]=  {
    'H': 1.00794, 'He': 4.002602, 'Li': 6.941, 'Be': 9.0122, 'B': 10.81, 'C': 12.01, 'N': 14.007, 'O': 15.999, 'F': 18.998403163,
    'Ne': 20.1797, 'Na': 22.98976928, 'Mg': 24.305, 'Al': 26.9815386, 'Si': 28.085, 'P': 30.973761998, 'S': 32.06, 'Cl': 35.45,
    'Ar': 39.948, 'K': 39.0983, 'Ca': 40.078, 'Sc': 44.955908, 'Ti': 47.867, 'V': 50.9415, 'Cr': 51.9961, 'Mn': 54.938044,
    'Fe': 55.845, 'Co': 58.933194, 'Ni': 58.6934, 'Cu': 63.546, 'Zn': 65.38, 'Ga': 69.723, 'Ge': 72.63, 'As': 74.921595,
    'Se': 78.971, 'Br': 79.904, 'Kr': 83.798, 'Rb': 85.4678, 'Sr': 87.62, 'Y': 88.90584, 'Zr': 91.224, 'Nb': 92.90637,
    'Mo': 95.95, 'Tc': 98.0, 'Ru': 101.07, 'Rh': 102.9055, 'Pd': 106.42, 'Ag': 107.8682, 'Cd': 112.414, 'In': 114.818,
    'Sn': 118.71, 'Sb': 121.76, 'Te': 127.6, 'I': 126.90447, 'Xe': 131.293, 'Cs': 132.90545196, 'Ba': 137.327, 'La': 138.90547,
    'Ce': 140.116, 'Pr': 140.90766, 'Nd': 144.242, 'Pm': 145.0, 'Sm': 150.36, 'Eu': 151.964, 'Gd': 157.25, 'Tb': 158.92535,
    'Dy': 162.5, 'Ho': 164.93033, 'Er': 167.259, 'Tm': 168.93422, 'Yb': 173.04, 'Lu': 174.9668, 'Hf': 178.49, 'Ta': 180.94788,
    'W': 183.84, 'Re': 186.207, 'Os': 190.23, 'Ir': 192.217, 'Pt': 195.084, 'Au': 196.966569, 'Hg': 200.592, 'Tl': 204.38,
    'Pb': 207.2, 'Bi': 208.98040, 'Th': 232.03805, 'Pa': 231.03588, 'U': 238.05078, 'Np': 237.0, 'Pu': 244.0, 'Am': 243.0,
    'Cm': 247.0, 'Bk': 247.0, 'Cf': 251.0, 'Es': 252.0, 'Fm': 257.0, 'Md': 258.0, 'No': 259.0, 'Lr': 262.0, 'Rf': 267.0,
    'Db': 270.0, 'Sg': 271.0, 'Bh': 270.0, 'Hs': 277.0, 'Mt': 276.0, 'Ds': 281.0, 'Rg': 280.0, 'Cn': 285.0, 'Nh': 284.0,
    'Fl': 289.0, 'Mc': 288.0, 'Lv': 293.0, 'Ts': 294.0, 'Og': 294.0
}

DEFAULT_BOND_SCALE: float = 1.30  # Typical 1.15–1.25


def pair_cutoff(a: str, b: str, *, scale: float = DEFAULT_BOND_SCALE,
                rcov: Mapping[str, float] = RCOV) -> float:
    """
    Covalent-bond distance cutoff (Å) for a given pair (a, b).
    Falls back to 1.0 Å when element is missing (conservative but safe).
    """
    ra = rcov.get(a, 1.0)
    rb = rcov.get(b, 1.0)
    return scale * (ra + rb)


def get_positions_species(apm) -> Tuple[Sequence, Sequence[str]]:
    """
    Robustly obtain positions and species/symbols from an AtomPositionManager-like object.
    Supports .get_positions()/.r and .get_species()/.symbols/.species.
    """
    if hasattr(apm, "atomPositions"):
        R = apm.atomPositions
    elif hasattr(apm, "r"):
        R = apm.r
    else:
        raise AttributeError("APM must expose positions via get_positions() or .r")

    if hasattr(apm, "atomLabelsList"):
        S = apm.atomLabelsList
    elif hasattr(apm, "symbols"):
        S = apm.symbols
    elif hasattr(apm, "species"):
        S = apm.species
    else:
        S = getattr(getattr(apm, "metadata", {}), "get", lambda _k, _d=None: None)("symbols")
    if S is None:
        raise AttributeError("APM must expose species via get_species()/symbols/species")

    return R, S


def neighbors_within(apm, r_i, n: int, cutoff: float) -> List[Tuple[int, float]]:
    """
    Normalizes APM.find_n_closest_neighbors(..) to a list[(index, distance)] within 'cutoff'.
    Handles both keyworded and positional call signatures.
    """
    try:
        return apm.find_n_closest_neighbors(
            r=r_i, n=n, kdtree=True, eps=0, p=2, distance_upper_bound=cutoff
        )

    except Exception as ex:
        # Fail-soft: proceed with other checks; optionally log when debug
        print(f"[neighbors_within] blacklist check error: {ex}")

def reduced_composition(counts: Mapping[str, int]) -> Dict[str, int]:
    """
    Reduce an elemental composition by the GCD of counts (e.g., {C:6,H:6,O:12} -> {C:1,H:1,O:2}).
    Non-negative integers are enforced via int() cast.
    """
    elems = [e for e in counts if int(counts[e]) > 0]
    if not elems:
        return {}
    values = [max(0, int(counts[e])) for e in elems]
    g = reduce(gcd, values) if values else 1
    g = g or 1
    return {e: (int(counts[e]) // g) for e in sorted(elems)}


def composition_key(counts: Mapping[str, int]) -> str:
    """
    Canonical key like 'C1-H1-N1-O2' (always include 1).
    """
    rc = reduced_composition(counts)
    return "-".join(f"{el}{rc[el]}" for el in sorted(rc))
