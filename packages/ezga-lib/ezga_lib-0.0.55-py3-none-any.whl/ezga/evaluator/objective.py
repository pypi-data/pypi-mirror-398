import numpy as np
from numpy.linalg import norm, inv
from sage_lib.partition.Partition import Partition

import warnings
from sklearn.exceptions import ConvergenceWarning

warnings.filterwarnings("ignore", category=ConvergenceWarning)

def evaluate_objectives(structures, objectives_funcs):
    r"""
    Compute multi-objective scores for a set of structures.

    This function applies one or more user-supplied objective functions to an
    array of structures and returns an (N, K) array of objective values,
    where N is the number of structures and K is the number of objectives.

    **Procedure**:

    1. **Single callable**  
       If `objectives_funcs` is a single callable  
       .. math::
          f: \{\text{structures}\} \;\to\; \mathbb{R}^{N \times K},
       then invoke  
       ```python
         results = objectives_funcs(structures)
       ```
       and return it as a NumPy array.

    2. **List of K callables**  
       If `objectives_funcs = [f_1, f_2, \dots, f_K]`, each with signature  
       \\(f_k: \{\text{structures}\} \to \mathbb{R}^N\\), then compute  
       .. math::
          \mathbf{o}_k = f_k(\text{structures}), \quad k=1,\dots,K,
       stack them column-wise  
       .. math::
          O = [\,\mathbf{o}_1,\dots,\mathbf{o}_K\,] \in \mathbb{R}^{N\times K}.
       This is implemented as:
       ```python
       np.array([ func(structures) for func in objectives_funcs ]).T
       ```

    3. **Return shape**  
       Always returns a NumPy array of shape \\((N,K)\\), suitable for downstream
       selection and analysis routines.

    :param structures:
        List of N structure objects. Each object is passed to the objective functions.
    :type structures: list[Any]
    :param objectives_funcs:
        Either a single callable returning an (N,K) array, or a list of K callables
        each returning an (N,) array of values.
    :type objectives_funcs: callable or list[callable]
    :returns:
        NumPy array of shape (N, K) containing objective values.
    :rtype: numpy.ndarray

    :raises ValueError:
        If `objectives_funcs` is a list but the returned shapes do not align, or
        if the inputs are not callable.
    """
    if isinstance(objectives_funcs, list):  
        return np.array([func(structures) for func in objectives_funcs]).T
    else:
        return np.array([objectives_funcs(structures)])

# ---------------------------
# Helper accessors (dataset-first, with safe fallbacks)
# ---------------------------

def _get_positions_list(dataset, coordinate_system: str = "cartesian"):
    """Return list of (n_i,3) arrays, or raise if neither API is available."""
    # Preferred dataset-level accessor
    if hasattr(dataset, "get_all_positions"):
        try:
            return dataset.get_all_positions(coordinate_system=coordinate_system)
        except TypeError:
            # Older signature
            return dataset.get_all_positions()

    # Fallback: try iterating structures
    try:
        structs = list(dataset)
    except TypeError:
        structs = getattr(dataset, "structures", None)
    if structs is None:
        raise ValueError("Dataset does not provide positions API nor is iterable over structures.")

    pos_list = []
    for s in structs:
        apm = getattr(s, "AtomPositionManager", s)
        P = getattr(apm, "atomPositions", None)
        pos_list.append(np.asarray(P, dtype=float) if P is not None else np.zeros((0,3), dtype=float))
    return pos_list


def _get_lattice_vectors_list(dataset):
    """Return list of (3,3) lattice matrices, or safe zeros if missing; length N."""
    if hasattr(dataset, "get_all_lattice_vectors"):
        try:
            return dataset.get_all_lattice_vectors()
        except Exception:
            pass

    # Fallback via structures
    try:
        structs = list(dataset)
    except TypeError:
        structs = getattr(dataset, "structures", None)
    if structs is None:
        # As absolute fallback, infer N from energies and return identities
        try:
            N = len(dataset.get_all_energies())
        except Exception:
            raise ValueError("Cannot access lattice vectors from dataset.")
        return [np.eye(3) for _ in range(N)]

    mats = []
    for s in structs:
        apm = getattr(s, "AtomPositionManager", s)
        L = getattr(apm, "latticeVectors", None)
        if L is None:
            mats.append(np.eye(3))
        else:
            mats.append(np.asarray(L, dtype=float))
    return mats


# ---------------------------
# 1) Naive objectives aggregator (dataset-aware)
# ---------------------------

def naive_objectives(dataset, objective_funcs):
    """
    Evaluate a list of objective callables on the dataset and stack results column-wise.

    Each objective f must adhere to: f(dataset) -> np.ndarray of shape (N,)

    Returns
    -------
    np.ndarray, shape (N, K)
    """
    # Infer N from energies (preferred) or compositions
    try:
        N = len(dataset.get_all_energies())
    except Exception:
        X_all, _ = dataset.get_all_compositions(return_species=True)
        N = X_all.shape[0]

    K = len(objective_funcs)
    out = np.zeros((N, K), dtype=float)

    for j, f in enumerate(objective_funcs):
        try:
            col = f(dataset)
            col = np.asarray(col, dtype=float).reshape(-1)
            if col.shape[0] != N:
                # Broadcast scalar or pad/truncate to N
                if col.size == 1:
                    out[:, j] = float(col)
                else:
                    m = min(N, col.shape[0])
                    out[:m, j] = col[:m]
            else:
                out[:, j] = col
        except Exception:
            # If any objective fails, leave zeros in that column
            pass
    return out


# ---------------------------
# 2) K-means model selection (unchanged API, improved guards)
# ---------------------------

def find_optimal_kmeans_k(data, max_k=10, random_state=42):
    """
    Finds an optimal number of clusters (2..max_k) via silhouette score.
    If samples < 2, returns 1.
    """
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.metrics import silhouette_score
    from sklearn.cluster import KMeans

    data = np.asarray(data)
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    n_samples = data.shape[0]
    if n_samples < 2:
        return 1

    best_k = 2
    best_silhouette = -1

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        for k in range(2, max_k + 1):
            if k >= n_samples:
                break  # cannot have more clusters than samples
            try:
                kmeans = KMeans(n_clusters=k, random_state=random_state, n_init="auto")
                labels = kmeans.fit_predict(data)
                # Require at least 2 distinct labels
                if len(set(labels)) < 2:
                    continue
                score = silhouette_score(data, labels)
                if score > best_silhouette:
                    best_silhouette = score
                    best_k = k
            except Exception:
                continue
    return best_k


# ---------------------------
# 3) Volume objective (dataset-first)
# ---------------------------

