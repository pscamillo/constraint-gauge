"""gauge.density - can this generator be scored at all? (addendum A10)

Per-location scoring asks which sheet a point sits on. A generator can
only answer that where it emits nodes finer than the sheets themselves.
If the typical distance between neighbouring generator nodes exceeds
the local sheet spacing, then a ground-truth point has no node of its
own: the nearest node belongs to a neighbouring sheet, and the reported
winding difference is arbitrary regardless of how good the generator's
internal solution is.

The gate is therefore a PRECONDITION, not a metric:

    node_gap  = median distance to the nearest other generator node
    sheet_gap = median A2.2 spacing of the GT in the same region
                (twice the measured tolerance)
    ratio     = node_gap / sheet_gap

ratio < 1 means the generator resolves individual sheets and scoring is
meaningful. ratio >= 1 means it does not, and the run is reported as
NOT SCORABLE with the ratio, rather than as a low score. The
distinction matters: a low score is a statement about the generator's
accuracy, and this is not one.

Discovered on winding-sync v0.2.0, whose TracingConfig.seed_stride_um
is 260 um by design while PHerc Paris 4 sheets sit about 180 um apart.
"""

import numpy as np


def node_gap_vox(points_xyz, planar=False, sample=20000, seed=1):
    """Median nearest-neighbour distance among generator nodes."""
    P = np.asarray(points_xyz, dtype=float)
    if planar:
        P = P[:, :2]
    if len(P) < 3:
        return float("nan")
    if len(P) > sample:
        sel = np.random.default_rng(seed).choice(len(P), sample,
                                                 replace=False)
        P = P[sel]
    try:
        from scipy.spatial import cKDTree
        d, _ = cKDTree(P).query(P, k=2, workers=-1)
        return float(np.median(d[:, 1]))
    except ImportError:
        d2 = ((P[:, None, :] - P[None, :, :]) ** 2).sum(-1)
        np.fill_diagonal(d2, np.inf)
        return float(np.median(np.sqrt(d2.min(axis=1))))


def check(points_xyz, tau_gt, planar=False, limit=1.0):
    """Return (scorable, info). tau_gt is the per-point A2.2 tolerance
    of the ground truth in the scored region; sheet_gap is twice its
    median."""
    ng = node_gap_vox(points_xyz, planar=planar)
    t = np.asarray(tau_gt, dtype=float)
    t = t[np.isfinite(t)]
    sg = 2.0 * float(np.median(t)) if len(t) else float("nan")
    ratio = ng / sg if sg > 0 else float("nan")
    ok = bool(np.isfinite(ratio) and ratio < limit)
    return ok, {"node_gap_vox": ng, "sheet_gap_vox": sg,
                "ratio": ratio, "limit": limit, "scorable": ok}
