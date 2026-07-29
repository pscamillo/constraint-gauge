#!/usr/bin/env python3
"""tests/test_planar.py - A9 planar matching for slice-based generators.

GT is a 3D cloud of concentric sheets spanning many z. The adapter is a
perfect generator that only exists on ONE plane. Under 3D matching it
scores nothing (the z offset eats the tolerance); under planar matching
it scores M1 = 1.0 on the pairs whose GT points lie within their own
tau of the plane, and coverage reflects that eligible subset only.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge import gt as gt_mod, adapters, match, metrics
from gauge.localtau import gt_local_tau, combine_tau

def main():
    rng = np.random.default_rng(5)
    X, W, C = [], [], []
    for k in range(6):     # 6 thin sheets in x, 60 vox apart
        n = 4000
        X.append(np.column_stack([
            np.full(n, k * 60.0) + rng.normal(0, 1.0, n),   # sheet plane
            rng.random(n) * 2000,                            # along sheet
            rng.random(n) * 400 + 1000]))                    # height
        W.append(np.full(n, float(k)))
        C.append(np.array(["m"] * n, dtype=object))
    xyz = np.vstack(X); wind = np.concatenate(W); coll = np.concatenate(C)
    pairs = gt_mod.build_pairs(xyz, wind, coll, max_pairs=20000)
    tau = combine_tau(gt_local_tau(xyz, wind, coll),
                      np.full(len(xyz), 1e9))

    zp = 1200.0
    sel = np.abs(xyz[:, 2] - zp) < 5.0      # adapter lives on the plane
    P = xyz[sel].copy(); P[:, 2] = zp
    ad = adapters.AdapterResult("plane", P, wind[sel], np.ones(sel.sum()))

    m3 = match.match(xyz, pairs, ad, tau, planar=False)
    s3 = metrics.summarize(pairs, m3, metrics.score(pairs, m3, ad))
    mp = match.match(xyz, pairs, ad, tau, planar=True)
    sp = metrics.summarize(pairs, mp, metrics.score(pairs, mp, ad))
    print(f"  3D    : M4 {s3['M4_coverage']:.3f}  M1 {s3['M1_exact_dw1']}")
    print(f"  planar: M4 {sp['M4_coverage']:.3f}  M1 {sp['M1_exact_dw1']:.3f}")
    fails = 0
    for ok, msg in [(s3["M4_coverage"] < 0.05,
                     "3D matching cannot reach a single-plane adapter"),
                    (sp["M4_coverage"] > 0.0,
                     "planar matching finds eligible pairs"),
                    (sp["M1_exact_dw1"] == 1.0,
                     "a perfect plane generator scores M1 = 1.0")]:
        print(("OK   " if ok else "FAIL ") + msg)
        fails += 0 if ok else 1
    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails

if __name__ == "__main__":
    raise SystemExit(main())
