"""gauge.localtau - radius-dependent matching tolerance (addendum A2.1).

Motivation (A2, Paul Henderson): a tau derived from the scroll's MEDIAN
pitch can cross sheets where packing is tight; local spacing varies ~4x
within a crop. Fix: tau is derived from the LOCAL pitch at each query
point, looked up in a measured radial table, with the median as
fallback where no local measurement exists.

Rule (sealed by addendum A2.1):
    tau(p) = 0.5 * pitch_local(r(p)) / um_per_vox
    r(p)   = in-plane distance from p to the scroll axis, in mm
    axis   = per-scroll config, or "auto" = median (x, y) of GT points
    pitch_local = step lookup in a per-scroll table of measured radial
                  bins; outside the table or without one, the median
                  pitch of section 3.3 applies.

Table format (json):
    {"axis": "auto" or [cx, cy] in full-res vox,
     "um_per_vox": 2.4,
     "bins_mm": [[r_lo, r_hi, pitch_um], ...],
     "source": "free text provenance"}

The Paris 4 table ships in data/paris4_pitch_table.json and comes from
the radial binning of the human annotated pairs (July measurement,
136-259 um across 0-20 mm).
"""

import json

import numpy as np


def gt_local_tau(gt_xyz, wind, coll, um_per_vox=None):
    """A2.2: tolerance measured from the annotations themselves.

    For each GT point, find the nearest annotated point in the SAME
    collection whose winding differs by exactly 1; tau at that point is
    half that distance. No spacing constant, no axis, no radial model:
    the annotations state directly how far the neighboring sheet is at
    each annotated location. Points with no adjacent-winding neighbor
    in their collection get nan (caller falls back).

    KD-tree per (collection, winding level) when scipy is available:
    mesh collections reach 40k+ points, where pairwise distance matrices
    are not viable. Chunked brute force otherwise.

    Returns tau_vox (N,) with nan where undefined.
    """
    try:
        from scipy.spatial import cKDTree
    except ImportError:
        cKDTree = None

    n = len(gt_xyz)
    tau = np.full(n, np.nan)
    for cid in np.unique(coll):
        idx = np.nonzero(coll == cid)[0]
        if len(idx) < 2:
            continue
        P, W = gt_xyz[idx], np.round(wind[idx])
        levels = np.unique(W)
        best = np.full(len(idx), np.inf)
        for lv in levels:
            here = np.nonzero(W == lv)[0]
            nb = np.nonzero(np.abs(W - lv) == 1)[0]
            if len(nb) == 0:
                continue
            if cKDTree is not None:
                d, _ = cKDTree(P[nb]).query(P[here], k=1, workers=-1)
            else:
                d = np.full(len(here), np.inf)
                for a in range(0, len(here), 2000):
                    b = min(a + 2000, len(here))
                    d2 = ((P[here[a:b], None, :] - P[None, nb, :]) ** 2
                          ).sum(-1)
                    d[a:b] = np.sqrt(d2.min(axis=1))
            best[here] = np.minimum(best[here], d)
        ok = np.isfinite(best)
        tau[idx[ok]] = 0.5 * best[ok]
    return tau


def combine_tau(*candidates):
    """Tightest available estimate wins (A2.2): elementwise nanmin of
    scalar or per-point candidates. Tighter costs coverage, never
    accuracy."""
    arrs = [np.asarray(c, dtype=float) for c in candidates if c is not None]
    n = max((a.shape[0] for a in arrs if a.ndim), default=1)
    stack = np.vstack([np.broadcast_to(a, (n,)) for a in arrs])
    out = np.nanmin(stack, axis=0)
    return out


class PitchTable:
    def __init__(self, axis, um_per_vox, bins_mm, median_um):
        self.axis = axis                      # None => auto from GT
        self.um_per_vox = float(um_per_vox)
        self.bins = sorted(bins_mm)           # [[lo, hi, pitch_um], ...]
        self.median_um = float(median_um)

    @classmethod
    def load(cls, path, median_um):
        d = json.load(open(path))
        axis = d.get("axis", "auto")
        axis = None if axis == "auto" else np.asarray(axis, float)
        return cls(axis, d["um_per_vox"], d["bins_mm"], median_um)

    def resolve_axis(self, gt_xyz):
        if self.axis is None:
            self.axis = np.median(gt_xyz[:, :2], axis=0)
        return self.axis

    def pitch_um_at(self, xyz):
        """Per-point local pitch (um). Inside the table: bin lookup.
        Beyond either end: nearest-bin extrapolation (below the
        innermost bin the MEDIAN would be looser than the local pitch,
        which is exactly the cross-sheet hazard, so the tight inner
        value extends inward). The median fallback only applies when
        there is no table at all."""
        r_mm = np.linalg.norm(xyz[:, :2] - self.axis[None, :], axis=1) \
            * self.um_per_vox / 1000.0
        if not self.bins:
            return np.full(len(xyz), self.median_um)
        out = np.full(len(xyz), np.nan)
        for lo, hi, p in self.bins:
            m = (r_mm >= lo) & (r_mm < hi)
            out[m] = p
        out[r_mm < self.bins[0][0]] = self.bins[0][2]
        out[r_mm >= self.bins[-1][1]] = self.bins[-1][2]
        out[np.isnan(out)] = self.median_um   # interior gaps in the table
        return out

    def tau_vox_at(self, xyz):
        return 0.5 * self.pitch_um_at(xyz) / self.um_per_vox
