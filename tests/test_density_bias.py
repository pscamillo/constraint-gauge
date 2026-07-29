#!/usr/bin/env python3
"""tests/test_density_bias.py - is the surviving sample easier? (A19b)

test_density_curve showed a perfect generator holding M1 above 0.92 out
to ratio 1.64 while coverage collapsed. Two readings are possible and
they lead to opposite decisions about the A10 gate:

  (a) density costs coverage and not accuracy, so the gate double-counts
  (b) the surviving pairs are systematically EASIER, so the high M1 is
      selection and the gate is protecting against a real distortion

This decides between them. For each grid step it compares the surviving
pairs against the full population on the properties that make a pair
easy: the true dw, the separation between the two points, and the local
tau. If the survivors look like the population, (a). If they are
skewed toward small dw, short separation or loose tau, (b).

It also probes the degenerate case seen at grid 40, where the reported
node gap collapsed to 1.6 vox: coarse snapping merges points, and the
nearest-neighbour distance between MERGED nodes is not the spacing of
the grid at all.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge import gt as gt_mod, adapters, match, metrics, density  # noqa
from gauge.localtau import gt_local_tau, combine_tau                # noqa
from tests.test_density_curve import snap_to_grid                   # noqa


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
    sep = np.linalg.norm(xyz[pairs["a"]] - xyz[pairs["b"]], axis=1)
    dw = pairs["dw"].astype(float)
    taupair = np.minimum(tau[pairs["a"]], tau[pairs["b"]])

    print(f"\npopulation: {len(dw)} pairs, "
          f"mean dw {dw.mean():.2f}, median separation {np.median(sep):.1f} "
          f"vox, median tau {np.median(taupair):.1f} vox")
    print(f"\n{'grid':>6} {'M4':>6} {'M1':>6} | survivors: "
          f"{'mean dw':>8} {'med sep':>8} {'med tau':>8}   verdict")

    for step in (0, 10, 20, 25, 30):
        P = xyz if step == 0 else snap_to_grid(xyz, step)
        ad = adapters.AdapterResult(f"perfect@{step}", P, wind,
                                    np.ones(len(wind)))
        mres = match.match(xyz, pairs, ad, tau)
        s_mask = mres.scorable
        t = metrics.score(pairs, mres, ad)
        s = metrics.summarize(pairs, mres, t)
        if s_mask.sum() == 0:
            continue
        d_s, sep_s, tau_s = dw[s_mask], sep[s_mask], taupair[s_mask]
        # a survivor sample is "easier" if dw is smaller, separation is
        # shorter, or tau is looser than the population
        easier = (d_s.mean() < dw.mean() * 0.9 or
                  np.median(sep_s) < np.median(sep) * 0.9 or
                  np.median(tau_s) > np.median(taupair) * 1.1)
        print(f"{step:>6} {s['M4_coverage']:>6.3f} "
              f"{s['M1_exact_dw1']:>6.3f} | "
              f"{d_s.mean():>8.2f} {np.median(sep_s):>8.1f} "
              f"{np.median(tau_s):>8.1f}   "
              f"{'SKEWED EASIER' if easier else 'like population'}")

    print("\ndegenerate node gap at coarse grids:")
    for step in (25, 30, 40):
        P = snap_to_grid(xyz, step)
        uniq = np.unique(np.round(P[:, :2], 6), axis=0)
        ng = density.node_gap_vox(P)
        print(f"  grid {step}: {len(P)} nodes but {len(uniq)} distinct "
              f"(x, y); reported node gap {ng:.1f} vox")
    print("  a node gap far below the grid step means points merged onto "
          "the same node, so the median nearest-neighbour distance is "
          "measuring duplicates rather than spacing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
