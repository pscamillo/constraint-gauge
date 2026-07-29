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
    """Median nearest-neighbour distance among DISTINCT generator nodes.

    Deduplication matters: a generator laying nodes on a coarse grid
    puts several of them at the same coordinate, and the nearest
    neighbour of a duplicate is at distance zero. Without this the
    measure collapses as the grid gets coarser, which is the opposite of
    the truth (observed at grid 40: 2173 nodes, 1215 distinct, reported
    gap 1.6 vox against a real spacing of 40).
    """
    P = np.asarray(points_xyz, dtype=float)
    if planar:
        P = P[:, :2]
    P = np.unique(np.round(P, 6), axis=0)
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


def check(points_xyz, tau_gt, planar=False, limit=1.0, gt_xyz=None):
    """Return (scorable, info). tau_gt is the per-point A2.2 tolerance
    of the ground truth in the scored region; sheet_gap is twice its
    median. gt_xyz is accepted and ignored: an earlier attempt to
    exempt adapters that predict on the GT points was reverted, since
    the case it was written for turned out not to occur (A18).
    """
    ng = node_gap_vox(points_xyz, planar=planar)
    t = np.asarray(tau_gt, dtype=float)
    t = t[np.isfinite(t)]
    sg = 2.0 * float(np.median(t)) if len(t) else float("nan")
    ratio = ng / sg if sg > 0 else float("nan")
    ok = bool(np.isfinite(ratio) and ratio < limit)
    return ok, {"node_gap_vox": ng, "sheet_gap_vox": sg,
                "ratio": ratio, "limit": limit, "scorable": ok}