def objective_volume():
    """
    Volume per structure from lattice vectors. If missing, returns 0 for that structure.

    Dataset API: dataset.get_all_lattice_vectors() -> list of (3,3)
    Fallback: s.AtomPositionManager.latticeVectors
    """
    def compute(dataset):
        mats = _get_lattice_vectors_list(dataset)
        vols = []
        for L in mats:
            try:
                vols.append(abs(np.linalg.det(np.asarray(L, dtype=float))))
            except Exception:
                vols.append(0.0)
        return np.asarray(vols, dtype=float)
    return compute


# ---------------------------
# 4) Density objective (dataset-first)
# ---------------------------

def objective_density(atomic_weights: dict | None = None):
    """
    Density = total mass / volume.
    Mass from composition counts and `atomic_weights` (unit mass if None).
    Volume from lattice determinant (identity if missing -> vol=1 to avoid div-by-zero).
    """
    def compute(dataset):
        # Compositions
        X_all, species_order = dataset.get_all_compositions(return_species=True)
        N = X_all.shape[0]
        # Mass vector per species
        if atomic_weights is None:
            w = np.ones(len(species_order), dtype=float)
        else:
            w = np.array([atomic_weights.get(lbl, 1.0) for lbl in species_order], dtype=float)

        total_mass = X_all.dot(w)  # shape (N,)

        # Volumes
        mats = _get_lattice_vectors_list(dataset)
        vols = np.empty(N, dtype=float)
        for i, L in enumerate(mats):
            try:
                vols[i] = abs(np.linalg.det(np.asarray(L, dtype=float)))
            except Exception:
                vols[i] = 1.0  # neutral fallback

        # Density (safe)
        with np.errstate(divide="ignore", invalid="ignore"):
            dens = np.where(vols > 0, total_mass / vols, 0.0)
        dens = np.nan_to_num(dens, nan=0.0, posinf=0.0, neginf=0.0)
        return dens
    return compute


# ---------------------------
# 5) Average interatomic distance (dataset-first)
# ---------------------------

def objective_average_interatomic_distance(coordinate_system: str = "cartesian"):
    """
    Mean of all pairwise distances per structure.
    If <2 atoms, returns 0 for that structure.
    """
    from scipy.spatial.distance import pdist

    def compute(dataset):
        pos_list = _get_positions_list(dataset, coordinate_system=coordinate_system)
        out = []
        for P in pos_list:
            P = np.asarray(P, dtype=float)
            if P.ndim != 2 or P.shape[0] < 2:
                out.append(0.0)
                continue
            try:
                d = pdist(P)          # condensed distances
                out.append(float(np.mean(d))) if d.size else out.append(0.0)
            except Exception:
                out.append(0.0)
        return np.asarray(out, dtype=float)
    return compute


# ---------------------------
# 6) Average coordination number within cutoff (dataset-first)
# ---------------------------

def objective_coordination_number(cutoff: float = 3.0, coordinate_system: str = "cartesian"):
    """
    Average number of neighbors within `cutoff` per atom, per structure.
    Self-distances excluded.
    """
    from scipy.spatial.distance import pdist, squareform

    def compute(dataset):
        pos_list = _get_positions_list(dataset, coordinate_system=coordinate_system)
        out = []
        for P in pos_list:
            P = np.asarray(P, dtype=float)
            n = P.shape[0] if P.ndim == 2 else 0
            if n == 0:
                out.append(0.0)
                continue
            if n == 1:
                out.append(0.0)
                continue
            try:
                D = squareform(pdist(P))
                np.fill_diagonal(D, np.inf)
                cn = np.sum(D < float(cutoff), axis=1)
                out.append(float(np.mean(cn)))
            except Exception:
                out.append(0.0)
        return np.asarray(out, dtype=float)
    return compute


def objective_symmetry(
    coordinate_system: str = "cartesian",
    use_mass_weights: bool = False,
    normalize_by_mean: bool = False,
):
    """
    Symmetry score based on the dispersion of atomic distances to the center.
    Lower score => more symmetric.

    Dataset-first API (preferred; any missing pieces fall back to per-structure):
      - dataset.get_all_positions(coordinate_system="cartesian"|"fractional") -> list[np.ndarray], len N,
        each array shaped (n_atoms_i, 3)
      - OPTIONAL: dataset.get_all_masses() -> list[np.ndarray], len N, each (n_atoms_i,)

    Fallback per-structure API (original style):
      - s.AtomPositionManager.atomPositions : (n_atoms, 3)
      - OPTIONAL when use_mass_weights=True:
            s.AtomPositionManager.atomMasses : (n_atoms,)

    Parameters
    ----------
    coordinate_system : {"cartesian","fractional"}
        Which coordinates to request from the dataset if available.
        Ignored when falling back to per-structure attributes.
    use_mass_weights : bool
        If True and masses are available, compute a *mass-weighted* center (COM).
        Otherwise use an unweighted mean center.
    normalize_by_mean : bool
        If True, return the coefficient of variation: std(dist) / mean(dist)
        (guards against trivial scaling with system size). If mean==0, returns 0.

    Returns
    -------
    compute(dataset) -> np.ndarray, shape (N,)
        Symmetry score per structure.
    """
    import numpy as np

    def _center(points: np.ndarray, masses: np.ndarray | None) -> np.ndarray:
        if points.size == 0:
            return np.zeros(3, dtype=float)
        if masses is not None and use_mass_weights:
            m = np.asarray(masses, dtype=float).reshape(-1, 1)
            m[m <= 0] = 0.0
            denom = m.sum()
            if denom > 0:
                return (points * m).sum(axis=0) / denom
        # Unweighted center
        return points.mean(axis=0)

    def _score_from_positions(points: np.ndarray, masses: np.ndarray | None) -> float:
        if points is None or points.ndim != 2 or points.shape[0] == 0:
            return 0.0
        c = _center(points, masses)
        d = np.linalg.norm(points - c, axis=1)
        if d.size == 0:
            return 0.0
        sd = float(np.std(d))
        if normalize_by_mean:
            mu = float(np.mean(d))
            return sd / mu if mu > 0 else 0.0
        return sd

    def _try_dataset_positions(dataset):
        """Return (positions_list, masses_list_or_None) or (None, None) if not available."""
        positions_list = None
        masses_list = None
        # Try a generic positions accessor
        if hasattr(dataset, "get_all_positions"):
            try:
                positions_list = dataset.get_all_positions(coordinate_system=coordinate_system)
            except TypeError:
                # Older signature without kwarg
                positions_list = dataset.get_all_positions()
        # Optional masses
        if hasattr(dataset, "get_all_masses"):
            try:
                masses_list = dataset.get_all_masses()
            except Exception:
                masses_list = None
        return positions_list, masses_list

    def compute(dataset):
        # Preferred path: dataset-level bulk access
        positions_list, masses_list = _try_dataset_positions(dataset)

        scores = []
        if positions_list is not None:
            # Dataset provided a list of (n_i,3) arrays
            for i, P in enumerate(positions_list):
                masses = None
                if use_mass_weights and masses_list is not None and i < len(masses_list):
                    masses = masses_list[i]
                    if masses is not None and len(masses) != len(P):
                        masses = None  # shape mismatch; ignore masses safely
                scores.append(_score_from_positions(np.asarray(P, dtype=float), masses))
            return np.asarray(scores, dtype=float)

        # Fallback: iterate structures and read attributes
        # Expect s.AtomPositionManager.atomPositions (and optionally .atomMasses)
        try:
            structs = list(dataset)  # some datasets are iterable
        except TypeError:
            # If not iterable, try to access an internal container
            structs = getattr(dataset, "structures", None)
            if structs is None:
                raise ValueError("Dataset does not provide positions API nor is iterable over structures.")

        for s in structs:
            P = getattr(getattr(s, "AtomPositionManager", s), "atomPositions", None)
            masses = None
            if use_mass_weights:
                masses = getattr(getattr(s, "AtomPositionManager", s), "atomMasses", None)
            P = np.asarray(P, dtype=float) if P is not None else None
            masses = np.asarray(masses, dtype=float) if masses is not None else None
            if masses is not None and P is not None and len(masses) != len(P):
                masses = None  # mismatch; ignore
            scores.append(_score_from_positions(P, masses))
        return np.asarray(scores, dtype=float)

    return compute


