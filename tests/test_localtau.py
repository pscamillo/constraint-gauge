#!/usr/bin/env python3
"""tests/test_localtau.py - A2.1 demonstration with known answers.

Builds concentric windings whose spacing TIGHTENS toward the axis
(10 vox inner to ~40 vox outer, like a real scroll). The adapter is
honest but has gaps: in the tight inner region, even-numbered windings
carry no adapter points. A GT query on a missing winding then has its
nearest adapter point on the NEIGHBOURING sheet, one local pitch away.

Under the median tau (half the MEDIAN pitch, larger than the inner
pitch) that neighbour is inside tolerance: the match crosses sheets
silently and poisons dw. This is exactly the failure Paul Henderson
described. Under the local tau (A2.1) the same match is rejected: the
pair costs coverage, never accuracy.

Asserts:
  median tau: M1 on dw=1 clearly poisoned (< 0.9)
  local tau:  M1 on dw=1 == 1.0, at lower coverage
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge import gt as gt_mod                      # noqa: E402
from gauge import adapters, match, metrics          # noqa: E402
from gauge.localtau import PitchTable               # noqa: E402


def rings(n_wind=24, n_ang=48, cx=1000.0, cy=1000.0):
    """Concentric windings, spacing 10 vox inner growing ~1.6/turn."""
    radii, r = [], 50.0
    for k in range(n_wind):
        radii.append(r)
        r += 10.0 + 1.6 * k
    th = np.linspace(0, 2 * np.pi, n_ang, endpoint=False)
    pts, wind = [], []
    for k, rk in enumerate(radii):
        pts.append(np.column_stack([cx + rk * np.cos(th),
                                    cy + rk * np.sin(th),
                                    np.full(n_ang, 500.0)]))
        wind.append(np.full(n_ang, float(k)))
    return np.vstack(pts), np.concatenate(wind), np.asarray(radii)


def main():
    xyz, w, radii = rings()
    spacing = np.diff(radii)                      # local pitch per winding

    # GT: every 5th point, one collection
    gi = np.arange(0, len(w), 5)
    gt_xyz, gt_w = xyz[gi], w[gi]
    gt_c = np.array(["1"] * len(gi), dtype=object)
    pairs = gt_mod.build_pairs(gt_xyz, gt_w, gt_c)

    # adapter: honest labels, but inner even windings are missing
    inner = w < 8
    keep = ~(inner & (w % 2 == 0))
    ad = adapters.AdapterResult("gappy", xyz[keep], w[keep],
                                np.ones(keep.sum()))

    um_per_vox = 1.0
    median_pitch = float(np.median(spacing))      # ~ mid-range
    tau_med = match.tau_vox(median_pitch, um_per_vox)

    # local table from the true spacing, binned by radius in "mm" (vox/1000)
    bins = [[radii[k] / 1000.0, radii[k + 1] / 1000.0, float(spacing[k])]
            for k in range(len(spacing))]
    table = {"axis": [1000.0, 1000.0], "um_per_vox": um_per_vox,
             "bins_mm": bins, "source": "synthetic true spacing"}
    json.dump(table, open("/tmp/synth_table.json", "w"))
    pt = PitchTable.load("/tmp/synth_table.json", median_um=median_pitch)
    pt.resolve_axis(gt_xyz)
    tau_loc = pt.tau_vox_at(gt_xyz)

    fails = 0
    res = {}
    for name, tau in [("median", tau_med), ("local", tau_loc)]:
        mres = match.match(gt_xyz, pairs, ad, tau)
        t = metrics.score(pairs, mres, ad)
        s = metrics.summarize(pairs, mres, t)
        res[name] = s
        print(f"{name:6s} tau: M1 {s['M1_exact_dw1']:.3f}  "
              f"M2 {s['M2_mae']:.3f}  M4 {s['M4_coverage']:.3f}  "
              f"(n_dw1 {s['n_dw1']})")

    ok1 = res["median"]["M1_exact_dw1"] < 0.9
    ok2 = res["local"]["M1_exact_dw1"] == 1.0
    ok3 = res["local"]["M4_coverage"] < res["median"]["M4_coverage"]
    for ok, msg in [(ok1, "median tau is poisoned by cross-sheet matches"),
                    (ok2, "local tau keeps accuracy clean"),
                    (ok3, "local tau pays in coverage, not correctness")]:
        print(("OK   " if ok else "FAIL ") + msg)
        fails += 0 if ok else 1
    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
