#!/usr/bin/env python3
"""tools/probe_ws_consistency.py - winding-sync internal figures (A12/A15).

The internal-consistency figures quoted in A12 (satisfied_exactly 0.670,
within_one 0.881, mean_abs_residual 0.611) and the winding spans (216
for L1, 257 for BFS on the identical graph) first came from an ad-hoc
probe preserved only in the session log of 2026-07-29 (A20 item 9).
This file is that probe, committed so the figures have an artefact and
rerun. It writes results/ws_consistency_z<Z>.json.

Recorded output of the original run (stride 160 um, level 2, z 57200):

    seeds 67925, edges 152459
    winding: -27 a 189  (amplitude 216)
    consistency():
      satisfied_exactly: 0.6695308246807339
      within_one: 0.8808532129949691
      mean_abs_residual: 0.6105510333925842
      winding_range: 216
    BFS no mesmo grafo: -60 a 197 (amplitude 257)

Needs abundantjoe/winding-sync importable (PYTHONPATH) and network
access to the open-data bucket. This measures the tool's OWN internal
metric next to the graph the bench scores; it is our stride variant per
A11, never the author's configuration.
"""

import argparse
import json
import os

import numpy as np

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
VOLUME = "20260411134726-2.400um-0.2m-78keV-masked.zarr"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=int, default=57200,
                    help="full-resolution z of the slice")
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--stride-um", type=float, default=160.0,
                    help="our variant stride (A11); the author default "
                         "is TracingConfig().seed_stride_um")
    ap.add_argument("--out", default=None,
                    help="output json; default results/ws_consistency_z<Z>.json")
    a = ap.parse_args()

    from winding_sync.volume import VolumeSource
    from winding_sync.constraints import (build_constraints, TracingConfig,
                                          consistency)
    from winding_sync.solver import solve_l1, solve_bfs_tree

    src = VolumeSource.from_ome_zarr(
        f"{BUCKET}/PHercParis4/volumes/{VOLUME}",
        level=a.level, base_voxel_um=2.4, name="P4")
    img = src.slice_at(a.z // (2 ** a.level)).astype(np.float64)
    g, st = build_constraints(img, src.voxel_um,
                              config=TracingConfig(seed_stride_um=a.stride_um))
    w = solve_l1(g)
    cons = {k: float(v) for k, v in consistency(g, w).items()}
    w_bfs = solve_bfs_tree(g)

    out = {
        "scroll": "PHercParis4",
        "z_full_res": int(a.z),
        "level": int(a.level),
        "seed_stride_um": float(a.stride_um),
        "is_author_config": False,
        "note": ("our stride variant per A11; internal consistency() is "
                 "the tool's own metric, quoted in A12 next to the "
                 "external M1 on the same graph"),
        "n_seeds": int(g.n_nodes),
        "n_edges": int(g.n_edges),
        "l1": {"w_min": float(w.min()), "w_max": float(w.max()),
               "span": float(w.max() - w.min())},
        "consistency": cons,
        "bfs_single_root": {"w_min": float(w_bfs.min()),
                            "w_max": float(w_bfs.max()),
                            "span": float(w_bfs.max() - w_bfs.min())},
    }
    path = a.out or os.path.join("results", f"ws_consistency_z{a.z}.json")
    json.dump(out, open(path, "w"), indent=2)
    print(f"seeds {g.n_nodes}, edges {g.n_edges}")
    print(f"L1 winding span {out['l1']['span']:.0f}, "
          f"BFS span {out['bfs_single_root']['span']:.0f}")
    for k, v in cons.items():
        print(f"  {k}: {v}")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
