#!/usr/bin/env python3
"""tests/test_gt_tau.py - A2.2: tolerance from the annotations.

Same tightening rings as test_localtau. The annotation-derived tau
needs no table and no axis: each GT point measures its own neighbor
distance. Must match or beat the A2.1 table result (M1 == 1.0), and on
the synthetic where annotations are dense, tau_gt must be defined for
nearly all points.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.test_localtau import rings
from gauge import gt as gt_mod, adapters, match, metrics
from gauge.localtau import gt_local_tau, combine_tau


def main():
    xyz, w, radii = rings()
    spacing = np.diff(radii)
    gi = np.arange(0, len(w), 5)
    gt_xyz, gt_w = xyz[gi], w[gi]
    gt_c = np.array(["1"] * len(gi), dtype=object)
    pairs = gt_mod.build_pairs(gt_xyz, gt_w, gt_c)
    keep = ~((w < 8) & (w % 2 == 0))
    ad = adapters.AdapterResult("gappy", xyz[keep], w[keep],
                                np.ones(keep.sum()))

    tau_gt = gt_local_tau(gt_xyz, gt_w, gt_c)
    tau_med = 0.5 * float(np.median(spacing))
    tau = combine_tau(tau_gt, np.full(len(gt_xyz), tau_med))

    cov_def = np.isfinite(tau_gt).mean()
    mres = match.match(gt_xyz, pairs, ad, tau)
    t = metrics.score(pairs, mres, ad)
    s = metrics.summarize(pairs, mres, t)
    print(f"A2.2: tau defined on {cov_def:.1%} of gt points; "
          f"M1 {s['M1_exact_dw1']:.3f} M2 {s['M2_mae']:.3f} "
          f"M4 {s['M4_coverage']:.3f}")
    fails = 0
    for ok, msg in [
        (cov_def > 0.95, "annotation tau defined almost everywhere"),
        (s["M1_exact_dw1"] == 1.0, "accuracy clean, no geometry used"),
    ]:
        print(("OK   " if ok else "FAIL ") + msg)
        fails += 0 if ok else 1
    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
