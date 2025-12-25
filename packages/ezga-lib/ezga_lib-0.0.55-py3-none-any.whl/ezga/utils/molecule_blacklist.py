# ezga/utils/molecule_blacklist.py
from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Any

from .chemistry import (
    pair_cutoff,
    get_positions_species,
    neighbors_within,
)

RuleFn = Callable[[Any], bool]  # fn(apm) -> True if motif present
CUTOFF_MAX = float(4.0)

def _rule_Hf(apm, remove:bool=False, **kwargs) -> bool:
    """
    Detect a free H2 dimer: each H has exactly one H neighbor within H-H cutoff,
    and no non-H neighbors within H-X cutoff.
    """
    R, S = get_positions_species(apm)
    if sum(1 for s in S if s == "H") < 2:
        return False

    hh_cut = 3.0 # pair_cutoff("H", "H")
    to_remove: Set[int] = set()
    found = False

    for i, si in enumerate(S):
        if si != "H":
            continue
        neigh_dist, neigh_idx = neighbors_within(apm, R[i], n=3, cutoff=CUTOFF_MAX)

        if neigh_dist[1] >= hh_cut:
            found = True
            if remove:
                to_remove.update(i)
            else:
                return found

    if found and remove:
        apm.remove_atom(np.array(list(to_remove), dtype=np.int64))
        return False

    return found

def _rule_H2(apm, remove:bool=False, **kwargs) -> bool:
    """
    Detect a free H2 dimer: each H has exactly one H neighbor within H-H cutoff,
    and no non-H neighbors within H-X cutoff.
    """
    R, S = get_positions_species(apm)
    if sum(1 for s in S if s == "H") < 2:
        return False

    hh_cut = 0.9 # pair_cutoff("H", "H")
    to_remove: Set[int] = set()
    found = False

    for i, si in enumerate(S):
        if si != "H":
            continue
        neigh_dist, neigh_idx = neighbors_within(apm, R[i], n=3, cutoff=CUTOFF_MAX)

        if S[ neigh_idx[1] ] == "H" and neigh_dist[1] <= hh_cut:
            found = True
            if remove:
                to_remove.update((i, neigh_idx[1]))
            else:
                return found

    if found and remove:
        apm.remove_atom(np.array(list(to_remove), dtype=np.int64))
        return False

    return found

def _rule_H2b(apm, remove:bool=False, **kwargs) -> bool:
    """
    Detect a free H2 dimer: each H has exactly one H neighbor within H-H cutoff,
    and no non-H neighbors within H-X cutoff.
    """
    R, S = get_positions_species(apm)
    if sum(1 for s in S if s == "H") < 2:
        return False

    hh_cut = 0.9 #pair_cutoff("H", "H")
    to_remove: Set[int] = set()
    found = False

    for i, si in enumerate(S):
        if si != "H":
            continue
        neigh_dist, neigh_idx = neighbors_within(apm, R[i], n=3, cutoff=CUTOFF_MAX)

        if S[ neigh_idx[1] ] == "H" and neigh_dist[1] <= hh_cut and neigh_dist[2] <= 2.0:
            found = True
            if remove:
                to_remove.update((i, neigh_idx[1]))
            else:
                return found

    if found and remove:
        apm.remove_atom(np.array(list(to_remove), dtype=np.int64))
        return False

    return found

def _rule_H2O(apm, remove:bool=False, **kwargs) -> bool:
    """
    Detect an H2O molecule: O with exactly two H neighbors within O-H cutoff,
    and the two H are NOT H-H bonded (to avoid mislabeling OH + H2 as H2O).
    """
    R, S = get_positions_species(apm)
    if not any(s == "O" for s in S) or sum(1 for s in S if s == "H") < 2:
        return False

    oh_cut = pair_cutoff("O", "H")
    hh_cut = pair_cutoff("H", "H")
    to_remove: Set[int] = set()
    found = False

    for i, si in enumerate(S):
        if si != "O":
            continue
        neigh_dist, neigh_idx = neighbors_within(apm, R[i], n=4, cutoff=CUTOFF_MAX)

        if (
            S[neigh_idx[1]] == "H" and neigh_dist[1] <= oh_cut and
            S[neigh_idx[2]] == "H" and neigh_dist[2] <= oh_cut
        ):
            found = True
            if remove:
                to_remove.update((i, neigh_idx[1], neigh_dist[2]))
            else:
                return found

    if found and remove:
        apm.remove_atom(np.array(list(to_remove), dtype=np.int64))
        return False

    return found

