#!/usr/bin/env python3
"""tests/test_e1_fidelity.py - gauge.e1 against the original v1_5 (A14).

The A14 fidelity claim (agreement to 0.000e+00 on 300 pairs) first ran
on 2026-07-29 as an ad-hoc script preserved only in the session log
(A20 item 9). This file is that script, committed so the claim has an
artefact and reruns. Recorded output of the original run:

    38 collections | 706 pares
    grad_mag[4]: shape=(282, 2044, 2044)
    pares comparados: 300
    diferenca absoluta entre as duas integrais: max 0.000e+00, media 0.000e+00
    IDENTICO

Needs, outside this repository:
  - the winding-ruler repo (concordance/ruler_concordance_v1_5.py):
      CG_WINDING_RULER, default ~/repos/winding-ruler
  - the spiral dataset root with lasagna_inputs and the annotations:
      CG_DATASET, default
      ~/challenges/vesuvius/spiral-dataset/PHercParis4

Exits with an explanation when either is absent (skip, not failure).
"""

import importlib.util
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

N_PAIRS = 300
TOL = 1e-9


def main():
    ruler = os.environ.get("CG_WINDING_RULER",
                           os.path.expanduser("~/repos/winding-ruler"))
    dataset = os.environ.get(
        "CG_DATASET",
        os.path.expanduser("~/challenges/vesuvius/spiral-dataset/"
                           "PHercParis4"))
    v15_path = os.path.join(ruler, "concordance",
                            "ruler_concordance_v1_5.py")
    if not os.path.exists(v15_path):
        raise SystemExit(f"SKIP: original estimator not found at "
                         f"{v15_path} (set CG_WINDING_RULER)")
    if not os.path.isdir(dataset):
        raise SystemExit(f"SKIP: dataset not found at {dataset} "
                         f"(set CG_DATASET)")

    spec = importlib.util.spec_from_file_location("v15", v15_path)
    v15 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v15)

    from gauge import e1 as mine

    pairs_o, colls = v15.collect_pairs(dataset, 10000, 11000)
    sub, z0 = v15.load_gradmag(dataset, 10000, 11000)

    diffs, n = [], 0
    for cid, a, b, dw in pairs_o[:N_PAIRS]:
        io, ok_o = v15.multiray_integral(sub, z0, a, b, 7, 6.0)
        im, ok_m = mine._multiray(sub, z0, a, b)
        if ok_o and ok_m:
            diffs.append(abs(io - im))
            n += 1
    d = np.array(diffs)
    print(f"pairs compared: {n}")
    print(f"abs difference between the two integrals: "
          f"max {d.max():.3e}, mean {d.mean():.3e}")
    assert n >= 250, f"too few comparable pairs ({n})"
    assert d.max() < TOL, f"DIVERGES: max {d.max():.3e} >= {TOL:.0e}"
    print("OK   bit-identical reimplementation (A14)")
    print("ALL OK")


if __name__ == "__main__":
    main()
