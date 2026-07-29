"""gauge.meshgt - ground truth pairs from human-verified segment meshes
(addendum A3.1).

Why meshes: a verified multi-wrap segment states sheet identity by
construction — every grid point lies on ONE continuous sheet, and wraps
are adjacent windings. Dense, continuous, and exactly the GT sean and
Paul argued for.

Axis-free winding assignment (honoring A2.2's constraint: no axis, no
spacing constant, no radial model). Along the mid row of the arc axis,
walk a SELF-PROXIMITY CHAIN: from the current node, the next node is
the nearest point in 3D among those further than an arc guard along the
row. By construction that partner sits one wrap outward, so chain nodes
mark full wraps and winding(u) = index of the chain interval containing
u. The mesh counts its own turns.

Overlap handling (sean's warning): GP segments overlap their neighbors
at the seam, so (a) each mesh is its own collection — cross-mesh pairs
never exist — and (b) the first and last wraps are trimmed by default.
The merged 1667 tifxyz has no seam and can run with trim=0.

Coordinates are in the frame of the volume the mesh is registered on
(the "-on-<volume>-<um>" in the tifxyz dirname). Adapters are scored in
the same frame; no cross-frame comparison is attempted here.
"""

import os

import numpy as np
import tifffile


def _load_tifxyz(mesh_dir):
    x = tifffile.imread(os.path.join(mesh_dir, "x.tif")).astype(np.float64)
    y = tifffile.imread(os.path.join(mesh_dir, "y.tif")).astype(np.float64)
    z = tifffile.imread(os.path.join(mesh_dir, "z.tif")).astype(np.float64)
    valid = np.isfinite(z) & (z > 0)
    return x, y, z, valid


def _arc_axis(x, y, z, valid):
    """1 if the arc (long) direction is axis 1 (columns), else 0."""
    def path_len(axis):
        dx = np.diff(x, axis=axis)
        dy = np.diff(y, axis=axis)
        dz = np.diff(z, axis=axis)
        m = valid.take(range(valid.shape[axis] - 1), axis=axis) & \
            valid.take(range(1, valid.shape[axis]), axis=axis)
        return float(np.sqrt(dx**2 + dy**2 + dz**2)[m].sum())
    return 1 if path_len(1) >= path_len(0) else 0


def _wrap_chain(row_xyz, s, guard_vox):
    """Chain of wrap crossings along one row.

    A true wrap return has two signatures at once: the chord has come
    back DOWN to sheet-spacing scale, and the point has wrapped (chord
    much shorter than arc). Both are self-derived, no spacing constant:
    the global minimum of the chord ahead IS a measurement of the local
    sheet spacing, so a return is any point with

        chord <= 5 x (min chord ahead)   and   chord < 0.5 x arc

    beyond the grid-neighbor guard. The next node is the argmin of the
    chord inside the FIRST contiguous run of that mask: the earliest
    genuine return, immune both to far-end drift (which fooled a global
    argmin) and to early chord/arc triggers at ~0.6 turn (excluded by
    the depth criterion, chord there is still diameter-scale).
    """
    chain = [0]
    n = len(s)
    while True:
        i = chain[-1]
        d = np.linalg.norm(row_xyz[i + 1:] - row_xyz[i], axis=1)
        ds = s[i + 1:] - s[i]
        ahead = ds > guard_vox
        if not ahead.any():
            break
        dmin = d[ahead].min()
        mask = ahead & (d <= 5.0 * dmin) & (d < 0.5 * ds)
        idx = np.nonzero(mask)[0]
        if idx.size == 0:
            break
        gaps = np.nonzero(np.diff(idx) > 1)[0]
        run0 = idx[:gaps[0] + 1] if gaps.size else idx
        chain.append(i + 1 + int(run0[np.argmin(d[run0])]))
    return chain


