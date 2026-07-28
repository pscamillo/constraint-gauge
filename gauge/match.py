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


def _nearest(query_xyz, points_xyz, tau):
    """Nearest adapter point within tau for each query. Brute force is
    fine at these sizes (hundreds of GT points, tens of thousands of
    seeds); swap in a KD-tree only if it ever matters."""
    q = np.asarray(query_xyz)[:, None, :]          # (Q, 1, 3)
    d2 = ((q - points_xyz[None, :, :]) ** 2).sum(-1)
    idx = np.argmin(d2, axis=1)                    # smallest index on ties
    dist = np.sqrt(d2[np.arange(len(q)), idx])
    ok = dist <= tau
    return np.where(ok, idx, -1), np.where(ok, dist, np.inf)


def match(gt_xyz, pairs, adapter, tau):
    a_pt, a_d = _nearest(gt_xyz[pairs["a"]], adapter.points_xyz, tau)
    b_pt, b_d = _nearest(gt_xyz[pairs["b"]], adapter.points_xyz, tau)
    scorable = (a_pt >= 0) & (b_pt >= 0)
    return MatchResult(scorable, a_pt, b_pt, a_d, b_d)
