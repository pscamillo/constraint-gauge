#!/usr/bin/env python3
"""tests/test_mesh_spacing.py - the direct mesh estimator (A6.3) must
recover a KNOWN spiral pitch with no extrapolation.

The synthetic spiral in test_meshgt grows 220 vox of radius per turn,
so the perpendicular gap between consecutive wraps is 220 vox by
construction. At 2.4 um/vox that is 528 um.
"""
import os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.test_meshgt import build_spiral_tifxyz          # noqa: E402
from gauge.meshgt import mesh_spacing_um                    # noqa: E402

TRUE_VOX = 220.0
UM_PER_VOX = 2.4

def main():
    tmp = tempfile.mkdtemp()
    mesh = os.path.join(tmp, "synth.tifxyz")
    build_spiral_tifxyz(mesh)
    d, info = mesh_spacing_um(mesh, UM_PER_VOX, stride_v=4, stride_u=6)
    true_um = TRUE_VOX * UM_PER_VOX
    err = abs(info["median_um"] - true_um) / true_um
    print(f"  n {info['n']}, median {info['median_um']:.1f} um "
          f"(true {true_um:.1f}), q1 {info['q1_um']:.1f} "
          f"q3 {info['q3_um']:.1f}, erro {err:.1%}")
    fails = 0
    for ok, msg in [(info["n"] > 100, "enough measurements"),
                    (err < 0.05, "median within 5% of true spacing"),
                    (info["q3_um"] / info["q1_um"] < 1.5,
                     "spread is tight, no extrapolation needed")]:
        print(("OK   " if ok else "FAIL ") + msg)
        fails += 0 if ok else 1
    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails

if __name__ == "__main__":
    raise SystemExit(main())
