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
