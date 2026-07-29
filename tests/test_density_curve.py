#!/usr/bin/env python3
"""tests/test_density_curve.py - where does node spacing actually break
scoring? (A19)

A10 refuses to score a generator whose nodes are more spaced than the
sheets, with the cut at ratio 1.0. That number was argued from geometry,
never measured. This measures it.

Method: take the annotated arm's own ground truth, build a PERFECT
generator from it (every winding correct by construction), then move its
nodes onto grids of increasing coarseness. The generator never gets any
worse; only the localisation step does. Whatever M1 does across that
sweep is the cost of density alone, with accuracy held at 1.0.

Reading it: if a perfect generator still scores well at ratio 1.15, the
gate at 1.0 is too strict and marginal submissions are being blocked for
nothing. If it collapses well before that, the gate is right and any
subject scoring above the curve at its own ratio is doing better than a
perfect generator would at that spacing.

    python tests/test_density_curve.py <relative_windings.json>
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge import gt as gt_mod, adapters, match, metrics, density  # noqa
from gauge.localtau import gt_local_tau, combine_tau                # noqa


def snap_to_grid(xyz, step):
    """Move every point to the nearest node of a regular grid of the
    given step, keeping z, which is how a slice-wise generator on a
    fixed grid lays its nodes out."""
    out = xyz.copy()
    out[:, 0] = np.round(xyz[:, 0] / step) * step
    out[:, 1] = np.round(xyz[:, 1] / step) * step
    return out


def main():
    gt_path = (sys.argv[1] if len(sys.argv) > 1 else
               os.environ.get("CG_GT_JSON") or
               os.path.expanduser("~/challenges/vesuvius/spiral-dataset/"
                                  "PHercParis4/relative_windings.json"))
    if not os.path.exists(gt_path):
        raise SystemExit(
            f"annotated GT not found: {gt_path}\n"
            "this test needs the Paris 4 relative_windings.json "
            "(spiral-input dataset). Pass its path as the first "
            "argument or set CG_GT_JSON.")
    xyz, wind, coll = gt_mod.load_points(gt_path)
    pairs = gt_mod.build_pairs(xyz, wind, coll)
    tau = combine_tau(gt_local_tau(xyz, wind, coll),
                      np.full(len(xyz), 1e9))
    sheet_gap = 2.0 * float(np.median(tau[np.isfinite(tau)]))
    print(f"\nannotated arm: {len(xyz)} points, {len(pairs['dw'])} pairs")
    print(f"sheet gap (2 x median tau): {sheet_gap:.1f} vox\n")
    print(f"{'grid':>6} {'node gap':>9} {'ratio':>6} {'M1':>7} "
          f"{'M2':>7} {'M4':>7}  gate")
    rows = []
    for step in (0, 5, 10, 15, 20, 25, 30, 40):
        P = xyz if step == 0 else snap_to_grid(xyz, step)
        ad = adapters.AdapterResult(f"perfect@{step}", P, wind,
                                    np.ones(len(wind)))
        ok, dens = density.check(P, tau)
        mres = match.match(xyz, pairs, ad, tau)
        t = metrics.score(pairs, mres, ad)
        s = metrics.summarize(pairs, mres, t)
        rows.append((step, dens["ratio"], s["M1_exact_dw1"],
                     s["M2_mae"], s["M4_coverage"], ok))
        lbl = "exact" if step == 0 else f"{step} vox"
        print(f"{lbl:>6} {dens['node_gap_vox']:>9.1f} "
              f"{dens['ratio']:>6.2f} {s['M1_exact_dw1']:>7.3f} "
              f"{s['M2_mae']:>7.3f} {s['M4_coverage']:>7.3f}  "
              f"{'pass' if ok else 'BLOCK'}")

    print("\nreading:")
    blocked = [r for r in rows if not r[5] and np.isfinite(r[2])]
    if blocked:
        best_blocked = max(blocked, key=lambda r: r[2])
        print(f"  best M1 among grids the gate BLOCKS: "
              f"{best_blocked[2]:.3f} at ratio {best_blocked[1]:.2f}")
    passed = [r for r in rows if r[5] and np.isfinite(r[2])]
    if passed:
        worst_passed = min(passed, key=lambda r: r[2])
        print(f"  worst M1 among grids the gate PASSES: "
              f"{worst_passed[2]:.3f} at ratio {worst_passed[1]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