def objective_energy(scale: float = 1.0):
    """
    Returns a function that computes scaled total energies from the dataset.

    Dataset API expected:
      - dataset.get_all_energies() -> array-like of shape (N,)

    Parameters
    ----------
    scale : float
        Factor to scale energies.

    Returns
    -------
    compute(dataset) -> np.ndarray, shape (N,)
    """
    import numpy as np

    def compute(dataset):
        y = np.asarray(dataset.get_all_energies(), dtype=float)
        y = np.nan_to_num(y, nan=0.0)
        return scale * y
    return compute

def objective_formation_energy(reference_potentials: dict | None = None,
                               unique_labels: list[str] | None = None,
                               delta: float = 0.25):
    """
    Compute formation energies:  E_form = E_total - X · μ.

    If `reference_potentials` is None, μ is obtained by *weighted* least squares,
    where high-energy/outlier structures receive exponentially smaller weights.

        w_i = exp(-(E_i - E_min) / delta)

    Dataset API expected:
      - dataset.get_all_energies() -> (N,)
      - dataset.get_all_compositions(return_species=True)
          -> (X_all, species_order)
      - dataset.get_species_mapping(order="stored") -> {label: index}

    Parameters
    ----------
    reference_potentials : dict | None
        {label: μ}. If None, μ is fitted via weighted least squares.
    unique_labels : list[str] | None
        Ordered list of species for X and μ.
    delta : float
        Weight decay parameter (in eV). Lower delta => stronger suppression
        of unstable structures.

    Returns
    -------
    compute(dataset) -> np.ndarray, shape (N,)
        Formation energies.
    """
    import numpy as np

    def _fit_mu_lstsq(X: np.ndarray, y: np.ndarray) -> np.ndarray:
        # Columns with zero variance carry no information; keep them but set μ=0.
        col_var = X.var(axis=0)
        informative = col_var > 0.0
        mu = np.zeros(X.shape[1], dtype=float)
        if np.any(informative):
            mu_inf, *_ = np.linalg.lstsq(X[:, informative].astype(float),
                                         y.astype(float),
                                         rcond=None)
            mu[informative] = mu_inf
        return mu

    def _fit_mu_weighted(X: np.ndarray, y: np.ndarray, delta: float=.25) -> np.ndarray:
        """
        Weighted least squares:
            W_i = exp(-(y_i - y_min) / delta)
        Columns with zero variance keep μ = 0.
        """
        col_var = X.var(axis=0)
        informative = col_var > 0.0

        mu = np.zeros(X.shape[1], dtype=float)

        if not np.any(informative):
            return mu

        # Compute energy-based weights
        y_min = float(np.min(y))
        w = np.exp(-(y - y_min) / max(delta, 1e-10))
        W = np.sqrt(w)[:, None]

        Xw = X[:, informative] * W
        yw = y * np.sqrt(w)

        mu_inf, *_ = np.linalg.lstsq(Xw.astype(float),
                                     yw.astype(float),
                                     rcond=None)
        mu[informative] = mu_inf
        return mu

    def compute(dataset):
        # Energies
        y = np.asarray(dataset.get_all_energies(), dtype=float)
        y = np.nan_to_num(y, nan=0.0)
        N = y.shape[0]

        # Compositions and species ordering
        X_all, species_order = dataset.get_all_compositions(return_species=True)
        mapping = dataset.get_species_mapping(order="stored")

        # Choose labels
        labels = list(unique_labels) if unique_labels is not None else list(species_order)

        # Build X for the selected labels (missing labels => zero column)
        idx = np.fromiter((mapping.get(lbl, -1) for lbl in labels), dtype=int, count=len(labels))
        valid = (idx >= 0)

        X = np.zeros((N, len(labels)), dtype=float)
        if np.any(valid):
            X[:, valid] = X_all[:, idx[valid]]

        # μ vector
        if reference_potentials is None:
            mu_vec = _fit_mu_weighted(X, y, delta=delta)
        else:
            mu_vec = np.array([reference_potentials.get(lbl, 0.0)
                               for lbl in labels], dtype=float)

        # Formation energy
        fE = y - X.dot(mu_vec)
        return fE

    return compute

