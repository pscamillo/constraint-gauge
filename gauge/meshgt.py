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
    """Chain of wrap crossings along one row. The next node is the
    nearest-in-3D point among those that have WRAPPED AROUND: chord
    much shorter than arc (chord/arc < 0.5), a scale-free criterion
    with no spacing constant. guard_vox only skips immediate grid
    neighbors."""
    chain = [0]
    while True:
        i = chain[-1]
        ds = s - s[i]
        ahead = ds > guard_vox
        if not ahead.any():
            break
        d = np.linalg.norm(row_xyz - row_xyz[i], axis=1)
        wrapped = ahead & (d < 0.5 * ds)
        if not wrapped.any():
            break
        cand = np.nonzero(wrapped)[0]
        chain.append(int(cand[np.argmin(d[cand])]))
    return chain


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

    # mid valid row for the chain
    counts = valid.sum(axis=1)
    vmid = int(np.argmax(counts))
    cols = np.nonzero(valid[vmid])[0]
    row = np.column_stack([x[vmid, cols], y[vmid, cols], z[vmid, cols]])
    seg = np.linalg.norm(np.diff(row, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])

    chain = _wrap_chain(row, s, guard_vox)
    n_wraps = len(chain) - 1
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
            "wrap_arc_vox": np.diff(s[np.asarray(chain)]).tolist(),
            "points": int(keep.sum())}
    return xyz, wind, coll, info
