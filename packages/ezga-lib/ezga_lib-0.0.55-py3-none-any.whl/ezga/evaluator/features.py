import numpy as np
from scipy.spatial.distance import pdist
from scipy.spatial import ConvexHull

def evaluate_features(structures, features_funcs):
    """
    Evaluates the given list of structures using a user-supplied feature extractor function.

    Parameters
    ----------
    structures : list
        List of structures to evaluate.
    features_funcs : callable
        A function or callable that, given a list of structures,
        returns an (N, D) array of features.

    Returns
    -------
    np.ndarray
        (N, D) array of feature vectors, one row per structure.
    """
    return np.array([features_funcs(structure) for structure in structures])

# ------------------------------------------------------------
# Composition Vector Feature
# ------------------------------------------------------------
def feature_composition_vector(IDs):
    """
    Returns a function that computes the composition vector for a given structure.
    The vector contains counts for each unique atom label present in the structure.
    
    Returns
    -------
    callable
        A function that accepts a structure and returns a 1D numpy array with the atom counts.
    """
    def get_feature_index_map():
        return { label: idx for idx, label in enumerate(IDs) }

    def compute(dataset):

        M, species_order = dataset.get_all_compositions(return_species=True)
        mapping = dataset.get_species_mapping(order="stored")

        # Build index array for requested IDs; -1 means "missing"
        idx = np.fromiter((mapping.get(lbl, -1) for lbl in IDs), dtype=int, count=len(IDs))
        valid = (idx >= 0)

        counts = np.zeros((M.shape[0], len(IDs)), dtype=M.dtype)
        if np.any(valid):
            counts[:, valid] = M[:, idx[valid]]

        return counts

    compute.get_feature_index_map = get_feature_index_map

    return compute

def feature_total_atoms():
    """
    For each structure, returns the total number of atoms.

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 1)
    """
    def get_feature_index_map():
        return {'N': 0}

    def compute(dataset):
        n = len(dataset)
        out = np.zeros((n, 1), dtype=float)
        for i in range(n):
            _, _, _, elements, *_ = dataset[i]
            out[i, 0] = float(len(elements))
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


def feature_unique_atom_count():
    """
    For each structure, returns the number of unique element types.

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 1)
    """
    def get_feature_index_map():
        return {'N': 0}

    def compute(dataset):
        n = len(dataset)
        out = np.zeros((n, 1), dtype=float)
        for i in range(n):
            _, _, _, elements, *_ = dataset[i]
            out[i, 0] = float(len(np.unique(elements)))
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


def feature_average_interatomic_distance():
    """
    For each structure, computes the average pairwise Euclidean distance
    between atoms.

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 1)
    """
    def get_feature_index_map():
        return {'avg_d': 0}

    def compute(dataset):
        n = len(dataset)
        out = np.zeros((n, 1), dtype=float)
        for i in range(n):
            positions, *_ = dataset[i]
            if positions.shape[0] < 2:
                out[i, 0] = 0.0
            else:
                dists = pdist(positions, metric='euclidean')
                out[i, 0] = float(np.mean(dists))
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


def feature_radius_of_gyration():
    """
    For each structure, computes the radius of gyration (R_g),
    defined as the RMS distance from the center of mass.

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 1)
    """
    def get_feature_index_map():
        return {'Rg': 0}

    def compute(dataset):
        n = len(dataset)
        out = np.zeros((n, 1), dtype=float)
        for i in range(n):
            positions, *_ = dataset[i]
            if positions.shape[0] == 0:
                out[i, 0] = 0.0
                continue
            com = np.mean(positions, axis=0)
            rg = np.sqrt(np.mean(np.sum((positions - com) ** 2, axis=1)))
            out[i, 0] = float(rg)
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


def feature_center_of_mass():
    """
    For each structure, computes the geometric center of mass (simple
    average of atomic positions; no mass weighting).

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 3)
    """
    def get_feature_index_map():
        return {'com_x': 0, 'com_y': 1, 'com_z': 2}

    def compute(dataset):
        n = dataset.size
        out = np.zeros((n, 3), dtype=float)
        for s in dataset:
            positions = s.AtomPositionManager.atomPositions
            if positions.shape[0] == 0:
                out[i, :] = 0.0
            else:
                out[i, :] = np.mean(positions, axis=0)
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


def feature_minimum_interatomic_distance():
    """
    For each structure, computes the minimum interatomic distance.

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 1)
    """
    def get_feature_index_map():
        return {'d_min': 0}

    def compute(dataset):
        n = len(dataset)
        out = np.zeros((n, 1), dtype=float)
        for i in range(n):
            positions, *_ = dataset[i]
            if positions.shape[0] < 2:
                out[i, 0] = 0.0
            else:
                dists = pdist(positions, metric='euclidean')
                out[i, 0] = float(np.min(dists))
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


def feature_convex_hull_volume():
    """
    For each structure, computes the volume of the convex hull of atomic
    positions. If the points are coplanar/collinear or hull construction
    fails, returns 0.

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 1)
    """
    def get_feature_index_map():
        return {'V_hull': 0}

    def compute(dataset):
        n = len(dataset)
        out = np.zeros((n, 1), dtype=float)
        for i in range(n):
            positions, *_ = dataset[i]
            if positions.shape[0] < 4:
                out[i, 0] = 0.0
                continue
            try:
                hull = ConvexHull(positions)
                out[i, 0] = float(hull.volume)
            except Exception:
                out[i, 0] = 0.0
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


def feature_cell_volume():
    """
    For each structure, computes the volume of the simulation cell as
    |det(lattice)|, where lattice is a 3x3 matrix of lattice vectors.

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 1)
    """
    def get_feature_index_map():
        return {'V_cell': 0}

    def compute(dataset):
        n = len(dataset)
        out = np.zeros((n, 1), dtype=float)
        for i in range(n):
            _, lattice, *_ = dataset[i]
            try:
                vol = float(abs(np.linalg.det(lattice)))
            except Exception:
                vol = 0.0
            out[i, 0] = vol
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


def feature_density():
    """
    For each structure, computes an approximate density defined as:
        ρ = N_atoms / V_cell

    Returns
    -------
    callable
        compute(dataset) -> shape (N_structures, 1)
    """
    def get_feature_index_map():
        return {'rho': 0}

    def compute(dataset):
        n = len(dataset)
        out = np.zeros((n, 1), dtype=float)
        for i in range(n):
            _, lattice, _, elements, *_ = dataset[i]
            N = len(elements)
            try:
                vol = float(abs(np.linalg.det(lattice)))
            except Exception:
                vol = 0.0
            if vol <= 0.0:
                out[i, 0] = 0.0
            else:
                out[i, 0] = float(N) / vol
        return out

    compute.get_feature_index_map = get_feature_index_map
    return compute


'''
provider = PartitionProvider(partition)  # your adapter

feat_funcs = [
    feature_total_atoms(),
    feature_unique_atom_count(),
    feature_average_interatomic_distance(),
    feature_cell_volume(),
    feature_density(),
]

X = evaluate_features(provider, feat_funcs)
print("Feature matrix shape:", X.shape)
'''