def objective_min_distance_to_hull(
    reference_potentials: dict | None = None,
    variable_species: str | None = None,
    A: float | None = None,
    mu_range: tuple[float, float] | None = None,
    steps: int = 20,
    unique_labels: list[str] | None = None,
):
    """
    For each structure, compute the minimal distance above the lower convex hull
    in (composition-fractions..., formation-energy) space while scanning the
    chemical potential μ of a single species.

    Parameters
    ----------
    reference_potentials : dict | None
        Fixed chemical potentials {label: μ}. If None, μ is *interpolated*
        from the dataset by linear least squares (see Notes below).
    variable_species : str
        Species whose μ is scanned over `mu_range`.
    A : float | None
        Normalization. If None -> per-atom normalization (energy/atom).
        If float -> use this constant for all structures (e.g., fixed area/volume).
    mu_range : (float, float) | None
        Range [μ_min, μ_max] to sample for the variable species.
        If None, defaults to (-3.0, 1.0).
    steps : int
        Number of μ samples.
    unique_labels : list[str] | None
        Optional ordered list of labels that define the composition space.
        If None, inferred from the dataset order; `variable_species` is appended if missing.

    Returns
    -------
    compute : callable
        compute(dataset) -> np.ndarray of shape (N_structs,)
        Minimal distance above the hull for each structure across the scanned μ.
    """
    import numpy as np
    from scipy.spatial import ConvexHull, QhullError

    if variable_species is None:
        raise ValueError("`variable_species` must be provided.")

    if mu_range is None:
        mu_range = (-3.0, 1.0)

    def _fit_mu_from_dataset(X: np.ndarray, y: np.ndarray, use_fractions: bool) -> np.ndarray:
        """
        Estimate μ by solving least squares:
          - use_fractions=True:  y/N ≈ (X/N)·μ
          - use_fractions=False: y   ≈  X·μ
        Non-informative columns (zero variance) are kept but set to μ=0 to stabilize the fit.
        """
        if use_fractions:
            N_atoms = X.sum(axis=1, keepdims=True).astype(float)
            N_atoms[N_atoms == 0.0] = 1.0
            D = X / N_atoms
            y_fit = y / N_atoms.ravel()
        else:
            D = X.astype(float)
            y_fit = y.astype(float)

        col_var = D.var(axis=0)
        informative = col_var > 0.0

        mu = np.zeros(D.shape[1], dtype=float)
        if np.any(informative):
            mu_inf, *_ = np.linalg.lstsq(D[:, informative], y_fit, rcond=None)
            mu[informative] = mu_inf
        return mu

    def _lower_hull_distance(points: np.ndarray) -> np.ndarray:
        """
        Given points in R^(M+1) where last coordinate is energy, return distance
        above the *lower* convex hull for each point. Uses QJ joggle fallback.
        points: shape (N, M+1) = [fractions..., fE]
        """
        N, D = points.shape
        if N < (D + 1):  # need at least (M+2) points in R^(M+1)
            return np.zeros(N, dtype=float)

        try:
            hull = ConvexHull(points)
        except QhullError:
            try:
                hull = ConvexHull(points, qhull_options="QJ")
            except Exception:
                return np.zeros(N, dtype=float)

        d_above = np.zeros(N, dtype=float)
        # hull.equations: each row [a_0 ... a_M a_E c] with energy coefficient at index -2
        for eq in hull.equations:
            a_all = eq[:-1]
            c = eq[-1]
            a_E = a_all[-1]   # coefficient for the last (energy) coordinate
            if a_E < 0.0:     # select lower facets
                na = np.linalg.norm(a_all)
                if na == 0.0:
                    continue
                signed = (points @ a_all + c) / na
                np.maximum(d_above, signed, out=d_above)
        d_above[d_above < 0.0] = 0.0
        return d_above

    def compute(dataset):
        # ---- 1) Data from dataset ----
        y = np.asarray(dataset.get_all_energies(), dtype=float)  # (N,)
        species, species_order = dataset.get_all_compositions(return_species=True)
        mapping = dataset.get_species_mapping(order="stored")

        # ---- 2) Labels and composition matrix X ----
        labels = list(unique_labels) if unique_labels is not None else list(species_order)
        if variable_species not in labels:
            labels.append(variable_species)

        idx = np.fromiter((mapping.get(lbl, -1) for lbl in labels), dtype=int, count=len(labels))
        valid = (idx >= 0)

        N = species.shape[0]
        M = len(labels)
        X = np.zeros((N, M), dtype=float)
        if np.any(valid):
            X[:, valid] = species[:, idx[valid]]

        # ---- 3) Normalization ----
        if A is None:
            norm = species.sum(axis=1).astype(float)  # total atoms
            norm[norm == 0.0] = 1.0
            use_fractions_for_fit = True
        else:
            norm = np.full(N, float(A), dtype=float)
            use_fractions_for_fit = False

        # ---- 4) Base chemical potentials μ ----
        if reference_potentials is None:
            mu_base = _fit_mu_from_dataset(X, y, use_fractions=use_fractions_for_fit)
        else:
            mu_base = np.array([reference_potentials.get(lbl, 0.0) for lbl in labels], dtype=float)

        try:
            var_idx = labels.index(variable_species)
        except ValueError:
            raise ValueError(f"Variable species '{variable_species}' is not among labels {labels}.")

        # ---- 5) Composition fractions for hull coordinates ----
        denom = X.sum(axis=1, keepdims=True)
        denom[denom == 0.0] = 1.0
        comp_frac = X / denom  # (N, M)

        # ---- 6) Scan μ for the variable species; accumulate minimal hull distance ----
        mu_vals = np.linspace(mu_range[0], mu_range[1], int(steps))
        min_dist = np.full(N, np.inf, dtype=float)

        for mu_v in mu_vals:
            mu = mu_base.copy()
            # Interpret mu_range as the *absolute* μ for the variable species.
            # If you prefer "offset" behavior, set: mu[var_idx] = mu_base[var_idx] + mu_v
            mu[var_idx] = mu_v

            fE = (y - X.dot(mu)) / norm  # per-atom (or per-A) formation energy
            pts = np.hstack([comp_frac, fE.reshape(-1, 1)])
            d = _lower_hull_distance(pts)
            np.minimum(min_dist, d, out=min_dist)

        # Replace inf (e.g., degenerate cases) by zero
        min_dist[~np.isfinite(min_dist)] = 0.0
        return min_dist

    return compute



