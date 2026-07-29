#!/usr/bin/env python3
"""tests/test_pitch.py - the estimator must converge from above to a
KNOWN spacing before it may judge anything real (A6.1).

Builds concentric sheets with an exactly known perpendicular spacing,
samples points on them at several densities, and checks:
  1. the nearest estimator always OVERestimates (upper bound property)
  2. the estimate decreases as density grows (converges from above)
  3. the extrapolated limit lands within 5% of the true spacing
  4. the allpairs estimator is much worse, as expected
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge import gt as gt_mod                       # noqa: E402
from gauge.pitch import (nearest_spacing_um, allpairs_spacing_um,    # noqa
                         convergence, extrapolate)


TRUE_UM = 180.0


def sheets(n_sheets=8, n_per=4000, spacing_vox=75.0, um_per_vox=2.4,
           seed=3):
    """Flat parallel sheets, spacing exact and perpendicular."""
    rng = np.random.default_rng(seed)
    X, W = [], []
    for k in range(n_sheets):
        p = np.column_stack([rng.random(n_per) * 4000.0,
                             rng.random(n_per) * 4000.0,
                             np.full(n_per, k * spacing_vox)])
        X.append(p)
        W.append(np.full(n_per, float(k)))
    return np.vstack(X), np.concatenate(W), \
        np.array(["s"] * (n_sheets * n_per), dtype=object)


def main():
    um_per_vox = 2.4
    spacing_vox = TRUE_UM / um_per_vox
    xyz, wind, coll = sheets(spacing_vox=spacing_vox,
                             um_per_vox=um_per_vox)

    curve = convergence(xyz, wind, coll, um_per_vox)
    for c in curve:
        print(f"  frac {c['fraction']:.2f}  n {c['n_est']:6d}  "
              f"median {c['median_um']:7.1f} um")
    med = [c["median_um"] for c in curve]
    limit, slope, r2 = extrapolate(curve)
    pairs = gt_mod.build_pairs(xyz, wind, coll, max_pairs=50000)
    ap = float(np.median(allpairs_spacing_um(xyz, pairs, um_per_vox)))
    print(f"  extrapolated limit {limit:.1f} um (true {TRUE_UM}, "
          f"r2 {r2:.3f});  allpairs median {ap:.0f} um")

    fails = 0
    checks = [
        (all(m >= TRUE_UM * 0.99 for m in med),
         "nearest estimator never underestimates"),
        (all(med[i] >= med[i + 1] - 1e-9 for i in range(len(med) - 1)),
         "estimate decreases with density"),
        (abs(limit - TRUE_UM) / TRUE_UM < 0.05,
         "extrapolated limit within 5% of truth"),
        (ap > TRUE_UM * 1.5,
         "allpairs is a ceiling, not a competitor"),
    ]
    for ok, msg in checks:
        print(("OK   " if ok else "FAIL ") + msg)
        fails += 0 if ok else 1
    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
