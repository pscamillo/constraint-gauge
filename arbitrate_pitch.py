#!/usr/bin/env python3
"""arbitrate_pitch.py - GATE0 section 6 arbitration, 225 vs 187 um.

    python arbitrate_pitch.py --gt data/.../relative_windings.json \
        --um-per-vox 2.4 --arm paris4-annotations --out arb_annot.json

    python arbitrate_pitch.py --gt-mesh data/gp_meshes \
        --um-per-vox 2.4 --arm paris4-meshes --out arb_mesh.json

The judge is the physical distance between annotated points on adjacent
windings (6.1). Both estimators are reported (nearest, allpairs) and the
verdict comes from the bootstrap interval on the density-extrapolated
limit (A6.1). Verdict letters are the pre-registered ones from 6.2.
"""

import argparse
import json

import os

import numpy as np

from gauge import gt as gt_mod
from gauge import pitch as pitch_mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", default=None)
    ap.add_argument("--gt-mesh", default=None)
    ap.add_argument("--um-per-vox", type=float, required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--p-order", default="xyz", choices=["xyz", "zyx"])
    ap.add_argument("--boot", type=int, default=40)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.gt_mesh:
        from run_gauge import load_mesh_arm
        xyz, wind, coll = load_mesh_arm(a.gt_mesh)
    elif a.gt:
        xyz, wind, coll = gt_mod.load_points(a.gt, p_order=a.p_order)
    else:
        raise SystemExit("need --gt or --gt-mesh")

    print(f"\narm: {a.arm}, {len(xyz)} points, "
          f"{len(np.unique(coll))} collections")

    limit, lo, hi, r2, curve = pitch_mod.extrapolate_ci(
        xyz, wind, coll, a.um_per_vox, n_boot=a.boot)
    print("\nconvergence (nearest estimator):")
    for c in curve:
        print(f"  frac {c['fraction']:.2f}  n {c['n_est']:7d}  "
              f"median {c['median_um']:7.1f} um  "
              f"[q1 {c['q1_um']:.1f}, q3 {c['q3_um']:.1f}]")

    pairs = gt_mod.build_pairs(xyz, wind, coll, max_pairs=200000)
    apm = pitch_mod.allpairs_spacing_um(xyz, pairs, a.um_per_vox)
    ap_med = float(np.median(apm)) if len(apm) else float("nan")

    ok, reasons = pitch_mod.validate_extrapolation(limit, lo, hi, curve)
    _, _, r2_main = pitch_mod.extrapolate(curve)
    print(f"\nextrapolated limit: {limit:.1f} um "
          f"[95% {lo:.1f}, {hi:.1f}], fit r2 {r2_main:.3f} "
          f"(bootstrap median r2 {r2:.3f})")
    print(f"allpairs median (ceiling): {ap_med:.0f} um")

    direct = None
    if a.gt_mesh:
        from gauge.meshgt import mesh_spacing_um
        import glob
        allsp, per = [], []
        for d0 in sorted(glob.glob(os.path.join(a.gt_mesh, "*"))):
            if not os.path.isdir(d0):
                continue
            sp, info = mesh_spacing_um(d0, a.um_per_vox)
            if info["n"]:
                allsp.append(sp)
                per.append({"mesh": os.path.basename(d0), **info})
        if allsp:
            allsp = np.concatenate(allsp)
            direct = {"n": int(len(allsp)),
                      "median_um": float(np.median(allsp)),
                      "q1_um": float(np.percentile(allsp, 25)),
                      "q3_um": float(np.percentile(allsp, 75)),
                      "per_mesh": per}
            print("\ndirect mesh estimator (A6.3), no extrapolation:")
            for p in per:
                print(f"  {p['mesh']}: n {p['n']:6d}  "
                      f"median {p['median_um']:6.1f} um  "
                      f"[q1 {p['q1_um']:.1f}, q3 {p['q3_um']:.1f}]")
            print(f"  POOLED: n {direct['n']}, median "
                  f"{direct['median_um']:.1f} um "
                  f"[q1 {direct['q1_um']:.1f}, q3 {direct['q3_um']:.1f}]")

    if direct is not None:
        # the unit of independence is the MESH, not the point: adjacent
        # grid cells measure nearly the same gap. Bootstrapping points
        # gives a spuriously tight interval (0.7 um wide on the first
        # run); bootstrapping meshes reports the spread that matters.
        clean = [p for p in per if p.get("accepted")]
        rejected = [p for p in per if not p.get("accepted")]
        for p in per:
            k = p.get("wrap_skip_k", 1)
            tag = f"  [wrap-skip k={k}, corrected]" if k > 1 else ""
            if not p.get("accepted"):
                tag += "  REJECTED"
            print(f"  cross-check {p['mesh']}: implied "
                  f"{p['implied_dr_um']:.0f} / raw "
                  f"{p['median_raw_um']:.0f} = {p['ratio_raw']:.2f}"
                  f" -> corrected {p['median_um']:.0f} um, ratio "
                  f"{p['ratio_corrected']:.2f}{tag}")
        if len(clean) < 3:
            letter, why = "e", "fewer than three accepted meshes"
            dlo = dhi = float("nan")
            print(f"\nVERDICT ({a.arm}): (e) {why}")
        else:
            med_by_mesh = np.array([p["median_um"] for p in clean])
            boot = np.random.default_rng(1)
            meds = [float(np.median(boot.choice(med_by_mesh,
                                                len(med_by_mesh))))
                    for _ in range(2000)]
            dlo = float(np.percentile(meds, 2.5))
            dhi = float(np.percentile(meds, 97.5))
            point = float(np.median(med_by_mesh))
            print(f"\naccepted meshes ({len(clean)}): medians "
                  f"{np.round(med_by_mesh, 1).tolist()} um")
            print(f"median across meshes: {point:.1f} um "
                  f"[95% {dlo:.1f}, {dhi:.1f}]")
            if rejected:
                print(f"rejected: {[p['mesh'] for p in rejected]}")
            letter, why = pitch_mod.verdict(point, dlo, dhi)
            print(f"\nVERDICT ({a.arm}, direct estimator across "
                  f"meshes): ({letter}) {why}")
            print("  note: each mesh median is an upper bound "
                  "(second-order sampling inflation, ~1.3%)")
            direct["median_across_meshes_um"] = point
            direct["ci95_across_meshes"] = [dlo, dhi]
            direct["n_meshes_used"] = len(clean)
            direct["rejected"] = [p["mesh"] for p in rejected]
    elif ok:
        letter, why = pitch_mod.verdict(limit, lo, hi)
        print(f"\nVERDICT ({a.arm}): ({letter}) {why}")
    else:
        letter = "e"
        why = ("extrapolation invalid: " + "; ".join(reasons))
        print(f"\nVERDICT ({a.arm}): (e) {why}")

    res = {"arm": a.arm, "points": int(len(xyz)),
           "direct_estimator": direct,
           "extrapolation_valid": bool(ok),
           "extrapolation_issues": reasons,
           "collections": int(len(np.unique(coll))),
           "estimator": "nearest adjacent-winding, "
                        "density-extrapolated (A6.1)",
           "limit_um": limit, "ci95_lo_um": lo, "ci95_hi_um": hi,
           "fit_r2": r2, "curve": curve,
           "allpairs_median_um": ap_med,
           "verdict": letter, "verdict_note": why,
           "claims": {"atlas_um": 187.3, "winding_sync_um": 225.0}}
    if a.out:
        json.dump(res, open(a.out, "w"), indent=2)
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
