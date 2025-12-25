import numpy as np
import copy
from typing import Callable, Dict, List, Optional, Tuple, Literal

# Assumes your PeriodicCKDTree is available in scope
# from your_module import PeriodicCKDTree

FieldName = Literal["fourier", "planes", "gaussians"]

# ----------------------------
# Lattice helpers (rows/cols)
# ----------------------------
# from sage_lib.partition.Partition import Partition
# from your_code.utils import get_element_counts, ...
def validate(idx, structure, constraints:list, logic:str = "all") -> bool:
    """
    Checks whether the provided feature vector satisfies
    the constraints according to the specified logic.
    
    Returns
    -------
    bool
        True if constraints pass, False otherwise.
    """

    def _as_bool(x) -> bool:
        # Accept Python bool, numpy.bool_, 0-D arrays, or vectors
        if isinstance(x, (bool, np.bool_)):
            return bool(x)
        a = np.asarray(x)
        if a.shape == ():        # numpy scalar
            return bool(a.item())
        return bool(np.all(a))   # vectors: require all components True

    if not constraints:
        return True
    vals = (_as_bool(constraint(idx, structure)) for constraint in constraints)

    if logic == "all":
        return all(vals)
    elif logic == "any":
        return any(vals)
        
    return False

# ----------------------------
# Probability field builders
# ----------------------------

def _grid_fractional_nd(N: int, dim: int) -> np.ndarray:
    lin = np.linspace(0.0, 1.0, N, endpoint=False)
    if dim == 2:
        U, V = np.meshgrid(lin, lin, indexing="ij")
        return np.stack([U, V], axis=-1)
    else:
        U, V, W = np.meshgrid(lin, lin, lin, indexing="ij")
        return np.stack([U, V, W], axis=-1)

def _frac_to_cart_nd(frac_points: np.ndarray, L: np.ndarray) -> np.ndarray:
    return np.tensordot(frac_points, L.T, axes=1)

def _wrap_min_image_nd(d: np.ndarray) -> np.ndarray:
    return (d + 0.5) % 1.0 - 0.5

def _periodic_grad_u_nd(f: np.ndarray, dim: int) -> List[np.ndarray]:
    N = f.shape[0]
    du = 1.0 / N
    grads = []
    for ax in range(dim):
        g = (np.roll(f, -1, axis=ax) - np.roll(f, 1, axis=ax)) / (2 * du)
        grads.append(g)
    return grads

def _grad_cart_from_grad_u_nd(dfu: List[np.ndarray], L: np.ndarray) -> List[np.ndarray]:
    LinvT = np.linalg.inv(L).T
    g_cart = []
    for i in range(LinvT.shape[0]):
        acc = 0.0
        for j in range(LinvT.shape[1]):
            acc = acc + LinvT[i, j] * dfu[j]
        g_cart.append(acc)
    return g_cart

def _grad_norm_nd(g_cart: List[np.ndarray]) -> np.ndarray:
    s = np.zeros_like(g_cart[0])
    for g in g_cart:
        s = s + g*g
    return np.sqrt(s) + 1e-12

def _smooth_indicator(levelset: np.ndarray, soft_width: float) -> np.ndarray:
    w = max(1e-12, float(soft_width))
    x = np.clip(levelset / w, -50.0, 50.0)
    return 1.0 / (1.0 + np.exp(x))

def _random_fourier_field_nd(u: np.ndarray, dim: int, seed: int, Kmax: int, n_modes: int, decay: float) -> np.ndarray:
    rng = np.random.default_rng(seed)
    N = u.shape[0]
    f = np.zeros([N]*dim, dtype=float)
    ranges = [range(-Kmax, Kmax+1) for _ in range(dim)]
    ks = [np.array(k, float) for k in __import__("itertools").product(*ranges) if any(ki != 0 for ki in k)]
    idx = rng.choice(len(ks), size=n_modes, replace=True)
    if dim == 2:
        u0, u1 = u[...,0], u[...,1]
        for j in idx:
            k = ks[j]
            k_norm = np.linalg.norm(k)
            amp = rng.normal(0.0, 1.0) / (k_norm**decay if k_norm>0 else 1.0)
            phi = rng.uniform(0.0, 2*np.pi)
            phase = 2*np.pi*(k[0]*u0 + k[1]*u1) + phi
            f += amp * np.cos(phase)
    else:
        u0, u1, u2 = u[...,0], u[...,1], u[...,2]
        for j in idx:
            k = ks[j]
            k_norm = np.linalg.norm(k)
            amp = rng.normal(0.0, 1.0) / (k_norm**decay if k_norm>0 else 1.0)
            phi = rng.uniform(0.0, 2*np.pi)
            phase = 2*np.pi*(k[0]*u0 + k[1]*u1 + k[2]*u2) + phi
            f += amp * np.cos(phase)
    f -= f.mean()
    f /= (f.std() + 1e-12)
    return f

