#!/usr/bin/env python3
"""tests/test_density.py - the A10 precondition.

A generator finer than the sheets passes; one coarser than the sheets
is reported NOT SCORABLE rather than scored badly.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge.density import check

def main():
    rng = np.random.default_rng(2)
    tau = np.full(1000, 37.5)          # sheet gap 75 vox
    fine = np.column_stack([rng.random(4000) * 2000,
                            rng.random(4000) * 2000,
                            np.zeros(4000)])          # ~22 vox apart
    coarse = np.column_stack([rng.random(120) * 2000,
                              rng.random(120) * 2000,
                              np.zeros(120)])         # ~91 vox apart
    ok_f, info_f = check(fine, tau, planar=True)
    ok_c, info_c = check(coarse, tau, planar=True)
    print(f"  fine  : node gap {info_f['node_gap_vox']:.1f}, ratio "
          f"{info_f['ratio']:.2f} -> scorable={ok_f}")
    print(f"  coarse: node gap {info_c['node_gap_vox']:.1f}, ratio "
          f"{info_c['ratio']:.2f} -> scorable={ok_c}")
    fails = 0
    for ok, msg in [(ok_f, "a generator finer than the sheets is scorable"),
                    (not ok_c, "a generator coarser than the sheets is not")]:
        print(("OK   " if ok else "FAIL ") + msg)
        fails += 0 if ok else 1
    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails

if __name__ == "__main__":
    raise SystemExit(main())
