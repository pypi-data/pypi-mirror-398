import numpy as np

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

def mutation_promote_rings_wfc_graph(
    target_ring_sizes=(6, 5),
    species_cycle=("Cu", "O"),        # A,B alternation; ring roles even->A, odd->B
    R: float = 4.0,                   # patch radius (Å) in x–y
    frac_z_threshold: float = 0.60,   # top layer fraction (slab along z)
    center_mode: str = "disorder",    # or "random"
    max_backtracks: int = 200,
    max_candidates: int = 64,
    d0_AB: float = 1.95,              # target A–B bond length (Å), e.g. Cu–O
    repel_distance: float = 1.6,      # soft floor for pair distances
    repel_strength: float = 0.5,
    max_steps: int = 30,
    step: float = 0.12,               # morph step per iteration (Å)
    z_anchor_weight: float = 0.05,    # keep local z near patch mean
    seed: int = None,
    cutoffs: dict = None,             # pair cutoffs, overrides below if provided
    verbose: bool = False,
):
    """
    Promote an n-member alternating A–B ring using a Wave-Function-Collapse-like
    constraint solver directly on the local neighbor graph.

    Returns a function(structure)->structure | None.
    """
    rng = np.random.RandomState(seed)

    # --- default cutoffs if not provided ---
    if cutoffs is None:
        cutoffs = {
            (species_cycle[0], species_cycle[1]): (1.60, 2.20),
            (species_cycle[1], species_cycle[0]): (1.60, 2.20),
            # Optional: same-species edges if you want to allow/score them
            (species_cycle[0], species_cycle[0]): (2.60, 3.10),
            (species_cycle[1], species_cycle[1]): (2.50, 3.00),
        }

    A, B = species_cycle

    def _pair_cutoff(a, b):
        return cutoffs.get((a, b), (0.0, np.inf))

    def _dist2(a, b):
        d = a - b
        return float(d[0]*d[0] + d[1]*d[1] + d[2]*d[2])

    def _surface_mask(structure):
        c_len = float(structure.AtomPositionManager.latticeVectors[2, 2])
        z = np.array(structure.AtomPositionManager.atomPositions)[:, 2]
        return z > frac_z_threshold * c_len

    def _neighbors(i, pos, labels):
        """Neighbors by type-dependent max cutoff (undirected, Cu–O edges dominate)."""
        pi = pos[i]
        li = labels[i]
        out = []
        for j in range(len(pos)):
            if j == i: 
                continue
            lj = labels[j]
            rmin, rmax = _pair_cutoff(li, lj)
            if rmax == np.inf:
                continue
            if _dist2(pi, pos[j]) <= rmax * rmax:
                out.append(j)
        return out

    def _cn_and_angle_variance(i, pos, labels):
        """Disorder score: |CN - CN*| + 0.2*angle variance (higher = more disordered)."""
        neigh = _neighbors(i, pos, labels)
        li = labels[i]
        cn_star = 4 if li == A else (2 if li == B else 3)
        cn = len(neigh)
        cn_dev = abs(cn - cn_star)
        if len(neigh) < 2:
            return cn_dev + 1.0
        vi = pos[i]
        vecs = np.array([pos[j] - vi for j in neigh], float)
        norms = np.linalg.norm(vecs, axis=1)
        good = norms > 1e-6
        vecs = vecs[good] / norms[good, None]
        m = len(vecs)
        if m < 2:
            return cn_dev + 1.0
        ang = []
        for a in range(m):
            for b in range(a+1, m):
                c = float(np.clip(np.dot(vecs[a], vecs[b]), -1.0, 1.0))
                ang.append(np.arccos(c))
        ang = np.array(ang)
        var = float(np.var(ang)) if ang.size else 1.0
        return cn_dev + 0.2 * var

    def _choose_center(pos, labels, mask):
        idxs = np.where(mask)[0]
        if idxs.size == 0:
            return None
        if center_mode == "random":
            return int(rng.choice(idxs))
        # disorder-weighted
        sample = idxs[:max_candidates] if idxs.size > max_candidates else idxs
        scores = np.array([_cn_and_angle_variance(i, pos, labels) for i in sample])
        s = scores.sum()
        if s <= 0:
            return int(rng.choice(sample))
        prob = scores / s
        return int(rng.choice(sample, p=prob))

    def _regular_ngon_xy(n, edge, center_xy, phase=0.0):
        rho = edge / (2.0 * np.sin(np.pi / n))
        V = []
        for k in range(n):
            ang = phase + 2.0 * np.pi * k / n
            V.append(center_xy + rho * np.array([np.cos(ang), np.sin(ang)], float))
        return np.array(V)

    def _gauss_weight(r_xy, R):
        return np.exp(-(r_xy * r_xy) / (2.0 * R * R))

    # ---------------- WFC-on-graph core ----------------
    def _wfc_single_ring(graph_nodes, graph_adj, labels_patch, n, offset_parity=0):
        """
        Graph-WFC:
        - Variables = nodes in patch.
        - Domains = {NONE} ∪ {0..n-1}.
        - Even roles require A, odd roles require B (with offset_parity to swap).
        - Edge compatibility: NONE-any, any-NONE, or ring-neighbors (k±1 mod n).
        - Global uniqueness: each ring role used exactly once.
        Returns: (success, role_to_node dict, node_to_role dict)
        """
        Np = len(graph_nodes)
        idx_map = {node: t for t, node in enumerate(graph_nodes)}  # node id -> local idx
        inv_idx = {t: node for node, t in idx_map.items()}

        # Domains
        domains = []
        role_parity = [(k + offset_parity) % 2 for k in range(n)]
        for t in range(Np):
            lab = labels_patch[t]
            # base domain
            dom = {-1}  # -1 => NONE
            # add role k if species parity matches
            for k in range(n):
                if (role_parity[k] == 0 and lab == A) or (role_parity[k] == 1 and lab == B):
                    dom.add(k)
            domains.append(dom)

        # Track role usage uniqueness
        used_role = {k: None for k in range(n)}

        # AC-3 queue
        from collections import deque
        def compatible(a_state, b_state):
            if a_state == -1 or b_state == -1:
                return True
            # must be neighbors along the ring
            return (b_state == (a_state + 1) % n) or (b_state == (a_state - 1 + n) % n)

        def neighbors_local(t):
            node = inv_idx[t]
            return [idx_map[j] for j in graph_adj[node] if j in idx_map]

        def propagate():
            Q = deque([(t, None) for t in range(Np)])  # initialize
            while Q:
                t, _ = Q.popleft()
                Dt = domains[t]
                # if a role is uniquely assigned to t, mark usage
                # (multiple nodes can still have that role in domain until chosen)
                for r in list(Dt):
                    if r != -1 and used_role[r] is not None and used_role[r] != t:
                        # role already claimed elsewhere -> remove
                        if r in Dt:
                            Dt.remove(r)
                            for u in neighbors_local(t):
                                Q.append((u, t))
                            if not Dt:
                                return False
                # arc-consistency
                for u in neighbors_local(t):
                    Du = domains[u]
                    # prune Du by requiring there exists a comp value in Dt
                    pruned = False
                    keep = set()
                    for sv in Du:
                        ok = any(compatible(sv, sw) or compatible(sw, sv) for sw in Dt)
                        if ok:
                            keep.add(sv)
                    if keep != Du:
                        domains[u] = keep
                        pruned = True
                    if not domains[u]:
                        return False
                    if pruned:
                        Q.append((u, t))
            return True

        # Backtracking with entropy heuristic
        def entropy_choice():
            # choose var with smallest domain size >1
            best_t = None
            best_sz = 10**9
            for t, D in enumerate(domains):
                sz = len(D)
                # already decided?
                if sz == 1:
                    continue
                if sz < best_sz:
                    best_sz = sz
                    best_t = t
            return best_t

        # Save/restore helpers
        def snapshot():
            return [set(d) for d in domains], dict(used_role)

        def restore(snap):
            D, U = snap
            for i in range(Np):
                domains[i] = set(D[i])
            for k in range(n):
                used_role[k] = U[k]

        # Ensure feasibility
        if not propagate():
            return False, None, None

        backtracks = 0
        while True:
            t = entropy_choice()
            if t is None:
                # all singleton -> success if every role used exactly once
                node_to_role = {}
                role_to_node = {}
                for i in range(Np):
                    val = next(iter(domains[i]))
                    if val != -1:
                        node_to_role[inv_idx[i]] = val
                        if val in role_to_node:
                            return False, None, None
                        role_to_node[val] = inv_idx[i]
                # did we cover all roles 0..n-1?
                if len(role_to_node) == n:
                    return True, role_to_node, node_to_role
                return False, None, None

            # Branch: try assigning a specific role, with random order
            choices = list(domains[t])
            rng.shuffle(choices)

            progressed = False
            for val in choices:
                snap = snapshot()

                # enforce uniqueness if choosing a ring role
                if val != -1:
                    if used_role[val] is not None and used_role[val] != t:
                        restore(snap); 
                        continue
                    used_role[val] = t
                    # remove this role from all other domains
                    for i in range(Np):
                        if i != t and val in domains[i]:
                            domains[i].remove(val)

                # commit singleton domain at t
                domains[t] = {val}

                if propagate():
                    progressed = True
                    break  # deeper loop

                # revert
                restore(snap)
                backtracks += 1
                if backtracks > max_backtracks:
                    return False, None, None

            if not progressed:
                # dead end
                return False, None, None

    # ---------------- main mutate ----------------
    def func(structure):
        labels_all = np.array(structure.AtomPositionManager.atomLabelsList)
        pos = np.array(structure.AtomPositionManager.atomPositions, float)

        # surface & movable
        surf = _surface_mask(structure)
        movable = pos[:,2] > 10
        mask = surf & movable & np.isin(labels_all, np.array([A, B]))
        center_idx = _choose_center(pos, labels_all, mask)
        if center_idx is None:
            return None

        # patch nodes within R (x–y)
        c_xy = pos[center_idx, :2]
        dxy = np.linalg.norm(pos[:, :2] - c_xy[None, :], axis=1)
        patch_nodes = np.where((dxy <= R) & mask)[0]
        if patch_nodes.size < 4:
            return None

        # adjacency restricted to patch
        adj = {}
        for i in patch_nodes:
            neigh = _neighbors(i, pos, labels_all)
            adj[i] = [j for j in neigh if j in set(patch_nodes)]

        # feasibility per ring size
        labs_patch = labels_all[patch_nodes]
        countA = int(np.sum(labs_patch == A))
        countB = int(np.sum(labs_patch == B))

        # try target sizes (prefer larger first)
        for n in sorted(target_ring_sizes, reverse=True):
            if n % 2 == 1:
                continue
            need = n // 2
            if countA < need or countB < need:
                continue

            # Run graph-WFC (two parity offsets to avoid bias)
            success = False
            for parity in (0, 1):
                ok, role_to_node, node_to_role = _wfc_single_ring(
                    graph_nodes=list(patch_nodes),
                    graph_adj=adj,
                    labels_patch=labs_patch,
                    n=n,
                    offset_parity=parity
                )
                if ok:
                    success = True
                    break
            if not success:
                continue

            # order ring nodes by role
            ring_nodes = [role_to_node[k] for k in range(n)]

            # build target polygon and morph
            Vxy = _regular_ngon_xy(n, d0_AB, c_xy, phase=rng.uniform(0, 2*np.pi))
            # random rotate polygon to avoid bias
            sft = rng.randint(0, n)
            Vxy = np.roll(Vxy, sft, axis=0)

            z_target = np.mean(pos[ring_nodes, 2])
            for _ in range(max_steps):
                # attractions
                for k, i in enumerate(ring_nodes):
                    vi = pos[i]
                    disp_xy = Vxy[k] - vi[:2]
                    r_xy = np.linalg.norm(vi[:2] - c_xy)
                    w = _gauss_weight(r_xy, R)
                    pos[i, 0] += step * w * disp_xy[0]
                    pos[i, 1] += step * w * disp_xy[1]
                    pos[i, 2] += z_anchor_weight * (z_target - vi[2])

                # soft repulsion within ring
                for a in range(n):
                    i = ring_nodes[a]
                    for b in range(a+1, n):
                        j = ring_nodes[b]
                        rij = pos[j] - pos[i]
                        d = np.linalg.norm(rij)
                        if d < 1e-8:
                            continue
                        if d < repel_distance:
                            corr = repel_strength * (repel_distance - d) * rij / d * 0.5
                            pos[i] -= corr
                            pos[j] += corr

            # commit and return
            structure.AtomPositionManager.atomPositions = pos
            if verbose:
                print(f"[WFC-graph] center={center_idx}, n={n}, nodes={ring_nodes}")
            return structure

        # no feasible ring size solved
        return None

    return func