def objective_distance_to_composition_hull(
    reference_potentials: dict | None = None,
    A: float | None = None,
    unique_labels: list[str] | None = None,
):
    """
    Distance above the lower convex hull in (composition fractions..., formation energy) space.
    If `reference_potentials` is None, chemical potentials μ are estimated by linear least-squares
    interpolation from the dataset (E ≈ X·μ or E/N ≈ (X/N)·μ, depending on normalization).
    """

    import numpy as np
    from scipy.spatial import ConvexHull, QhullError

    def _fit_mu_from_dataset(X: np.ndarray, y: np.ndarray, use_fractions: bool, all_labels: list[str]) -> np.ndarray:
        """
        Estimate μ by solving least squares:
          - use_fractions=True:  y_norm = y/N,  D = X/N  -> solve D μ ≈ y_norm
          - use_fractions=False: y,             D = X    -> solve D μ ≈ y
        Columns in D with zero variance are kept but do not destabilize the fit.
        """
        if use_fractions:
            N_atoms = X.sum(axis=1, keepdims=True).astype(float)
            N_atoms[N_atoms == 0.0] = 1.0
            D = X / N_atoms
            y_fit = y / N_atoms.ravel()
        else:
            D = X.astype(float)
            y_fit = y.astype(float)

        # Identify informative columns (non-allzero variance) to improve conditioning
        col_var = D.var(axis=0)
        informative = col_var > 0.0

        mu = np.zeros(D.shape[1], dtype=float)
        if np.any(informative):
            mu_inf, *_ = np.linalg.lstsq(D[:, informative], y_fit, rcond=None)
            mu[informative] = mu_inf
        # Non-informative columns remain 0.0
        return mu

    def compute(dataset):
        # --- data from dataset ---
        y = np.asarray(dataset.get_all_energies(), dtype=float)  # (N,)
        species, species_order = dataset.get_all_compositions(return_species=True)
        mapping = dataset.get_species_mapping(order="stored")

        # labels order
        labels = list(unique_labels) if unique_labels is not None else list(species_order)

        # composition matrix X (counts for selected labels)
        idx = np.fromiter((mapping.get(lbl, -1) for lbl in labels), dtype=int, count=len(labels))
        valid = (idx >= 0)
        M = len(labels)
        N = species.shape[0]

        X = np.zeros((N, M), dtype=float)
        if np.any(valid):
            X[:, valid] = species[:, idx[valid]]

        # normalization vector
        if A is None:
            norm = species.sum(axis=1).astype(float)
            norm[norm == 0.0] = 1.0
            use_fractions_for_fit = True
        else:
            norm = np.full(N, float(A), dtype=float)
            use_fractions_for_fit = False

        # — μ vector: provided or fitted —
        if reference_potentials is None:
            mu_vec = _fit_mu_from_dataset(X, y, use_fractions=use_fractions_for_fit, all_labels=labels)
        else:
            mu_vec = np.array([reference_potentials.get(lbl, 0.0) for lbl in labels], dtype=float)

        # formation energy per normalization
        fE = (y - X.dot(mu_vec)) / norm

        # composition fractions (on selected labels)
        denom = X.sum(axis=1, keepdims=True)
        denom[denom == 0.0] = 1.0
        comp_frac = X / denom

        points = np.hstack([comp_frac, fE.reshape(-1, 1)])

        # Need at least (M+2) points for a full-dimensional hull in R^(M+1)
        if points.shape[0] < (M + 2):
            return np.zeros(N, dtype=float)

        # hull with joggle fallback
        try:
            hull = ConvexHull(points)
        except QhullError:
            try:
                hull = ConvexHull(points, qhull_options="QJ")
            except Exception:
                return np.zeros(N, dtype=float)

        # distance above *lower* hull (energy is last coordinate)
        d_above = np.zeros(N, dtype=float)
        for eq in hull.equations:
            a = eq[:-1]   # includes fraction coeffs and energy coeff
            c = eq[-1]
            a_E = a[-1]
            if a_E < 0.0:  # lower facet
                na = np.linalg.norm(a)
                if na == 0.0:
                    continue
                signed = (points @ a + c) / na
                np.maximum(d_above, signed, out=d_above)

        d_above[d_above < 0] = 0.0
        return d_above

    return compute



def objective_similarity(
    r_cut=4.0,
    n_max=2,
    l_max=2,
    sigma=0.5,
    n_components=3,
    compress_model='pca',  # or 'umap', etc.
    eps=0.6,
    min_samples=2,
    cluster_model='minibatch-kmeans',  # or 'dbscan'
    max_clusters=10
):
    """
    Returns a function that computes similarity scores for a list of structures based on the
    complement of their anomaly scores computed in the cluster space derived from SOAP descriptors.
    
    Similarity is defined as:
         similarity = 1 / (1 + anomaly)
    so that a lower anomaly (i.e., a more typical structure) yields a higher similarity,
    with similarity values in the range (0, 1].
    
    Parameters
    ----------
    r_cut : float
        Cutoff radius for the SOAP calculation.
    n_max : int
        Maximum number of radial basis functions.
    l_max : int
        Maximum spherical harmonic degree.
    sigma : float
        Gaussian width for the SOAP descriptors.
    n_components : int
        Number of components for dimensionality reduction.
    compress_model : str
        Compression model to use (e.g., 'pca' or 'umap').
    eps : float
        Epsilon parameter for the clustering algorithm.
    min_samples : int
        Minimum number of samples for clustering.
    cluster_model : str
        Identifier for the clustering method (e.g., 'dbscan' or 'minibatch-kmeans').
    max_clusters : int
        Maximum number of allowed clusters.
    
    Returns
    -------
    callable
         A function that accepts a list of dataset and returns a NumPy array of similarity scores.
    
    See Also
    --------
    objective_anomality
         Function that calculates anomaly scores from the cluster space.
    """
    # Get the anomaly objective function using the provided parameters.
    anomaly_func = objective_anomality(
        r_cut=r_cut,
        n_max=n_max,
        l_max=l_max,
        sigma=sigma,
        n_components=n_components,
        compress_model=compress_model,
        eps=eps,
        min_samples=min_samples,
        cluster_model=cluster_model,
        max_clusters=max_clusters
    )
    
    def compute_similarity(dataset):
        """
        Computes similarity scores for a list of dataset.
        
        Parameters
        ----------
        dataset : list
            List of atomic dataset for which to compute similarity.
        
        Returns
        -------
        np.ndarray
            An array of similarity scores (one per structure), calculated as 1 / (1 + anomaly).
        """
        # Compute anomaly scores using the wrapped anomaly function.
        anomaly_scores = anomaly_func( dataset.containers )
        
        # Compute similarity scores as the inverse relation to anomaly:
        # similarity = 1 / (1 + anomaly)
        # This ensures that dataset with low anomaly (i.e., more typical) have similarity near 1,
        # while dataset with high anomaly have similarity scores near 0.
        similarity_scores = 1.0 / (1.0 + anomaly_scores)

        return similarity_scores

    return compute_similarity
    
