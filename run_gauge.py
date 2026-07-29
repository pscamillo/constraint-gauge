#!/usr/bin/env python3
"""run_gauge.py - score one constraint generator against human annotations.

    python run_gauge.py --gt relative_windings.json \
        --adapter json:result.json --subject E1 \
        --gt-arm paris4-annotations \
        --pitch-um 180 --um-per-vox 2.4 \
        --out-prefix paris4_e1

    python run_gauge.py --gt-mesh data/gp_meshes \
        --adapter json:result.json --subject winding-sync/l1 \
        --gt-arm paris4-meshes --pitch-um 180 --um-per-vox 2.4 \
        --out-prefix paris4_meshes_ws

Ground truth arms: --gt for annotated point collections, --gt-mesh for
a directory of verified segment meshes (A3.1/A3.2), one collection per
mesh.

Adapters:  json:PATH                     AdapterResult as JSON
           windingsync:SCROLL:Z[:LEVEL[:STRIDE_UM]]
                                         winding-sync L1 on that slice
           bfs:SCROLL:Z[:LEVEL[:STRIDE_UM]]
                                         BFS baseline, identical graph
           (Z is full-resolution; LEVEL defaults to 2; STRIDE_UM
            overrides the author's TracingConfig and makes the run OUR
            variant, labelled winding-sync/<solver>@stride<N> per A11)

tau is measured, not assumed: half the distance from each GT point to
its nearest adjacent-winding neighbour (A2.2), falling back to the
radial table and then the median. Every result carries its provenance
label against the arm it was scored on (A7); an undeclared line must
not be published.

Outputs: <prefix>_pairs.csv (per-pair table, the source of truth) and
<prefix>_summary.json. Diagnostic runs at tau/2 and 2tau are printed
but never primary (3.6).
"""

import argparse
import json
import os

import numpy as np

from gauge import gt as gt_mod
from gauge import adapters, match, metrics, provenance, density


def build_adapter(spec):
    kind, _, rest = spec.partition(":")
    if kind == "json":
        return adapters.load_json(rest)
    if kind in ("windingsync", "bfs", "bfssingle"):
        parts = rest.split(":")
        scroll, z = parts[0], int(parts[1])
        level = int(parts[2]) if len(parts) > 2 else 2
        stride = float(parts[3]) if len(parts) > 3 else None
        solver = {"windingsync": "l1", "bfs": "bfs",
                  "bfssingle": "bfs-single"}[kind]
        return adapters.from_winding_sync(scroll, z, level=level,
                                          solver=solver,
                                          seed_stride_um=stride)
    raise SystemExit(f"unknown adapter spec: {spec}")


def load_mesh_arm(root, stride=10):
    """Every mesh under root becomes its own collection (A3.1)."""
    import glob
    from gauge.meshgt import load_mesh_gt
    X, W, C = [], [], []
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(d):
            continue
        # adaptive trim: seam guard only when >= 2 windings survive it.
        # A collection with a single winding yields no dw>=1 pair and no
        # measured tau, so it is dropped rather than carried as fallback.
        for trim in (1, 0):
            try:
                x, w, c, info = load_mesh_gt(d, stride=stride,
                                             trim_wraps=trim)
            except ValueError:
                continue
            if len(np.unique(np.round(w))) < 2:
                if trim == 1:
                    continue          # try again without the seam trim
                print(f"  {os.path.basename(d)}: dropped, "
                      f"{info['n_wraps']} wrap(s), no adjacent pair")
                break
            X.append(x), W.append(w), C.append(c)
            print(f"  {os.path.basename(d)}: {info['n_wraps']} wraps, "
                  f"{info['points']} pts, trim={trim}, "
                  f"{len(np.unique(np.round(w)))} windings")
            break
        else:
            print(f"  {os.path.basename(d)}: skipped, too few wraps")
    if not X:
        raise SystemExit(f"no usable meshes under {root}")
    return (np.vstack(X), np.concatenate(W), np.concatenate(C))


def gt_local_tau_probe(xyz, wind, coll, pitch_um, um_per_vox):
    """Tolerance used to decide slab membership: the same A2.2 measure,
    with the median fallback where it is undefined."""
    from gauge.localtau import gt_local_tau
    t = gt_local_tau(xyz, wind, coll)
    med = match.tau_vox(pitch_um, um_per_vox)
    return np.where(np.isfinite(t), t, med)


