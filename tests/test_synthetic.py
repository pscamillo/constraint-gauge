#!/usr/bin/env python3
"""tests/test_synthetic.py - end-to-end check with known answers.

Builds an Archimedean spiral, samples GT points with known windings,
then scores three synthetic adapters:

  perfect   adapter points on the spiral, correct windings     -> M1 = 1
  noisy20   20% of adapter windings shifted by +-1             -> M1 ~ known
  offset    adapter displaced by 3*tau                          -> M4 ~ 0

The noisy adapter's confidence is informative (low where corrupted), so
its calibration bins must show rising accuracy with confidence.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge import gt as gt_mod                      # noqa: E402
from gauge import adapters, match, metrics          # noqa: E402


def spiral(n_per_turn=40, turns=12, pitch_vox=20.0):
    th = np.linspace(0, 2 * np.pi * turns, n_per_turn * turns)
    r = 50 + pitch_vox * th / (2 * np.pi)
    x = 1000 + r * np.cos(th)
    y = 1000 + r * np.sin(th)
    z = np.full_like(x, 500.0)
    w = th / (2 * np.pi)
    return np.column_stack([x, y, z]), w


def fake_gt(xyz, w, every=13):
    """Subsample the spiral into 'annotated points', one collection."""
    idx = np.arange(0, len(w), every)
    pts = xyz[idx]
    wind = np.floor(w[idx])
    coll = np.array(["1"] * len(idx), dtype=object)
    return pts, wind, coll


def main():
    rng = np.random.default_rng(7)
    xyz, w = spiral()
    gt_xyz, gt_w, gt_c = fake_gt(xyz, w)
    pairs = gt_mod.build_pairs(gt_xyz, gt_w, gt_c)
    tau = match.tau_vox(pitch_um=20.0, um_per_vox=1.0)  # pitch 20 vox
    print(f"synthetic: {len(gt_xyz)} gt points, {len(pairs['dw'])} pairs, "
          f"tau {tau} vox")
    fails = 0

    # 1. perfect
    perfect = adapters.AdapterResult("perfect", xyz, np.floor(w),
                                     np.ones(len(w)))
    mres = match.match(gt_xyz, pairs, perfect, tau)
    t = metrics.score(pairs, mres, perfect)
    s = metrics.summarize(pairs, mres, t)
    ok = s["M1_exact_dw1"] == 1.0 and s["M4_coverage"] == 1.0 \
        and s["M2_mae"] == 0.0
    print(f"perfect: M1 {s['M1_exact_dw1']:.3f} M2 {s['M2_mae']:.3f} "
          f"M4 {s['M4_coverage']:.3f}  {'OK' if ok else 'FAIL'}")
    fails += 0 if ok else 1

    # 2. noisy20 with informative confidence
    wind = np.floor(w).copy()
    bad = rng.random(len(wind)) < 0.20
    wind[bad] += rng.choice([-1.0, 1.0], size=bad.sum())
    conf = np.where(bad, 0.2, 0.9) + rng.random(len(wind)) * 0.05
    noisy = adapters.AdapterResult("noisy20", xyz, wind, conf)
    mres = match.match(gt_xyz, pairs, noisy, tau)
    t = metrics.score(pairs, mres, noisy)
    s = metrics.summarize(pairs, mres, t)
    accs = [b["acc"] for b in s["M3_bins"]]
    calib_ok = len(accs) >= 4 and accs[-1] > accs[0]
    ok = 0.5 < s["M1_exact_dw1"] < 0.95 and calib_ok
    print(f"noisy20: M1 {s['M1_exact_dw1']:.3f} M2 {s['M2_mae']:.3f} "
          f"M4 {s['M4_coverage']:.3f} calib low->high "
          f"{accs[0]:.2f}->{accs[-1]:.2f}  {'OK' if ok else 'FAIL'}")
    fails += 0 if ok else 1

    # 3. displaced far beyond the domain: nothing should be scorable
    off = adapters.AdapterResult("offset", xyz + np.array([5000.0, 0, 0]),
                                 np.floor(w), np.ones(len(w)))
    mres = match.match(gt_xyz, pairs, off, tau)
    t = metrics.score(pairs, mres, off)
    s = metrics.summarize(pairs, mres, t)
    ok = s["M4_coverage"] < 0.05
    print(f"offset : M4 {s['M4_coverage']:.3f}  {'OK' if ok else 'FAIL'}")
    fails += 0 if ok else 1

    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