def objective_anomality(
    r_cut=4.0,
    n_max=2,
    l_max=2,
    sigma=0.5,
    n_components=3,
    compress_model='pca', #'umap'
    eps=0.6,
    min_samples=2,
    cluster_model='minibatch-kmeans', #'dbscan'
    max_clusters=10
):
    """
    Returns a function that computes anomaly scores for a list of structures using the cluster space
    derived from SOAP descriptors.

    The process is as follows:
        1. Compute SOAP descriptors for each structure.
        2. Compress the descriptors using the specified dimensionality reduction method.
        3. Perform clustering on the compressed data for each atomic species.
        4. Generate a cluster count matrix representing the cluster space.
        5. Compute anomaly scores as the Mahalanobis distance in this space.

    Parameters:
        r_cut (float): Cutoff radius for SOAP calculation.
        n_max (int): Maximum number of radial basis functions.
        l_max (int): Maximum spherical harmonic degree.
        sigma (float): Gaussian width for the SOAP descriptors.
        n_components (int): Number of components for dimensionality reduction.
        compress_model (str): Compression model to use (e.g., 'pca', 'umap').
        eps (float): Epsilon parameter for the clustering algorithm.
        min_samples (int): Minimum samples for clustering.
        cluster_model (str): Identifier for the clustering method (e.g., 'dbscan').
        max_clusters (int): Maximum number of allowed clusters.

    Returns:
        callable: A function that accepts a list of structures and returns a NumPy array of anomaly scores.
    """
    from sklearn.decomposition import PCA
    from scipy.spatial.distance import mahalanobis
    from sklearn.cluster import KMeans
    from scipy.stats import zscore

    def compute(
        dataset,
        n_components=5,
        r_cut=5.0,
        n_max=3,
        l_max=3,
        sigma=0.5,
        max_clusters=10,
    ):
        """
        Computes anomaly scores per structure by:
          1. Generating SOAP descriptors per species
          2. Doing PCA + K-means (with an optimal number of clusters up to max_clusters)
          3. Counting cluster assignments to build a combined cluster-count matrix
          4. Using Mahalanobis distance in that cluster space as an anomaly metric

        Parameters
        ----------
        dataset : Partitions
            List of atomic structures.
        n_components : int
            Number of PCA components for dimensionality reduction per species.
        r_cut, n_max, l_max, sigma : float or int
            Parameters for the SOAP calculation.
        max_clusters : int
            The maximum possible number of clusters to try per species.

        Returns
        -------
        anomaly_scores : np.ndarray, shape (num_structures,)
            Mahalanobis-based anomaly scores for each structure.
        """

        # --------------------------------------------------------------------------
        # Step 0: Validate input
        # --------------------------------------------------------------------------
        n_structures = dataset.size()
        if n_structures == 0:
            return np.array([])

        if n_structures < n_components:
            # If you cannot reliably do PCA because you have fewer structures than n_components
            return np.zeros(n_structures)

        # --------------------------------------------------------------------------
        # Step 1: SOAP Descriptors
        # --------------------------------------------------------------------------
        descriptors_by_species, atom_info_by_species = dataset.get_SOAP(
            r_cut=r_cut,
            n_max=n_max,
            l_max=l_max,
            sigma=sigma,
            save=False,
            cache=False
        )
        # descriptors_by_species: {species: (num_atoms_of_species, feature_dim)}
        # atom_info_by_species:   {species: [(structure_idx, atom_idx, ...), ...]}

        # If no descriptors at all, return zeros
        if not descriptors_by_species:
            return np.zeros(n_structures)

        # We will accumulate each species' cluster counts in a list.
        # Ultimately we'll stack them horizontally, so that each species
        # contributes a block of columns to the final (num_structures x total_num_clusters).
        cluster_counts_list = []

        # --------------------------------------------------------------------------
        # Step 2: For each species, do PCA + K-means and build cluster counts
        # --------------------------------------------------------------------------
        for species, desc_array in descriptors_by_species.items():
            # desc_array shape: (num_atoms_of_species, feature_dim)
            if desc_array.shape[0] == 0:
                # No atoms of this species
                continue

            # structure_indices[i] => a tuple (struc_idx, atom_idx, etc.)
            # We'll parse out the structure index from that tuple.
            structure_indices_full = atom_info_by_species[species]

            # Check descriptor dimension
            feature_dim = desc_array.shape[1]
            if feature_dim < n_components:
                # Not enough descriptor dimension => produce a zero matrix
                # or skip. We'll do zero matrix here, but you can adjust logic.
                zero_matrix = np.zeros((n_structures, 1), dtype=int)
                cluster_counts_list.append(zero_matrix)
                continue

            # 2A. PCA
            try:
                pca = PCA(n_components=n_components)
                compressed_data = pca.fit_transform(desc_array)  # shape: (num_atoms_of_species, n_components)
            except ValueError:
                # If PCA fails, skip or produce zeros
                zero_matrix = np.zeros((n_structures, 1), dtype=int)
                cluster_counts_list.append(zero_matrix)
                continue

            # 2B. Determine Optimal Cluster Count up to max_clusters
            #     Then run K-means for that cluster count.
            optimal_k = find_optimal_kmeans_k(compressed_data, max_k= np.min([compressed_data.shape[0], max_clusters]) ) 
            # If there's only 1 cluster (edge case), we skip KMeans or do a single cluster labeling:
            if optimal_k == 1:
                # All atoms in the same cluster => cluster_counts is shape (n_structures, 1)
                cluster_counts = np.zeros((n_structures, 1), dtype=int)
                for i_atom, c_data in enumerate(compressed_data):
                    # Single cluster => cluster index is 0
                    struc_idx = structure_indices_full[i_atom][0]
                    if 0 <= struc_idx < n_structures:
                        cluster_counts[struc_idx, 0] += 1
            else:
                kmeans = KMeans(n_clusters=optimal_k, random_state=42)
                atom_clusters = kmeans.fit_predict(compressed_data)  # shape: (num_atoms_of_species,)

                # 2C. Build cluster-count matrix
                # We want shape (n_structures, optimal_k).
                cluster_counts = np.zeros((n_structures, optimal_k), dtype=int)
                for i_atom, cluster_label in enumerate(atom_clusters):
                    struc_idx = structure_indices_full[i_atom][0]
                    # Guard against out-of-range structure indices
                    if 0 <= struc_idx < n_structures:
                        cluster_counts[struc_idx, cluster_label] += 1

            # Accumulate cluster counts for this species
            cluster_counts_list.append(cluster_counts)

        # If no species produced cluster counts, return zeros
        if not cluster_counts_list:
            return np.zeros(n_structures)

        # --------------------------------------------------------------------------
        # Step 3: Combine cluster counts from all species
        # --------------------------------------------------------------------------
        # We horizontally stack them. Example: species A => (n_structures, a_k),
        # species B => (n_structures, b_k). Combined => (n_structures, a_k + b_k).
        combined_cluster_counts = np.hstack(cluster_counts_list)  # shape: (n_structures, sum_of_clusters_all_species)

        # --------------------------------------------------------------------------
        # Step 4: Anomaly Scoring in cluster space (Mahalanobis)
        # --------------------------------------------------------------------------
        # 4A. Z-score normalization
        normalized_data = zscore(combined_cluster_counts, axis=0)
        normalized_data = np.nan_to_num(normalized_data, nan=0.0)

        # 4B. Mean / Covariance
        mean_vector = np.mean(normalized_data, axis=0)
        cov_matrix = np.cov(normalized_data, rowvar=False)

        # Regularize the covariance matrix to avoid singularities
        cov_matrix += 1e-6 * np.eye(cov_matrix.shape[0])
        cov_inv = inv(cov_matrix)

        # 4C. Mahalanobis distance => anomaly score
        anomaly_scores = []
        for row in normalized_data:
            try:
                dist = mahalanobis(row, mean_vector, cov_inv)
            except Exception:
                dist = np.nan
            anomaly_scores.append(dist)
        
        return np.array(anomaly_scores)

    return compute

