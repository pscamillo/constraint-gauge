#!/usr/bin/env python3
"""tests/test_mesharm_calibration.py - does the mesh arm return what it
is given? (A17)

The two GT arms never overlap: the annotated arm sits where the lasagna
grad_mag field exists (z up to ~18948 full-res), the mesh arm sits above
it (z 29420-73889). So a subject built on that field cannot be scored on
the mesh arm at all, and no subject can be cross-validated across the
two. The sanity question has to be answered from inside: given an
adapter whose error rate is KNOWN by construction, does the mesh arm
report that rate?

Builds adapters from the mesh GT itself with a controlled fraction of
windings corrupted by +/-1, and checks that measured M1 tracks the
injected accuracy. A ruler that reports 0.05 for a subject that is 80%
right would be broken; this test would catch it.

Run from the repo root with the mesh data present:
    python tests/test_mesharm_calibration.py data/gp_meshes
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge import gt as gt_mod, adapters, match, metrics   # noqa: E402
from gauge.localtau import gt_local_tau, combine_tau        # noqa: E402


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "data/gp_meshes"
    from run_gauge import load_mesh_arm
    xyz, wind, coll = load_mesh_arm(root, stride=10)
    pairs = gt_mod.build_pairs(xyz, wind, coll, max_pairs=30000)
    tau = combine_tau(gt_local_tau(xyz, wind, coll),
                      np.full(len(xyz), 37.5))
    print(f"\nmesh arm: {len(xyz)} points, {len(pairs['dw'])} pairs")

    def expected(f):
        return (1.0 - f) ** 2 + f * f / 2.0

    rng = np.random.default_rng(11)
    rows, fails = [], 0
    for frac in (0.0, 0.1, 0.3, 0.5, 1.0):
        w = wind.copy()
        bad = rng.random(len(w)) < frac
        w[bad] += rng.choice([-1.0, 1.0], size=bad.sum())
        ad = adapters.AdapterResult(f"synthetic-{frac:.0%}", xyz, w,
                                    np.ones(len(w)))
        mres = match.match(xyz, pairs, ad, tau)
        t = metrics.score(pairs, mres, ad)
        s = metrics.summarize(pairs, mres, t)
        rows.append((frac, s["M1_exact_dw1"], s["M2_mae"],
                     s["M4_coverage"]))
        exp = expected(frac)
        print(f"  corrupted {frac:.0%}: M1 {s['M1_exact_dw1']:.3f}  "
              f"(closed form {exp:.3f}, diff "
              f"{abs(s['M1_exact_dw1']-exp):.3f})  "
              f"M2 {s['M2_mae']:.3f}  M4 {s['M4_coverage']:.3f}")

    m1 = [r[1] for r in rows]
    devs = [abs(r[1] - expected(r[0])) for r in rows]
    checks = [
        (max(devs) < 0.02,
         f"every point matches the closed form (max deviation "
         f"{max(devs):.3f})"),
        (m1[0] > 0.99, "uncorrupted adapter scores 1.0"),
        (abs(m1[-1] - 0.5) < 0.03,
         "fully corrupted adapter sits at the 0.5 floor, as the algebra "
         "predicts, not at zero"),
        (all(r[3] > 0.99 for r in rows),
         "coverage is unaffected by accuracy"),
    ]
    for ok, msg in checks:
        print(("OK   " if ok else "FAIL ") + msg)
        fails += 0 if ok else 1
    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
