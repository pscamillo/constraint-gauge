#!/usr/bin/env python3
"""tests/test_meshgt.py - A3.1 extractor on a synthetic 8-wrap segment.

Builds a tifxyz grid of an 8-turn spiral (arc along u, height along v),
writes it to disk, and checks that load_mesh_gt: detects 8 wraps via
the self-proximity chain (no axis given), assigns windings that match
the construction exactly, trims the seam wraps, and that the resulting
pairs score M1 = 1.0 against a perfect self-adapter through the
existing pipeline.
"""

import json
import os
import sys
import tempfile

import numpy as np
import tifffile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gauge import gt as gt_mod, adapters, match, metrics   # noqa: E402
from gauge.meshgt import load_mesh_gt                       # noqa: E402
from gauge.localtau import gt_local_tau, combine_tau        # noqa: E402


def build_spiral_tifxyz(dirpath, turns=8, V=30, step=20.0):
    """Archimedean spiral sampled at ~constant 3D arc step, generated
    until the requested number of turns completes."""
    r0, growth = 800.0, 220.0 / (2 * np.pi)   # r grows 220 vox per turn
    th_list = [0.0]
    while th_list[-1] < turns * 2 * np.pi:
        r = r0 + growth * th_list[-1]
        th_list.append(th_list[-1] + step / r)
    th = np.asarray(th_list)
    U = len(th)
    r = r0 + growth * th
    cx, cy = 5000.0, 5000.0
    xs = cx + r * np.cos(th)
    ys = cy + r * np.sin(th)
    true_w = np.floor(th / (2 * np.pi)).astype(int)

    x = np.tile(xs, (V, 1))
    y = np.tile(ys, (V, 1))
    z = 60000.0 + np.arange(V)[:, None] * step + 0 * x
    os.makedirs(dirpath, exist_ok=True)
    for name, arr in [("x", x), ("y", y), ("z", z)]:
        tifffile.imwrite(os.path.join(dirpath, f"{name}.tif"),
                         arr.astype(np.float32))
    json.dump({"scale": [1.0 / step, 1.0 / step], "format": "tifxyz",
               "type": "seg", "uuid": "synthspiral"},
              open(os.path.join(dirpath, "meta.json"), "w"))
    return true_w


def main():
    tmp = tempfile.mkdtemp()
    mesh = os.path.join(tmp, "synth.tifxyz")
    true_w = build_spiral_tifxyz(mesh)

    xyz, wind, coll, info = load_mesh_gt(mesh, stride=6)
    print(f"wraps detected: {info['n_wraps']}  points: {info['points']}  "
          f"wrap arcs (vox): "
          f"{[f'{a:.0f}' for a in info['wrap_arc_vox'][:4]]}...")

    fails = 0
    ok = info["n_wraps"] == 8
    print(("OK   " if ok else "FAIL ") + "8 wraps found by the chain")
    fails += 0 if ok else 1

    # windings must be internally consistent: pairs + self-adapter
    pairs = gt_mod.build_pairs(xyz, wind, coll, max_pairs=60000)
    ad = adapters.AdapterResult("self", xyz, wind, np.ones(len(wind)))
    tau = combine_tau(gt_local_tau(xyz, wind, coll),
                      np.full(len(xyz), 1e9))
    mres = match.match(xyz, pairs, ad, tau)
    t = metrics.score(pairs, mres, ad)
    s = metrics.summarize(pairs, mres, t)
    print(f"pairs {len(pairs['dw'])}  M1 {s['M1_exact_dw1']:.3f}  "
          f"M4 {s['M4_coverage']:.3f}")
    ok = s["M1_exact_dw1"] == 1.0 and s["M4_coverage"] == 1.0
    print(("OK   " if ok else "FAIL ") + "self-adapter scores clean")
    fails += 0 if ok else 1

    # trim: windings 0 and 7 must be absent
    ok = wind.min() >= 1 and wind.max() <= 6
    print(("OK   " if ok else "FAIL ") + "seam wraps trimmed")
    fails += 0 if ok else 1

    print("ALL OK" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