def information_novelty(
    r_cut=4.0,
    n_max=2,
    l_max=2,
    sigma=0.5,
    n_components=3,
    compress_model='pca', #'umap'
    eps=0.6,
    min_samples=2,
    cluster_model='minibatch-kmeans', #'dbscan'
    max_clusters=10
):
    """
    """
    from ..classification.clustering import SOAPClusterAnalyzer
    from ..metric.information_ensemble_metrics import InformationEnsambleMetric

    def compute(       
        dataset,
        n_components=5,
        r_cut=5.0,
        n_max=3,
        l_max=3,
        sigma=0.5,
        max_clusters=10,
        ):

        if dataset.size() <= n_components:
            return np.ones( dataset.size() )

        analyzer = SOAPClusterAnalyzer()
        cluster_array = analyzer.get_cluster_counts( dataset.containers )

        IEM = InformationEnsambleMetric(
            metric = 'novelty',
        )

        information_novelty = IEM.compute(cluster_array)

        return np.array(information_novelty)
    
    return compute

def objective_min_distance_to_hull_pourbaix_diagram(pd:object, references_species:list):
    from collections import defaultdict
    from ..utils.pourbaix_diagram import Species 

    def objective(dataset):
        pd._candidate_species = {}
        pd._name_counts = defaultdict(int)

        for structure in dataset:
            name = ''.join([f'{item}{key}' for item, key in structure.AtomPositionManager.atomCountDict.items()])
            pd.add_candidate_species( Species(name, G=structure.AtomPositionManager.E) )
            
        distances = pd.distance_convex_hull( reference_species=references_species, baseline_specie=None )

        return distances

    return objective


def objective_min_distance_to_electrochemicalhull(
    reference_potentials: dict,
    H_range: tuple = (-1.0, 0.5),
    steps: int = 100,
    unique_labels: list = None,
):
    """
    Objective function for GA: minimal distance of each structure to the convex hull
    across a range of applied electrochemical potentials (U).

    The electron chemical potential is varied via the CHE formalism:
        mu_e(U) = - e * U + pH- and p_H2-dependent terms.

    Parameters
    ----------
    reference_potentials : dict
        Dictionary of fixed chemical potentials, e.g. {'Cu': -3.5, 'O': -4.2, 'H2O': -14.25}.
        These are constants and serve as the baseline for non-variable species.
    H_range : tuple
        (H_min, H_max) range of applied potential (in eV).
    steps : int
        Number of discrete U values to sample between H_min and H_max.

    Returns
    -------
    compute : callable
        Function that, when called with a list of structures, returns
        min_distances: np.ndarray of shape (N_structs,)
            Minimum energy distance to convex hull for each structure across U_range.
    """
    unique_labels = {lbl for lbl in reference_potentials.keys()}.union({'O','H'}) - {'H2O'}
    unique_labels_dict = { u:i for i, u in enumerate(unique_labels) }
    M = len(unique_labels)

    def compute(dataset):
        """
        Compute min distance to convex hull for each structure across sampled U values.

        Structures are expected to provide:
            - structure.AtomPositionManager.E : total energy (eV)
            - structure.AtomPositionManager.latticeVectors : (3,3) array for cell vectors
        """

        # 1) Unique labels: hard coded for application
        #unique_labels = ['H','O','Cu']

        # 2) Build composition matrix X and energy array y
        N = len(dataset)

        # Fill composition counts and energies
        y = dataset.get_all_energies()

        species, species_order = dataset.get_all_compositions(return_species=True)
        mapping = dataset.get_species_mapping(order="stored")
        idx = np.fromiter((mapping.get(lbl, -1) for lbl in unique_labels), dtype=int, count=len(unique_labels))
        valid = (idx >= 0)
        X = np.zeros((species.shape[0], len(unique_labels)), dtype=species.dtype)
        if np.any(valid):
            X[:, valid] = species[:, idx[valid]]

        # 3) CHE adjustment Adjust for mu_O = mu_H2O - 2mu_H
        X[:,unique_labels_dict['H']] -= 2*X[:,unique_labels_dict['O']]

        # Reference chemical potentials for fixed species
        base_mu = np.array([reference_potentials.get(lbl, 0.0) for lbl in unique_labels])
        base_mu[ unique_labels_dict['O'] ] = reference_potentials.get('H2O', 0.0)

        # Formation energy reference
        fE_ref = y - X.dot(base_mu)
        nH = X[:, unique_labels_dict['H']]

        # Sample H potentials
        H_values = np.linspace(H_range[0], H_range[1], steps)

        # Vectorized formation energies
        fE_array = fE_ref[:, None] - nH[:, None]*H_values[None, :]
        fE_hull = fE_array.min(axis=0)
        min_distances = (fE_array - fE_hull).min(axis=1)

        return min_distances

    return compute