def _row_chain(x, y, z, valid, v, guard_vox):
    """Run the chain on grid row v; returns (cols, chain, arcs)."""
    cols = np.nonzero(valid[v])[0]
    if len(cols) < 3:
        return cols, [0], np.empty(0)
    row = np.column_stack([x[v, cols], y[v, cols], z[v, cols]])
    seg = np.linalg.norm(np.diff(row, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    chain = _wrap_chain(row, s, guard_vox)
    arcs = np.diff(s[np.asarray(chain)]) if len(chain) > 1 else np.empty(0)
    return cols, chain, arcs


def load_mesh_gt(mesh_dir, stride=8, guard_vox=None, trim_wraps=1,
                 collection=None):
    """Extract (xyz, wind, coll) from a verified tifxyz segment.

    stride      grid subsampling for emitted points (cells)
    guard_vox   minimum arc length before the chain may close a wrap;
                default 10x the grid step (from meta scale, step =
                1/scale voxels)
    trim_wraps  wraps dropped at each end (seam overlap guard)
    collection  id string; defaults to the mesh dirname

    Returns arrays shaped like gauge.gt.load_points, so build_pairs and
    the whole scoring pipeline work unchanged.
    """
    import json
    x, y, z, valid = _load_tifxyz(mesh_dir)
    meta = json.load(open(os.path.join(mesh_dir, "meta.json")))
    step_vox = 1.0 / float(meta["scale"][0])
    if guard_vox is None:
        guard_vox = 10.0 * step_vox

    if _arc_axis(x, y, z, valid) == 0:      # normalize: arc along axis 1
        x, y, z, valid = x.T, y.T, z.T, valid.T
    V, U = z.shape

    # multi-row consensus: run the chain on up to 5 well-covered rows,
    # modal wrap count wins, best row of the modal count gives the
    # boundaries. A fold that fools one row does not fool five heights.
    counts = valid.sum(axis=1)
    good = np.nonzero(counts >= 0.5 * counts.max())[0]
    picks = good[np.linspace(0, len(good) - 1, min(5, len(good))).astype(int)]
    results = []
    for v in picks:
        cols_v, chain_v, arcs_v = _row_chain(x, y, z, valid, v, guard_vox)
        results.append((v, cols_v, chain_v, arcs_v))
    row_counts = [len(c) - 1 for _, _, c, _ in results]
    vals, freq = np.unique(row_counts, return_counts=True)
    modal = int(vals[np.argmax(freq)])
    cands = [r for r, rc in zip(results, row_counts) if rc == modal]
    vmid, cols, chain, arcs_mid = max(cands, key=lambda r: len(r[1]))
    n_wraps = modal
    if n_wraps < 2 * trim_wraps + 1:
        raise ValueError(f"only {n_wraps} wraps found; lower trim/guard")

    # winding index per u column: interval of the chain containing it
    bounds_u = cols[chain]                     # u index of each wrap start
    wind_of_u = np.searchsorted(bounds_u, np.arange(U), side="right") - 1

    # sample grid points, trim seam wraps
    vs = np.arange(0, V, stride)
    us = np.arange(0, U, stride)
    gv, gu = np.meshgrid(vs, us, indexing="ij")
    keep = valid[gv, gu]
    w = wind_of_u[gu]
    keep &= (w >= trim_wraps) & (w <= n_wraps - 1 - trim_wraps)

    xyz = np.column_stack([x[gv, gu][keep], y[gv, gu][keep],
                           z[gv, gu][keep]])
    wind = w[keep].astype(np.float64)
    cid = collection or os.path.basename(os.path.normpath(mesh_dir))
    coll = np.array([cid] * len(wind), dtype=object)
    info = {"n_wraps": n_wraps, "trimmed": trim_wraps,
            "wrap_arc_vox": arcs_mid.tolist(),
            "row_wrap_counts": row_counts,
            "points": int(keep.sum())}
    return xyz, wind, coll, info


def mesh_spacing_um(mesh_dir, um_per_vox, stride_v=4, stride_u=4,
                    trim_wraps=1):
    """Perpendicular sheet spacing measured directly from a mesh
    (addendum A6.3).

    The grid samples each wrap densely along u (one grid step, 20 vox
    on the GP meshes) compared with the gap between wraps (60-100 vox),
    so the distance from a point on wrap k to the CURVE of wrap k+1 at
    the same height v is the perpendicular spacing, with second-order
    error only: a foot point falling between two samples inflates the
    measurement by step^2/(8 d^2), about 1.3% at these scales, always
    upward. No density extrapolation and no axis: the parametrization
    supplies the wrap-to-wrap correspondence.

    Note the contrast with the annotated arm, where sampling is sparser
    than the gap and the same estimator needs the A6.1 convergence
    treatment.

    Returns (spacings_um, info) with one measurement per sampled cell.
    """
    import json
    try:
        from scipy.spatial import cKDTree
    except ImportError:
        cKDTree = None
    x, y, z, valid = _load_tifxyz(mesh_dir)
    meta = json.load(open(os.path.join(mesh_dir, "meta.json")))
    step_vox = 1.0 / float(meta["scale"][0])
    guard = 10.0 * step_vox
    if _arc_axis(x, y, z, valid) == 0:
        x, y, z, valid = x.T, y.T, z.T, valid.T
    V, U = z.shape

    counts = valid.sum(axis=1)
    good = np.nonzero(counts >= 0.5 * counts.max())[0]
    picks = good[np.linspace(0, len(good) - 1,
                             min(5, len(good))).astype(int)]
    results = [_row_chain(x, y, z, valid, v, guard) for v in picks]
    row_counts = [len(c) - 1 for _, c, _ in results]
    vals, freq = np.unique(row_counts, return_counts=True)
    modal = int(vals[np.argmax(freq)])
    cands = [(v, r) for v, r in zip(picks, results)
             if len(r[1]) - 1 == modal]
    vref, (cols, chain, _) = max(cands, key=lambda t: len(t[1][0]))
    if modal < 2:
        return np.empty(0), {"n_wraps": modal, "n": 0}

    bounds_u = cols[chain]
    out = []
    for k in range(trim_wraps, modal - 1 - trim_wraps + 1):
        ua0, ua1 = bounds_u[k], bounds_u[k + 1]
        ub0, ub1 = bounds_u[k + 1], bounds_u[min(k + 2, modal)]
        if ub1 <= ub0:
            continue
        for v in range(0, V, stride_v):
            ua = np.arange(ua0, ua1, stride_u)
            ua = ua[valid[v, ua]]
            ub = np.arange(ub0, ub1)
            ub = ub[valid[v, ub]]
            if len(ua) < 3 or len(ub) < 3:
                continue
            A = np.column_stack([x[v, ua], y[v, ua], z[v, ua]])
            B = np.column_stack([x[v, ub], y[v, ub], z[v, ub]])
            if cKDTree is not None:
                d, _ = cKDTree(B).query(A, k=1, workers=-1)
            else:
                d = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2
                             ).sum(-1).min(axis=1))
            # drop measurements at the ends of the neighbour curve,
            # where the true foot point may lie outside the sampled span
            keep = (d > 0) & (d < 0.5 * (ua1 - ua0) * step_vox)
            out.append(d[keep])
    if not out or not len(np.concatenate(out)):
        return np.empty(0), {"n_wraps": modal, "n": 0}
    d = np.concatenate(out) * um_per_vox
    return d, {"n_wraps": modal, "n": int(len(d)),
               "median_um": float(np.median(d)),
               "q1_um": float(np.percentile(d, 25)),
               "q3_um": float(np.percentile(d, 75))}
