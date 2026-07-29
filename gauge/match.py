"""gauge.match - annotation-to-point matching, GATE0 section 3 (sealed).

The tolerance rule in force is A2.2: tau measured at each GT point as
half the distance to its nearest adjacent-winding neighbour, with the
A2.1 radial table and then the 3.3 median as fallbacks (tightest wins).
The sealed 3.3 text is kept below for the record:
tau = 0.5 x median pitch of the scroll, in voxels of the measured level
(section 3.3). A GT pair (A, B) is SCORABLE iff both endpoints
have an adapter point within tau (euclidean, full-res voxels). Nearest
neighbour; ties broken by smaller distance then smaller index (3.5,
deterministic). Non-scorable pairs count in COVERAGE only (3.4).
Sensitivity at tau/2 and 2*tau is diagnostic, never primary (3.6).
"""

from dataclasses import dataclass

import numpy as np


def tau_vox(pitch_um, um_per_vox):
    return 0.5 * pitch_um / um_per_vox


@dataclass
class MatchResult:
    scorable: np.ndarray      # (P,) bool per GT pair
    a_pt: np.ndarray          # (P,) adapter point index for A (-1 if none)
    b_pt: np.ndarray
    a_dist: np.ndarray        # (P,) match distance in voxels (inf if none)
    b_dist: np.ndarray


def _nearest(query_xyz, points_xyz, tau, chunk=20000):
    """Nearest adapter point within tau for each query. tau may be a
    scalar or a per-query array (A2.1/A2.2 local tau).

    Uses a KD-tree when scipy is available: mesh arms reach hundreds of
    thousands of points, where materializing pairwise distances is not
    viable. Falls back to chunked brute force otherwise, with the same
    tie-breaking (smallest index) in both paths.
    """
    q = np.asarray(query_xyz, dtype=np.float64)
    P = np.asarray(points_xyz, dtype=np.float64)
    tau = np.asarray(tau, dtype=np.float64)
    tau_arr = tau if tau.ndim else np.full(len(q), float(tau))

    try:
        from scipy.spatial import cKDTree
    except ImportError:
        cKDTree = None

    if cKDTree is not None:
        tree = cKDTree(P)
        dist, idx = tree.query(q, k=1, workers=-1)
        ok = dist <= tau_arr
        return np.where(ok, idx, -1), np.where(ok, dist, np.inf)

    idx = np.empty(len(q), dtype=int)
    dist = np.empty(len(q))
    for a in range(0, len(q), chunk):
        b = min(a + chunk, len(q))
        d2 = ((q[a:b, None, :] - P[None, :, :]) ** 2).sum(-1)
        i = np.argmin(d2, axis=1)
        idx[a:b] = i
        dist[a:b] = np.sqrt(d2[np.arange(b - a), i])
    ok = dist <= tau_arr
    return np.where(ok, idx, -1), np.where(ok, dist, np.inf)


def match(gt_xyz, pairs, adapter, tau, planar=False):
    """tau: scalar (3.3) or per-GT-point array indexed like gt_xyz
    (A2.1/A2.2). With an array, each pair endpoint uses its own
    tolerance.

    planar=True is for adapters that exist on a single z plane (a
    slice-based generator, addendum A9). The GT is a 3D cloud, so
    almost no GT point falls exactly on the plane and 3D distance would
    spend the whole tolerance on the z offset. In planar mode a GT
    point is eligible if |z_gt - z_plane| <= its own tau, and matching
    then uses in-plane (x, y) distance against the same tau. The slab
    thickness is therefore not a free parameter: it is the same
    tolerance that governs matching everywhere else.
    """
    tau = np.asarray(tau)
    tau_a = tau if tau.ndim == 0 else tau[pairs["a"]]
    tau_b = tau if tau.ndim == 0 else tau[pairs["b"]]
    P = adapter.points_xyz
    if planar:
        zs = np.unique(np.round(P[:, 2], 3))
        if len(zs) != 1:
            raise ValueError(f"planar matching needs a single-plane "
                             f"adapter; got {len(zs)} distinct z")
        z_plane = float(zs[0])
        A = gt_xyz[pairs["a"]].copy()
        B = gt_xyz[pairs["b"]].copy()
        in_a = np.abs(A[:, 2] - z_plane) <= tau_a
        in_b = np.abs(B[:, 2] - z_plane) <= tau_b
        A[:, 2] = z_plane
        B[:, 2] = z_plane
        a_pt, a_d = _nearest(A, P, tau_a)
        b_pt, b_d = _nearest(B, P, tau_b)
        a_pt = np.where(in_a, a_pt, -1)
        b_pt = np.where(in_b, b_pt, -1)
        a_d = np.where(in_a, a_d, np.inf)
        b_d = np.where(in_b, b_d, np.inf)
    else:
        a_pt, a_d = _nearest(gt_xyz[pairs["a"]], P, tau_a)
        b_pt, b_d = _nearest(gt_xyz[pairs["b"]], P, tau_b)
    scorable = (a_pt >= 0) & (b_pt >= 0)
    return MatchResult(scorable, a_pt, b_pt, a_d, b_d)