def _random_planes_levelset_nd(r: np.ndarray, dim: int, seed: int, n_planes: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vals = []
    shape = r.shape[:-1]
    for _ in range(n_planes):
        n = rng.normal(size=dim)
        n = n / (np.linalg.norm(n) + 1e-12)
        idx = tuple(rng.integers(0, shape[i]) for i in range(dim))
        r0 = r[idx]
        if dim == 2:
            vals.append(n[0]*(r[...,0]-r0[0]) + n[1]*(r[...,1]-r0[1]))
        else:
            vals.append(n[0]*(r[...,0]-r0[0]) + n[1]*(r[...,1]-r0[1]) + n[2]*(r[...,2]-r0[2]))
    f = np.maximum.reduce(vals)
    f -= np.median(f)
    return f

def _random_gaussian_field_nd(u: np.ndarray, L: np.ndarray, dim: int, seed: int, n_centers: int, sigma_range: Tuple[float,float]) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centers = rng.random((n_centers, dim))
    sigmas = rng.uniform(sigma_range[0], sigma_range[1], size=n_centers)
    r = _frac_to_cart_nd(u, L)
    g = np.zeros(r.shape[:-1], dtype=float)
    for c, s in zip(centers, sigmas):
        du = _wrap_min_image_nd(u - c)
        dr = _frac_to_cart_nd(du, L)
        d2 = np.sum(dr*dr, axis=-1)
        g += np.exp(-0.5 * d2 / (s*s))
    g /= (g.max() + 1e-12)
    return g

def _sdl_from_field_nd(f_scalar: np.ndarray, L: np.ndarray, dim: int, level: float) -> np.ndarray:
    dfu = _periodic_grad_u_nd(f_scalar, dim)
    g_cart = _grad_cart_from_grad_u_nd(dfu, L)
    gnorm = _grad_norm_nd(g_cart)
    return (f_scalar - level) / gnorm

def _make_sampler_from_grid(vol_grid: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    vol = np.asarray(vol_grid, float)
    N = vol.shape[0]
    dim = vol.ndim
    if dim == 2:
        def sample(u: np.ndarray) -> np.ndarray:
            U = np.asarray(u, float)
            S = U * N
            i0 = np.floor(S).astype(int) % N
            t = S - i0
            i1 = (i0 + 1) % N
            ix0, iy0 = i0[...,0], i0[...,1]
            ix1, iy1 = i1[...,0], i1[...,1]
            tx, ty = t[...,0], t[...,1]
            v00 = vol[ix0, iy0]; v10 = vol[ix1, iy0]
            v01 = vol[ix0, iy1]; v11 = vol[ix1, iy1]
            return (1-tx)*(1-ty)*v00 + tx*(1-ty)*v10 + (1-tx)*ty*v01 + tx*ty*v11
        return sample
    else:
        def sample(u: np.ndarray) -> np.ndarray:
            U = np.asarray(u, float)
            S = U * N
            i0 = np.floor(S).astype(int) % N
            t = S - i0
            i1 = (i0 + 1) % N
            ix0, iy0, iz0 = i0[...,0], i0[...,1], i0[...,2]
            ix1, iy1, iz1 = i1[...,0], i1[...,1], i1[...,2]
            tx, ty, tz = t[...,0], t[...,1], t[...,2]
            v000 = vol[ix0, iy0, iz0]; v100 = vol[ix1, iy0, iz0]
            v010 = vol[ix0, iy1, iz0]; v110 = vol[ix1, iy1, iz0]
            v001 = vol[ix0, iy0, iz1]; v101 = vol[ix1, iy0, iz1]
            v011 = vol[ix0, iy1, iz1]; v111 = vol[ix1, iy1, iz1]
            c00 = (1-tx)*v000 + tx*v100
            c10 = (1-tx)*v010 + tx*v110
            c01 = (1-tx)*v001 + tx*v101
            c11 = (1-tx)*v011 + tx*v111
            c0 = (1-ty)*c00 + ty*c10
            c1 = (1-ty)*c01 + ty*c11
            return (1-tz)*c0 + tz*c1
        return sample

def _build_sampler_from_name(
    field: FieldName, *,
    L: np.ndarray,
    seed: int,
    soft_width: float,
    target_vol_frac: float,
    N2: int, N3: int,
    # Fourier
    fourier_Kmax_2d: int, fourier_modes_2d: int,
    fourier_Kmax_3d: int, fourier_modes_3d: int,
    fourier_decay: float,
    # Planes
    planes_n_2d: int, planes_n_3d: int,
    # Gaussians
    gauss_n_2d: int, gauss_n_3d: int,
    gauss_sigma_range_2d: Tuple[float,float],
    gauss_sigma_range_3d: Tuple[float,float],
) -> Callable[[np.ndarray], np.ndarray]:
    dim = L.shape[0]
    N = N2 if dim == 2 else N3
    u = _grid_fractional_nd(N, dim)
    r = _frac_to_cart_nd(u, L)

    if field == "fourier":
        f = _random_fourier_field_nd(
            u, dim, seed=seed,
            Kmax=fourier_Kmax_2d if dim==2 else fourier_Kmax_3d,
            n_modes=fourier_modes_2d if dim==2 else fourier_modes_3d,
            decay=fourier_decay
        )
        thr = np.quantile(f, 1.0 - target_vol_frac)
        sdl = _sdl_from_field_nd(f, L, dim, thr)
        vol = _smooth_indicator(sdl, soft_width)
    elif field == "planes":
        f = _random_planes_levelset_nd(
            r, dim, seed=seed,
            n_planes=planes_n_2d if dim==2 else planes_n_3d
        )
        thr = np.quantile(f, 1.0 - target_vol_frac)
        sdl = _sdl_from_field_nd(f, L, dim, thr)
        vol = _smooth_indicator(sdl, soft_width)
    elif field == "gaussians":
        g = _random_gaussian_field_nd(
            u, L, dim, seed=seed,
            n_centers=gauss_n_2d if dim==2 else gauss_n_3d,
            sigma_range=gauss_sigma_range_2d if dim==2 else gauss_sigma_range_3d
        )
        thr = np.quantile(g, target_vol_frac)
        f = thr - g
        sdl = _sdl_from_field_nd(f, L, dim, 0.0)
        vol = _smooth_indicator(sdl, soft_width)
    else:
        raise ValueError(f"Unknown field name: {field}")

    return _make_sampler_from_grid(vol),  f, thr

# ----------------------------
# Collision policy & relax
# ----------------------------
def atoms_near_interface_cartesian(
    struct,
    f_scalar: np.ndarray,
    L: np.ndarray,
    cols: list[int],
    level: float,
    delta: float
):
    """
    Returns mask + distances for atoms within ±delta Å
    from the interphase defined by scalar field f_scalar.
    """
    dim = len(cols)
    # 1) Build SDL field (signed distance in Å)
    sdl_grid = _sdl_from_field_nd(f_scalar, L[np.ix_(cols, cols)], dim, level)
    # 2) Interpolator to evaluate SDL at arbitrary fractional coords
    sdl_sampler = _make_sampler_from_grid(sdl_grid)
    # 3) Atom fractional coords
    u_full = np.asarray(struct.AtomPositionManager.atomPositions_fractional, float)
    u_sub  = u_full[:, cols]
    # 4) Distances in Å
    dvals = sdl_sampler(u_sub)
    # 5) Band selection
    mask = np.abs(dvals) < delta
    return mask, dvals

def resolve_collisions(
    struct,
    mask: np.ndarray,
    p: float = 2.0,
    factor: float = 0.6,
    eps: float = 0.0,
    seed: int = None
) -> bool:
    """
    Detect collisions among masked atoms and remove half of the atoms
    involved in collisions (chosen randomly in one batch).
    
    Collision: d_ij < factor * (R_i + R_j).
    
    Parameters
    ----------
    struct : object
        Structure with AtomPositionManager (apm).
    mask : np.ndarray[bool]
        Boolean array selecting which atoms to check.
    p : float
        Minkowski p-norm for KDTree.
    factor : float
        Scaling factor for covalent radii.
    eps : float
        KDTree query approximation parameter.
    seed : int, optional
        Random seed for reproducibility.
    
    Returns
    -------
    removed : bool
        True if atoms were removed, False otherwise.
    """
    rng = np.random.default_rng(seed)
    apm = struct.AtomPositionManager

    if apm.atomCount == 0:
        return False

    radii = np.asarray([apm.covalent_radii[label] for label in apm.atomLabelsList], dtype=float)
    if radii.size == 0:
        return False

    pos = np.asarray(apm.atomPositions, dtype=float)
    N = pos.shape[0]
    rmax = float(np.max(radii))
    if not np.isfinite(rmax) or rmax <= 0.0:
        return False

    periodic = getattr(apm, "_latticeVectors", None) is not None
    indices = np.nonzero(mask)[0]

    colliding_pairs = []

    # Collect all pairs
    for i in indices:
        Ri = radii[i]
        r_local = factor * (Ri + rmax)

        nbrs = apm.kdtree.query_ball_point(pos[i], r=r_local, p=p, eps=eps)
        nbrs = nbrs[nbrs!=i]
        
        if len(nbrs) <= 0:
            continue

        Q = pos[nbrs]
        if periodic:
            P = np.repeat(pos[i][None, :], len(nbrs), axis=0)
            d = apm.distance_many(P, Q)
        else:
            d = np.linalg.norm(Q - pos[i], axis=1)


        thr = factor * (Ri + radii[nbrs])
        hits = np.where(d < thr)[0]
        for k in hits:
            colliding_pairs.append((i, nbrs[k]))

    if len(colliding_pairs) == 0:
        return False  # no collisions found

    # for each pair, randomly remove one atom
    atoms_to_remove = []
    for i, j in colliding_pairs:
        atoms_to_remove.append(rng.choice([i, j]))

    atoms_to_remove = np.unique(atoms_to_remove)  # deduplicate in case of overlap
    struct.AtomPositionManager.remove_atom(atoms_to_remove)
    # force rebuild kdtree
    struct.AtomPositionManager._kdtree = None
    
    return True



# ----------------------------
# Core crossover assembly
# ----------------------------
def crossover_split(
    structA, structB,
    maskA: np.ndarray, maskB: np.ndarray,
    maskA_constraints: np.ndarray = None,
    maskB_constraints: np.ndarray = None,
):
    """
    In-place crossover that preserves the original objects:
      - structA becomes child_true  = A[maskA==True]  (+ constrained A) + movable B[maskB==False]
      - structB becomes child_false = B[maskB==True]  (+ constrained B) + movable A[maskA==False]

    Notes
    -----
    - Only *movable* atoms are removed/added. Constrained atoms (mask*_constraints == True)
      are kept in their original parent and are never transferred.
    - Indices in masks refer to the *original* ordering before any removal.

    Parameters
    ----------
    structA, structB : objects with
        - AtomPositionManager.atomPositions (N,3)
        - AtomPositionManager.atomLabelsList (N,)
        - methods: remove_atom(atom_index: np.array) and add_atom(atomLabels: str, atomPosition: np.array)
    maskA, maskB : bool arrays
        Selection masks for A and B.
    maskA_constraints, maskB_constraints : bool arrays or None
        True -> constrained (NOT movable), False -> movable. If None, all atoms are considered movable.
    """
    structA = copy.deepcopy(structA)
    structB = copy.deepcopy(structB)

    # --- grab originals once (before any mutation) ---
    posA = np.asarray(structA.AtomPositionManager.atomPositions, float)
    labA = np.asarray(structA.AtomPositionManager.atomLabelsList, object)
    posB = np.asarray(structB.AtomPositionManager.atomPositions, float)
    labB = np.asarray(structB.AtomPositionManager.atomLabelsList, object)

    # --- basic validation ---
    for name, m, labels in (("A", maskA, labA), ("B", maskB, labB)):
        if m.dtype != bool:
            raise ValueError(f"mask{name} must be boolean.")
        if m.shape[0] != labels.shape[0]:
            raise ValueError(f"mask{name} length mismatch: {m.shape[0]} vs {labels.shape[0]}")

    if maskA_constraints is None:
        maskA_constraints = np.zeros_like(maskA, dtype=bool)   # no constraints by default
    if maskB_constraints is None:
        maskB_constraints = np.zeros_like(maskB, dtype=bool)

    if maskA_constraints.shape != maskA.shape or maskB_constraints.shape != maskB.shape:
        raise ValueError("Constraint mask shapes must match their corresponding selection masks.")

    # Movable = NOT constrained
    movableA = ~maskA_constraints.astype(bool)
    movableB = ~maskB_constraints.astype(bool)

    # --- indices to remove in-place (remove only movable atoms that are not selected to remain) ---
    # child_true (structA): keep A[maskA==True] and ALL constrained A; remove A[~maskA & movable]
    remove_from_A_for_true = np.where((~maskA) & movableA)[0]
    # child_false (structB): keep B[maskB==True] and ALL constrained B; remove B[~maskB & movable]
    remove_from_B_for_false = np.where((~maskB) & movableB)[0]

    # --- atoms to import (only movable atoms are transferred) ---
    # Into child_true (A): add movable B[~maskB]
    add_from_B_for_true_idx = np.where((~maskB) & movableB)[0]
    add_from_B_for_true_pos = posB[add_from_B_for_true_idx]
    add_from_B_for_true_lab = labB[add_from_B_for_true_idx]

    # Into child_false (B): add movable A[~maskA]
    add_from_A_for_false_idx = np.where((~maskA) & movableA)[0]
    add_from_A_for_false_pos = posA[add_from_A_for_false_idx]
    add_from_A_for_false_lab = labA[add_from_A_for_false_idx]

    # --- mutate structA -> child_true ---
    structA.AtomPositionManager.remove_atom(remove_from_A_for_true)
    structA.AtomPositionManager.add_atom(atomLabels=add_from_B_for_true_lab, atomPosition=add_from_B_for_true_pos)

    # --- mutate structB -> child_false ---
    structB.AtomPositionManager.remove_atom(remove_from_B_for_false)
    structB.AtomPositionManager.add_atom(atomLabels=add_from_A_for_false_lab, atomPosition=add_from_A_for_false_pos)

    # Return the (now mutated) originals for convenience
    return structA, structB


# ----------------------------
# Public factory
# ----------------------------

def crossover_field_stitch(
    *,
    field: FieldName,
    # Grid & field hyperparameters (built INSIDE when called)
    N2: int = 256,
    N3: int = 96,
    soft_width: float = 0.06,
    target_vol_frac: float = 0.2,

    # Fourier params
    fourier_Kmax_2d: int = 1,  fourier_modes_2d: int = 11,
    fourier_Kmax_3d: int = 4,  fourier_modes_3d: int = 220,
    fourier_decay: float = 1.8,
    # Planes params
    planes_n_2d: int = 100, planes_n_3d: int = 7,
    # Gaussians params
    gauss_n_2d: int = 2, gauss_n_3d: int = 14,
    gauss_sigma_range_2d: Tuple[float,float] = (1.18, 1.45),
    gauss_sigma_range_3d: Tuple[float,float] = (0.25, 0.55),

    seed: Optional[int] = None,

    # Collision/relax
    interphase_window:float = 2.0,
    factor:float = 0.8,

    active_axes:list = ['x','y','z'],
    constraints: list = None,
):
    """
    Returns f(A,B)->(childA, childB). The probability sampler p(u) is generated
    INSIDE this function from `field` and hyperparameters (no external sampler).
    Cell L is obtained from the structures. Covalent radii are taken from
    structureA.AtomPositionManager.covalent_radii.
    """
    rng = np.random.default_rng(seed)

    def _build_sampler(L: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
        sub_seed = int(rng.integers(0, 2**31-1))

        return _build_sampler_from_name(
            field,
            L=L,
            seed=sub_seed,
            soft_width=soft_width,
            target_vol_frac=target_vol_frac,
            N2=N2, N3=N3,
            fourier_Kmax_2d=fourier_Kmax_2d, fourier_modes_2d=fourier_modes_2d,
            fourier_Kmax_3d=fourier_Kmax_3d, fourier_modes_3d=fourier_modes_3d,
            fourier_decay=fourier_decay,
            planes_n_2d=planes_n_2d, planes_n_3d=planes_n_3d,
            gauss_n_2d=gauss_n_2d, gauss_n_3d=gauss_n_3d,
            gauss_sigma_range_2d=gauss_sigma_range_2d,
            gauss_sigma_range_3d=gauss_sigma_range_3d,
        )

    # Map column labels to indices
    label_to_index = {"x":0, "y":1, "z":2}
    # Convert labels to indices
    cols = [label_to_index[c.strip()] for c in (active_axes.split() if isinstance(active_axes, str) else active_axes) ]

    def _xover(structA, structB):
        """
        """
        L_A = np.asarray(structA.AtomPositionManager.latticeVectors, float)
        L_B = np.asarray(structB.AtomPositionManager.latticeVectors, float)

        if not np.allclose(L_A, L_B, atol=1e-8):
            #raise ValueError("Parent cells differ. Provide parents with identical cells.")
            pass
        L = L_A[np.ix_(cols, cols)]
        dim = L.shape[0]

        # 2) Covalent radii from structureA (per requirement)
        radii = getattr(structA.AtomPositionManager, "covalent_radii", None)

        # 3) Build probability sampler p(u) internally from `field` + hyperparams
        sampler, f, thr = _build_sampler(L,)

        N_atoms_A = structA.AtomPositionManager.atomCount
        N_atoms_B = structB.AtomPositionManager.atomCount
        N_atoms   = N_atoms_A + N_atoms_B

        uA_full = np.asarray(structA.AtomPositionManager.atomPositions_fractional, float)
        uB_full = np.asarray(structB.AtomPositionManager.atomPositions_fractional, float)
        uA_sub = uA_full[:, cols]
        uB_sub = uB_full[:, cols]

        u_atoms = np.vstack([
            structA.AtomPositionManager.atomPositions_fractional,
            structB.AtomPositionManager.atomPositions_fractional
        ])  # shape (N, dim)

        probs = np.concatenate([sampler(uA_sub), sampler(uB_sub)])            # shape (N,)
        rnd   = rng.random(N_atoms)         # one rnd per atom
        mask  = rnd > probs                 # global mask

        # Split into A and B parts
        maskA = mask[:N_atoms_A]
        maskB = mask[N_atoms_A:]

        if isinstance(constraints, list) and len(constraints) > 0:
            maskA_constraints = np.fromiter((validate(i, structA, constraints) for i in range(N_atoms_A)), dtype=bool, count=N_atoms_A)
            maskB_constraints = np.fromiter((validate(i, structB, constraints) for i in range(N_atoms_B)), dtype=bool, count=N_atoms_B)


        '''
        # === Publication-grade domain segmentation plot ==========================
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap

        # Extract fractional coordinates of parent A
        uA_full = np.asarray(structA.AtomPositionManager.atomPositions_fractional, float)
        uA = uA_full[:, cols]
        x, y = uA[:, 0], uA[:, 1]

        # Build smooth scientific colormap
        cmap = LinearSegmentedColormap.from_list(
            "fieldmap",
            ["#08306b", "#2171b5", "#6baed6", "#bdd7e7",
             "#fdd0a2", "#fdae6b", "#e6550d", "#a63603"],
            N=256
        )

        fig, ax = plt.subplots(figsize=(6.2, 5.4), dpi=300)

        # Background: scalar field (transposed for plotting)
        ax.imshow(
            f.T,
            origin="lower",
            cmap=cmap,
            extent=[0, 1, 0, 1],
            interpolation="bicubic"
        )

        # Domain boundary: level-set contour at thr
        cs = ax.contour(
            f.T,
            levels=[thr],
            colors="black",
            linewidths=1.0,
            extent=[0, 1, 0, 1]
        )
        cs.collections[0].set_label("Level-set boundary")

        # Domain A (maskA=True)
        ax.scatter(
            x[maskA], y[maskA],
            c="#ffd92f",
            #edgecolor="black",
            s=.1,
            label="Domain A (maskA=True)"
        )

        # Domain B (maskA=False)
        ax.scatter(
            x[~maskA], y[~maskA],
            c="white",
            #edgecolor="black",
            s=.1,
            label="Domain B (maskA=False)"
        )

        ax.set_xlabel(r"$u_{%s}$" % (["x","y","z"][cols[0]]))
        ax.set_ylabel(r"$u_{%s}$" % (["x","y","z"][cols[1]]))
        ax.set_title(f"{field.capitalize()} Field–Stitch Domain Segmentation")


        plt.tight_layout()

        # ---------- Saving -------------------------------------------------------
        output_dir = "figures_crossover"
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        basename = f"field_stitch_segmentation_{field}"
        print(12342311114)
        png_path = os.path.join(output_dir, basename + ".png")
        pdf_path = os.path.join(output_dir, basename + ".pdf")
        svg_path = os.path.join(output_dir, basename + ".svg")

        print(12342314)
        fig.savefig(png_path, dpi=300)
        fig.savefig(pdf_path)
        fig.savefig(svg_path)

        print(f"[Saved figure at]:\n - {png_path}\n - {pdf_path}\n - {svg_path}")

        plt.show()
        # ========================================================================
        '''


        # Build children
        structA, structB = crossover_split(structA, structB, maskA, maskB, maskA_constraints, maskB_constraints)
        


        # --- 4) Resolve short contacts ---
        maskA_near, dvalsA = atoms_near_interface_cartesian(
            structA,
            f_scalar=f,       # <-- the scalar field used
            L=L,
            cols=cols,
            level=thr,        # <-- threshold used for interface
            delta=interphase_window         # distance window in Å
        )

        maskB_near, dvalsA = atoms_near_interface_cartesian(
            structB,
            f_scalar=f,       # <-- the scalar field used
            L=L,
            cols=cols,
            level=thr,        # <-- threshold used for interface
            delta=interphase_window        # distance window in Å
        )

        def rebuild_constraints_mask(struct, constraints):
            N = struct.AtomPositionManager.atomCount
            if constraints is None or len(constraints) == 0:
                return np.zeros(N, dtype=bool)
            return np.fromiter(
                (validate(i, struct, constraints) for i in range(N)),
                dtype=bool,
                count=N
            )

        if isinstance(constraints, list) and len(constraints) > 0:
            # Recompute constraint masks for the *children*
            maskA_constraints = rebuild_constraints_mask(structA, constraints)
            maskB_constraints = rebuild_constraints_mask(structB, constraints)

            # Now both arrays have the correct shape
            maskA_near = np.logical_and(maskA_near, ~maskA_constraints)
            maskB_near = np.logical_and(maskB_near, ~maskB_constraints)

        '''
        import matplotlib.pyplot as plt
        pos = np.asarray(structA.AtomPositionManager.atomPositions, float)
        x, y = pos[:, cols[0]], pos[:, cols[1]]

        plt.figure(figsize=(5,5))
        plt.scatter(x[~maskA_near], y[~maskA_near], c="grey", s=30, alpha=0.4, label="Other atoms")
        plt.scatter(x[maskA_near], y[maskA_near], c="red", s=50, alpha=0.7, edgecolor="k", label="Near interface")
        plt.xlabel(["x","y","z"][cols[0]])
        plt.ylabel(["x","y","z"][cols[1]])
        plt.legend()
        plt.title("Atoms near interface")
        plt.show()

        pos = np.asarray(structB.AtomPositionManager.atomPositions, float)
        x, y = pos[:, cols[0]], pos[:, cols[1]]

        plt.figure(figsize=(5,5))
        plt.scatter(x[~maskB_near], y[~maskB_near], c="grey", s=30, alpha=0.4, label="Other atoms")
        plt.scatter(x[maskB_near], y[maskB_near], c="red", s=50, alpha=0.7, edgecolor="k", label="Near interface")
        plt.xlabel(["x","y","z"][cols[0]])
        plt.ylabel(["x","y","z"][cols[1]])
        plt.legend()
        plt.title("Atoms near interface")
        plt.show()
        '''

        resolve_collisions(    
            struct=structA,
            mask=maskA_near,
            p = 2.0,
            factor = factor,
            eps = 0.0,
            seed = seed
        )

        resolve_collisions(    
            struct=structB,
            mask=maskB_near,
            p = 2.0,
            factor = factor,
            eps = 0.0,
            seed = seed
        )

        

        return structA, structB


    return _xover