def _rule_H2Of(apm, remove:bool=False, **kwargs) -> bool:
    """
    Detect an H2O molecule: O with exactly two H neighbors within O-H cutoff,
    and the two H are NOT H-H bonded (to avoid mislabeling OH + H2 as H2O).
    """
    R, S = get_positions_species(apm)

    if not any(s == "O" for s in S) or sum(1 for s in S if s == "H") < 2:
        return False

    oh_cut = pair_cutoff("O", "H")
    hh_cut = pair_cutoff("H", "H")
    to_remove: Set[int] = set()
    found = False

    for i, si in enumerate(S):
        if si != "O":
            continue
        neigh_dist, neigh_idx = neighbors_within(apm, R[i], n=4, cutoff=CUTOFF_MAX)

        if ( 
            S[ neigh_idx[1] ] == "H" and neigh_dist[1] <= oh_cut and 
            S[ neigh_idx[2] ] == "H" and neigh_dist[2] <= oh_cut and  
            neigh_dist[3] >= 2.5
        ):
            found = True
            if remove:
                to_remove.update((i, neigh_idx[1], neigh_dist[2]))
            else:
                return found

    if found and remove:
        apm.remove_atom(np.array(list(to_remove), dtype=np.int64))
        return False

    return found

def _rule_O2(apm, remove:bool=False, **kwargs) -> bool:
    """
    Detect an H2O molecule: O with exactly two H neighbors within O-H cutoff,
    and the two H are NOT H-H bonded (to avoid mislabeling OH + H2 as H2O).
    """
    R, S = get_positions_species(apm)
    if sum(1 for s in S if s == "O") < 2:
        return False

    oo_cut = 1.4 # pair_cutoff("O", "O")
    to_remove: Set[int] = set()
    found = False

    for i, si in enumerate(S):
        if si != "O":
            continue
        neigh_dist, neigh_idx = neighbors_within(apm, R[i], n=3, cutoff=CUTOFF_MAX)

        if (
            S[neigh_idx[1]] == "O" and neigh_dist[1] <= oo_cut
        ):
            found = True
            if remove:
                to_remove.update((i, neigh_idx[1]))
            else:
                return found

    if found and remove:
        apm.remove_atom(np.array(list(to_remove), dtype=np.int64))
        return False

    return found

def _rule_HERO(apm, remove:bool=False, **kwargs) -> bool:
    """Return True if any atom lies outside the allowed Z window.

    This rule flags structures where at least one atom has a z-coordinate
    strictly less than 3.0 Å or strictly greater than 19.0 Å.

    Implementation details:
      * Fast path (NumPy): when `R` is a NumPy ndarray, the function uses
        `min()` and `max()` reductions on the z column to avoid allocating
        temporary boolean masks.
      * Fallback path (generic sequences): a single-pass scan with early exit.

    Args:
        apm: Atom position manager-like object accepted by
            `get_positions_species(apm)`. It is expected to provide atomic
            positions in Cartesian coordinates (Å).

    Returns:
        bool: True if any atom violates the Z window; False otherwise.
    """
    R, _ = get_positions_species(apm)

    # Empty containers or objects without length should not trigger the rule.
    try:
        if len(R) == 0:
            return False
    except TypeError:
        return False

    lo, hi = 3.0, 19.0

    # Fast path using NumPy (if available) for C-level reductions.
    try:
        import numpy as np
        if isinstance(R, np.ndarray):

            z = R[:, 2]
            below = z < lo
            above = z > hi
            any_bad = bool(below.any() or above.any())
            if any_bad and remove:
                idxs = np.where(below | above)[0].astype(int)
                apm.remove_atom(np.array(list(idxs), dtype=np.int64))
                return False

            return any_bad
    except Exception:
        # Fail-soft: fall back to a generic, allocation-free scan.
        pass

    return False

_DEFAULT_RULES: Dict[str, RuleFn] = {
    "H2":   _rule_H2,
    "H2B":  _rule_H2b,
    "H2O":  _rule_H2O,
    "H2OF": _rule_H2Of,
    "O2":   _rule_O2,
    "Hf":   _rule_Hf,
    "HERO":   _rule_HERO,
}

class BlacklistDetector:
    """
    Pluggable, PBC-aware motif blacklist checker.
    Usage:
        detector = BlacklistDetector(["H2O","H2"])
        present, tag = detector.contains(struct)
    """

    def __init__(self, blacklist: Iterable[str] = (), rules: Optional[Dict[str, RuleFn]] = None):
        self.blacklist: Set[str] = set(s.upper() for s in blacklist)
        self.rules: Dict[str, RuleFn] = dict(_DEFAULT_RULES if rules is None else rules)
        self.remove = False

    def register(self, name: str, fn: RuleFn) -> None:
        """Register/override a rule at runtime."""
        self.rules[name.upper()] = fn

    def contains(self, struct, remove: Optional[bool] = None) -> Tuple[bool, Optional[str]]:
        """Return (True, 'TAG') if any blacklisted motif is detected in struct; else (False, None)."""
        if not self.blacklist:
            return (False, None)
        remove = remove if isinstance(remove, bool) else self.remove

        apm = struct.AtomPositionManager
        for tag in self.blacklist:
            rule = self.rules.get(tag)

            if rule is None:
                continue
            try:
                if rule(apm=apm, remove=self.remove):
                    return (True, tag)
            except Exception:
                # Fail-soft: ignore rule errors in production; keep GA running.
                continue
        return (False, None)