def run(gt_path, adapter, pitch_um, um_per_vox, p_order, out_prefix,
        pitch_table=None, gt_mesh=None, subject=None, gt_arm=None,
        max_pairs=None, mesh_stride=10):
    if gt_mesh:
        print(f"gt arm: meshes under {gt_mesh} (stride {mesh_stride})")
        xyz, wind, coll = load_mesh_arm(gt_mesh, stride=mesh_stride)
    else:
        xyz, wind, coll = gt_mod.load_points(gt_path, p_order=p_order)
    # A9: for a single-plane adapter, restrict the GT to the slab the
    # generator can reach BEFORE building pairs. Sampling pairs from the
    # whole arm and filtering afterwards wastes the entire budget on
    # regions the generator does not cover.
    planar = len(np.unique(np.round(adapter.points_xyz[:, 2], 3))) == 1
    if planar:
        zp = float(adapter.points_xyz[0, 2])
        tau_probe = gt_local_tau_probe(xyz, wind, coll, pitch_um,
                                       um_per_vox)
        keep = np.abs(xyz[:, 2] - zp) <= tau_probe
        n_before = len(xyz)
        xyz, wind, coll = xyz[keep], wind[keep], coll[keep]
        print(f"  single-plane adapter at z={zp:.0f}: A9 slab keeps "
              f"{len(xyz)} of {n_before} gt points "
              f"({len(np.unique(coll))} collections)")
        if len(xyz) < 4:
            raise SystemExit("A9 slab too thin: fewer than 4 gt points "
                             "within tolerance of the adapter plane")
    pairs = gt_mod.build_pairs(xyz, wind, coll, max_pairs=max_pairs)
    tau_med = match.tau_vox(pitch_um, um_per_vox)
    from gauge.localtau import gt_local_tau, combine_tau
    tau_gt = gt_local_tau(xyz, wind, coll)          # A2.2 primary
    cands = [tau_gt]
    if pitch_table:
        from gauge.localtau import PitchTable
        pt = PitchTable.load(pitch_table, median_um=pitch_um)
        pt.resolve_axis(xyz)
        cands.append(pt.tau_vox_at(xyz))            # A2.1 fallback
    cands.append(np.full(len(xyz), tau_med))        # 3.3 last resort
    tau = combine_tau(*cands)
    n_gt = int(np.isfinite(tau_gt).sum())
    print(f"gt: {len(xyz)} points, {len(pairs['dw'])} pairs; "
          f"tau A2.2 on {n_gt}/{len(xyz)} points, "
          f"range {tau.min():.1f}-{tau.max():.1f} vox "
          f"(median fallback {tau_med:.1f})")

    # A10: precondition. A generator sparser than the sheets cannot be
    # scored per location at all, and a low score would misdescribe it.
    dens_ok, dens = density.check(adapter.points_xyz, tau, planar=planar,
                                  gt_xyz=xyz)
    print(f"  density gate (A10): node gap "
          f"{dens['node_gap_vox']:.1f} vox, sheet gap "
          f"{dens['sheet_gap_vox']:.1f} vox, ratio "
          f"{dens['ratio']:.2f} -> "
          f"{'SCORABLE' if dens_ok else 'NOT SCORABLE'}")
    if not dens_ok:
        print("  the generator emits nodes coarser than the sheets, so a "
              "ground-truth point has no node of its own and any winding "
              "difference read here is arbitrary. Reporting the ratio "
              "instead of a score.")

    for label, t in [("tau/2", tau / 2), ("tau", tau), ("2tau", tau * 2)]:
        mres = match.match(xyz, pairs, adapter, t, planar=planar)
        table = metrics.score(pairs, mres, adapter)
        summ = metrics.summarize(pairs, mres, table)
        line = (f"  [{label:5s}] scorable {summ['n_scorable']:5d} "
                f"(M4 {summ['M4_coverage']:.3f})  "
                f"M1 {summ['M1_exact_dw1']:.3f}  M2 {summ['M2_mae']:.3f}")
        print(line)
        if label == "tau":
            metrics.write_csv(f"{out_prefix}_pairs.csv", table)
            summ["adapter"] = adapter.name
            summ["planar_matching"] = bool(planar)
            summ["density_gate"] = dens
            summ["scorable"] = bool(dens_ok)
            if not dens_ok:
                summ["not_scorable_reason"] = (
                    "generator node gap exceeds sheet gap (A10); metrics "
                    "below are not a statement about its accuracy")
            if planar:
                summ["adapter_z"] = float(adapter.points_xyz[0, 2])
            if hasattr(adapter, "stats"):
                summ["adapter_stats"] = adapter.stats
            summ["subject"] = subject or adapter.name
            summ["gt_arm"] = gt_arm or ("paris4-meshes" if gt_mesh
                                        else "paris4-annotations")
            lab, note = provenance.label_for(summ["subject"],
                                             summ["gt_arm"])
            summ["provenance"] = lab
            summ["provenance_note"] = note
            summ["publishable_as_headline"] = provenance.publishable(lab)
            print(f"  provenance: {summ['subject']} vs "
                  f"{summ['gt_arm']} -> {lab.upper()}"
                  + ("" if provenance.publishable(lab)
                     else "  (label required when reporting)"))
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
    ap.add_argument("--gt", default=None,
                    help="annotated point collection json")
    ap.add_argument("--gt-mesh", default=None,
                    help="directory of verified segment meshes")
    ap.add_argument("--subject", default=None,
                    help="subject id for the provenance registry (A7)")
    ap.add_argument("--gt-arm", default=None,
                    help="gt arm id for the provenance registry (A7)")
    ap.add_argument("--mesh-stride", type=int, default=10,
                    help="grid subsampling when extracting mesh gt")
    ap.add_argument("--max-pairs", type=int, default=None,
                    help="deterministic cap on scored pairs")
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--pitch-um", type=float, required=True)
    ap.add_argument("--um-per-vox", type=float, required=True)
    ap.add_argument("--p-order", default="xyz", choices=["xyz", "zyx"])
    ap.add_argument("--out-prefix", default="gauge_run")
    ap.add_argument("--pitch-table", default=None,
                    help="per-scroll radial pitch table json (A2.1 local tau)")
    a = ap.parse_args()
    if not a.gt and not a.gt_mesh:
        raise SystemExit("need --gt or --gt-mesh")
    run(a.gt, build_adapter(a.adapter), a.pitch_um, a.um_per_vox,
        a.p_order, a.out_prefix, pitch_table=a.pitch_table,
        gt_mesh=a.gt_mesh, subject=a.subject, gt_arm=a.gt_arm,
        max_pairs=a.max_pairs, mesh_stride=a.mesh_stride)


if __name__ == "__main__":
    main()