def objective_min_distance_to_O_hull(
    reference_potentials: dict,
    mu_range: tuple = (-1.0, 0.5),
    steps: int = 100,
    unique_labels: list = None,
):
    """
    Objective function for GA: minimal distance of each structure to the convex hull
    across a range of applied electrochemical potentials (U).

    The electron chemical potential is varied via the CHE formalism:
        mu_e(U) = - e * U + pH- and p_H2-dependent terms.

    Parameters
    ----------
    reference_potentials : dict
        Dictionary of fixed chemical potentials, e.g. {'Cu': -3.5, 'O': -4.2, 'H2O': -14.25}.
        These are constants and serve as the baseline for non-variable species.
    mu_range : tuple
        (H_min, H_max) range of O chemical potential.
    steps : int
        Number of discrete U values to sample between H_min and H_max.

    Returns
    -------
    compute : callable
        Function that, when called with a list of structures, returns
        min_distances: np.ndarray of shape (N_structs,)
            Minimum energy distance to convex hull for each structure across U_range.
    by: Felix Riccius
    """
    unique_labels = {lbl for lbl in reference_potentials.keys()}
    unique_labels_dict = { u:i for i, u in enumerate(unique_labels) }
    M = len(unique_labels)

    def compute(dataset):
        """
        Compute min distance to convex hull for each structure across sampled U values.

        Structures are expected to provide:
            - structure.AtomPositionManager.E : total energy (eV)
            - structure.AtomPositionManager.latticeVectors : (3,3) array for cell vectors
        """

        # Fill composition counts and energies
        y = dataset.get_all_energies()

        species, species_order = dataset.get_all_compositions(return_species=True)
        mapping = dataset.get_species_mapping(order="stored")
        idx = np.fromiter((mapping.get(lbl, -1) for lbl in unique_labels), dtype=int, count=len(unique_labels))
        valid = (idx >= 0)
        X = np.zeros((species.shape[0], len(unique_labels)), dtype=species.dtype)
        if np.any(valid):
            X[:, valid] = species[:, idx[valid]]

        # Reference chemical potentials for fixed species
        base_mu = np.array([reference_potentials.get(lbl, 0.0) for lbl in unique_labels])

        # Formation energy reference
        fE_ref = y - X.dot(base_mu)
        nO = X[:, unique_labels_dict['O']]

        # Sample H potentials
        mu_values = np.linspace(mu_range[0], mu_range[1], steps)

        # Vectorized formation energies
        fE_array = fE_ref[:, None] - nO[:, None]*mu_values[None, :]
        fE_hull = fE_array.min(axis=0)
        min_distances = (fE_array - fE_hull).min(axis=1)

        return min_distances

    return compute

def objective_integral():
    """
    """

    def compute(dataset):
        """
        """
        vals = dataset.get_all_metadata('integral')

        # Replace None with 0
        clean = np.array([0.0 if v is None else v for v in vals], dtype=float)

        res = -np.nan_to_num(clean, nan=0.0)
        return res

    return compute

def objective_min_distance_to_electrochemicalhull_NiLDH(
    reference_potentials: dict,
    U_range: tuple = (0.0, 1.8),
    pH: float = 13.0,
    steps: int = 100,
    unique_labels: list[str] | None = None,
):
    """
    Approximate and efficient objective function:
    minimal distance of each Ni–Fe LDH structure to an electrochemical convex hull
    across a range of applied potentials (U), using a CHE-like formalism.

    This avoids recomputing convex hulls for each potential (vectorized instead).

    The effective H and O chemical potentials are:
        μ_H(U, pH) = ½·G_H2 - e·U + k_B·T·ln(10)·pH
        μ_O(U, pH) = G_H2O - 2·μ_H(U, pH)

    Parameters
    ----------
    reference_potentials : dict
        Reference chemical potentials in eV for fixed species, e.g.:
        {
            'Ni': -5.0, 'Fe': -5.2, 'V': -5.0, 'K': -11.65,
            'H2O': -14.2, 'H2': -7.01
        }
    U_range : tuple
        (U_min, U_max) range of applied potentials in eV.
    pH : float
        Electrochemical pH (default 14.0).
    steps : int
        Number of potential points sampled between U_min and U_max.
    unique_labels : list[str], optional
        Species order. If None, inferred from dataset.

    Returns
    -------
    compute : callable
        Function that, when called with a dataset, returns:
            np.ndarray of shape (N_structures,)
            Minimum energy distance to electrochemical hull.
    """
    import numpy as np
    from scipy.constants import Boltzmann, elementary_charge

    # constants
    kT = Boltzmann * 298.15 / elementary_charge  # eV

    # reference species
    mu_H2 = reference_potentials.get("H2", -7.01)
    mu_H2O = reference_potentials.get("H2O", -14.2)

    # potential-dependent functions
    def mu_H(U):
        return 0.5 * mu_H2 - U + kT * np.log(10) * pH

    def mu_O(U):
        return mu_H2O - 2 * mu_H(U)

    U_values = np.linspace(*U_range, steps)

    # derive the full set of species
    if unique_labels is None:
        unique_labels = list(reference_potentials.keys())

    unique_labels_dict = {u: i for i, u in enumerate(unique_labels)}
    M = len(unique_labels)

    def compute(dataset):
        """
        Compute minimal electrochemical distance for all structures.
        """
        y = dataset.get_all_energies()

        # compositions and ordering
        species, species_order = dataset.get_all_compositions(return_species=True)
        mapping = dataset.get_species_mapping(order="stored")

        idx = np.fromiter(
            (mapping.get(lbl, -1) for lbl in unique_labels), dtype=int, count=M
        )
        valid = idx >= 0

        X = np.zeros((species.shape[0], M), dtype=float)
        if np.any(valid):
            X[:, valid] = species[:, idx[valid]]

        # base reference μ for fixed elements
        base_mu = np.array([reference_potentials.get(lbl, 0.0) for lbl in unique_labels])

        # remove the variable ones (H and O)
        base_mu[unique_labels_dict.get("H", -1)] = 0.0
        base_mu[unique_labels_dict.get("O", -1)] = 0.0

        # formation energy baseline
        fE_ref = y - X.dot(base_mu)

        # atom counts
        nH = X[:, unique_labels_dict.get("H", 0)]
        nO = X[:, unique_labels_dict.get("O", 0)]

        # precompute μ_H(U), μ_O(U)
        muH_values = mu_H(U_values)
        muO_values = mu_O(U_values)

        # vectorized total formation energies
        fE_array = fE_ref[:, None] - nH[:, None] * muH_values[None, :] - nO[:, None] * muO_values[None, :]

        # "convex hull" approximation — minimal energy per U
        fE_hull = fE_array.min(axis=0)
        min_distances = (fE_array - fE_hull).min(axis=1)

        return min_distances

    return compute

objectives = [objective_min_distance_to_electrochemicalhull_NiLDH(
        reference_potentials={
            'Ni': -5.0, 'Fe': -5.2, 'V': -5.0, 'K': -11.65,
            'H2O': -14.2, 'H2': -7.01
        }
    )]


# === TEST ===
if __name__ == "__main__":
    from sage_lib.partition.Partition import Partition
    import time

    partition = Partition()
    partition.read_files('/Users/dimitry/Documents/Data/EZGA/9-superhero/sampling/config_884.xyz')
    objectives = objective_min_distance_to_electrochemicalhull(
        reference_potentials={'Cu':0, 'O':0, 'H':1}
    )

    start = time.time()
    for n in range(50):
        objectives(partition.containers)

    end = time.time()
    print(f"Elapsed time: {end - start:.6f} seconds")





