#!/usr/bin/env python3
"""run_e1.py - score the E1 estimator (S-D) on the annotated arm.

    python run_e1.py --dataset ~/.../spiral-dataset/PHercParis4 \
        --out-prefix results/e1

Reports two lines, per addendum A4 and A7:
  in-sample  pairs inside the z10000-11000 development window
  held-out   all other pairs, with k and orient frozen from the window

Only the held-out line is comparable with other subjects.
"""

import argparse
import json
import os

import numpy as np

from gauge import gt as gt_mod
from gauge import e1 as e1_mod
from gauge import pairwise, provenance

WINDOW = (10000, 11000)


def report(tag, pairs, res, subject, arm):
    table = pairwise.score_pairs(pairs, res)
    summ = pairwise.summarize_pairs(pairs, res, table)
    lab, note = provenance.label_for(subject, arm)
    summ.update({"subject": subject, "gt_arm": arm, "provenance": lab,
                 "provenance_note": note,
                 "publishable_as_headline": provenance.publishable(lab),
                 "estimator": res.stats})
    print(f"\n== {tag} ==")
    print(f"  pairs {summ['n_pairs_gt']}, answered {summ['n_scorable']} "
          f"(M4 {summ['M4_coverage']:.3f})")
    print(f"  M1 (dw=1, n={summ['n_dw1']}) {summ['M1_exact_dw1']:.3f}   "
          f"M2 {summ['M2_mae']:.3f}")
    print(f"  provenance: {subject} vs {arm} -> {lab.upper()}")
    if summ["M3_bins"]:
        b = summ["M3_bins"]
        print(f"  calibration: lowest-confidence bin {b[0]['acc']:.2f}, "
              f"highest {b[-1]['acc']:.2f}")
    return table, summ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out-prefix", default="results/e1")
    ap.add_argument("--max-pairs", type=int, default=None)
    a = ap.parse_args()

    gt_path = os.path.join(a.dataset, "relative_windings.json")
    xyz, wind, coll = gt_mod.load_points(gt_path)
    pairs = gt_mod.build_pairs(xyz, wind, coll, max_pairs=a.max_pairs)
    za, zb = xyz[pairs["a"], 2], xyz[pairs["b"], 2]
    inwin = (za >= WINDOW[0]) & (za < WINDOW[1]) & \
            (zb >= WINDOW[0]) & (zb < WINDOW[1])
    print(f"gt: {len(xyz)} points, {len(pairs['dw'])} pairs; "
          f"{inwin.sum()} inside the z{WINDOW[0]}-{WINDOW[1]} window, "
          f"{(~inwin).sum()} outside")

    res = e1_mod.predict(xyz, pairs, a.dataset)

    for tag, mask, subj in (
            ("IN-SAMPLE (development window)", inwin, "E1"),
            ("HELD-OUT (everything else)", ~inwin, "E1/held-out")):
        sub_pairs = {k: v[mask] for k, v in pairs.items()}
        sub_res = pairwise.PairwiseResult(
            subj, res.dw_pred[mask], res.answered[mask], res.conf[mask])
        sub_res.stats = res.stats
        table, summ = report(tag, sub_pairs, sub_res, subj,
                             "paris4-annotations")
        pref = f"{a.out_prefix}_{'insample' if subj == 'E1' else 'heldout'}"
        from gauge import metrics
        metrics.write_csv(f"{pref}_pairs.csv", table)
        json.dump(summ, open(f"{pref}_summary.json", "w"), indent=2)
        print(f"  wrote {pref}_pairs.csv, {pref}_summary.json")


if __name__ == "__main__":
    main()
