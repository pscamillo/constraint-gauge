"""gauge.match - annotation-to-point matching, GATE0 section 3 (sealed).

tau = 0.5 x median pitch of the scroll, in voxels of the measured level
(section 3.3, fixed). A GT pair (A, B) is SCORABLE iff both endpoints
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


def _nearest(query_xyz, points_xyz, tau, chunk=2000):
    """Nearest adapter point within tau for each query. tau may be a
    scalar or a per-query array (A2.1 local tau). Chunked brute force:
    memory stays bounded at chunk x N."""
    q = np.asarray(query_xyz)
    tau = np.asarray(tau)
    idx = np.empty(len(q), dtype=int)
    dist = np.empty(len(q))
    for a in range(0, len(q), chunk):
        b = min(a + chunk, len(q))
        d2 = ((q[a:b, None, :] - points_xyz[None, :, :]) ** 2).sum(-1)
        i = np.argmin(d2, axis=1)              # smallest index on ties
        idx[a:b] = i
        dist[a:b] = np.sqrt(d2[np.arange(b - a), i])
    ok = dist <= (tau if tau.ndim else np.full(len(q), float(tau)))
    return np.where(ok, idx, -1), np.where(ok, dist, np.inf)


def match(gt_xyz, pairs, adapter, tau):
    """tau: scalar (3.3) or per-GT-point array indexed like gt_xyz
    (A2.1). With an array, each pair endpoint uses its own tolerance."""
    tau = np.asarray(tau)
    tau_a = tau if tau.ndim == 0 else tau[pairs["a"]]
    tau_b = tau if tau.ndim == 0 else tau[pairs["b"]]
    a_pt, a_d = _nearest(gt_xyz[pairs["a"]], adapter.points_xyz, tau_a)
    b_pt, b_d = _nearest(gt_xyz[pairs["b"]], adapter.points_xyz, tau_b)
    scorable = (a_pt >= 0) & (b_pt >= 0)
    return MatchResult(scorable, a_pt, b_pt, a_d, b_d)
