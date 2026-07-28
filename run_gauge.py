#!/usr/bin/env python3
"""run_gauge.py - score one constraint generator against human annotations.

    python run_gauge.py --gt relative_windings.json \
        --adapter json:result.json \
        --pitch-um 187.3 --um-per-vox 2.4 \
        --out-prefix paris4_windingsync

Adapters:  json:PATH            AdapterResult serialized as JSON
           windingsync:SCROLL:Z winding-sync L1 on that slice
           bfs:SCROLL:Z         BFS baseline on the same graph

tau is derived, never passed: 0.5 x pitch_um / um_per_vox (GATE0 3.3).
Outputs: <prefix>_pairs.csv (per-pair table, the source of truth) and
<prefix>_summary.json. Diagnostic runs at tau/2 and 2tau are printed
but never primary (3.6).
"""

import argparse
import json

import numpy as np

from gauge import gt as gt_mod
from gauge import adapters, match, metrics


def build_adapter(spec):
    kind, _, rest = spec.partition(":")
    if kind == "json":
        return adapters.load_json(rest)
    if kind in ("windingsync", "bfs"):
        scroll, _, z = rest.partition(":")
        solver = "l1" if kind == "windingsync" else "bfs"
        return adapters.from_winding_sync(scroll, int(z), solver=solver)
    raise SystemExit(f"unknown adapter spec: {spec}")


def run(gt_path, adapter, pitch_um, um_per_vox, p_order, out_prefix,
        pitch_table=None):
    xyz, wind, coll = gt_mod.load_points(gt_path, p_order=p_order)
    pairs = gt_mod.build_pairs(xyz, wind, coll)
    tau_med = match.tau_vox(pitch_um, um_per_vox)
    if pitch_table:
        from gauge.localtau import PitchTable
        pt = PitchTable.load(pitch_table, median_um=pitch_um)
        pt.resolve_axis(xyz)
        tau = pt.tau_vox_at(xyz)                  # per-GT-point (A2.1)
        print(f"gt: {len(xyz)} points, {len(pairs['dw'])} pairs; "
              f"local tau {tau.min():.1f}-{tau.max():.1f} vox "
              f"(median fallback {tau_med:.1f})")
    else:
        tau = tau_med
        print(f"gt: {len(xyz)} points, {len(pairs['dw'])} pairs; "
              f"tau = {tau_med:.1f} vox")

    for label, t in [("tau/2", tau / 2), ("tau", tau), ("2tau", tau * 2)]:
        mres = match.match(xyz, pairs, adapter, t)
        table = metrics.score(pairs, mres, adapter)
        summ = metrics.summarize(pairs, mres, table)
        line = (f"  [{label:5s}] scorable {summ['n_scorable']:5d} "
                f"(M4 {summ['M4_coverage']:.3f})  "
                f"M1 {summ['M1_exact_dw1']:.3f}  M2 {summ['M2_mae']:.3f}")
        print(line)
        if label == "tau":
            metrics.write_csv(f"{out_prefix}_pairs.csv", table)
            summ["adapter"] = adapter.name
            summ["tau_vox"] = float(np.mean(t)) if hasattr(t, "__len__") else t
            summ["tau_mode"] = "local" if pitch_table else "median"
            summ["pitch_um"] = pitch_um
            summ["um_per_vox"] = um_per_vox
            json.dump(summ, open(f"{out_prefix}_summary.json", "w"),
                      indent=2)
            print(f"  wrote {out_prefix}_pairs.csv, "
                  f"{out_prefix}_summary.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--pitch-um", type=float, required=True)
    ap.add_argument("--um-per-vox", type=float, required=True)
    ap.add_argument("--p-order", default="xyz", choices=["xyz", "zyx"])
    ap.add_argument("--out-prefix", default="gauge_run")
    ap.add_argument("--pitch-table", default=None,
                    help="per-scroll radial pitch table json (A2.1 local tau)")
    a = ap.parse_args()
    run(a.gt, build_adapter(a.adapter), a.pitch_um, a.um_per_vox,
        a.p_order, a.out_prefix, pitch_table=a.pitch_table)


if __name__ == "__main__":
    main()
