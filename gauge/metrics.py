"""gauge.metrics - M1..M4 from GATE0 section 4 (sealed).

M1  exact agreement on dw=1 pairs (scorable only)
M2  mean absolute residual |dw_pred - dw_human| over scorable pairs
M3  calibration: pair confidence (min of endpoint confs) vs empirical
    accuracy, 10 quantile bins. Classic ECE is undefined here because
    confidences are arbitrary monotone scales, so M3_ece_rank is
    reported instead: the same weighted deviation with the confidence
    replaced by its normalized rank (A20 item 7)
M4  coverage: fraction of GT pairs scorable

Every public figure must be derived from the per-pair CSV this module
emits, never typed by hand (aggregate rule).
"""

import csv

import numpy as np


def score(pairs, mres, adapter):
    """Per-pair table as dict of arrays (scorable pairs only).

    gt_a/gt_b identify the pair: indices into the GT point set used in
    this run (after any A9 slab restriction), so two runs of the same
    configuration can be compared pair by pair instead of by position
    (added after the v0.2.0 rerun needed exactly that)."""
    s = mres.scorable
    a, b = mres.a_pt[s], mres.b_pt[s]
    dw_pred = adapter.winding[b] - adapter.winding[a]
    dw_true = pairs["dw"][s].astype(float)
    conf = np.minimum(adapter.conf[a], adapter.conf[b])
    return {
        "gt_a": pairs["a"][s],
        "gt_b": pairs["b"][s],
        "dw_true": dw_true,
        "dw_pred": dw_pred,
        "dw_pred_round": np.round(dw_pred),
        "hit": np.round(dw_pred) == dw_true,
        "conf": conf,
        "a_dist": mres.a_dist[s],
        "b_dist": mres.b_dist[s],
    }


def summarize(pairs, mres, table, n_bins=10):
    s = mres.scorable
    out = {}
    out["n_pairs_gt"] = int(len(pairs["dw"]))
    out["n_scorable"] = int(s.sum())
    out["M4_coverage"] = float(s.mean()) if len(s) else 0.0

    dw1 = table["dw_true"] == 1
    out["n_dw1"] = int(dw1.sum())
    out["M1_exact_dw1"] = float(table["hit"][dw1].mean()) if dw1.any() else float("nan")
    out["M2_mae"] = float(np.abs(table["dw_pred"] - table["dw_true"]).mean()) \
        if len(table["dw_true"]) else float("nan")

    # M3: quantile bins over pair confidence
    conf, hit = table["conf"], table["hit"].astype(float)
    bins = []
    if len(conf) >= n_bins:
        qs = np.quantile(conf, np.linspace(0, 1, n_bins + 1))
        qs[-1] += 1e-9
        ece_num = 0.0
        for k in range(n_bins):
            m = (conf >= qs[k]) & (conf < qs[k + 1])
            if not m.any():
                continue
            bins.append({"bin": k, "n": int(m.sum()),
                         "conf_mean": float(conf[m].mean()),
                         "acc": float(hit[m].mean())})
            ece_num += m.sum() * abs(hit[m].mean() -
                                     _rank01(conf, m))
        out["M3_bins"] = bins
        out["M3_ece_rank"] = float(ece_num / len(conf))
    else:
        out["M3_bins"] = bins
        out["M3_ece_rank"] = float("nan")
    out["M3_note"] = ("confidence is an arbitrary monotone scale; the "
                      "curve shows whether higher conf means higher "
                      "accuracy, not absolute probabilities")
    return out


def _rank01(conf, mask):
    """Mean normalized rank of the selected confidences (0..1)."""
    order = conf.argsort().argsort() / max(1, len(conf) - 1)
    return float(order[mask].mean())


def write_csv(path, table):
    keys = list(table)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keys)
        for row in zip(*(table[k] for k in keys)):
            w.writerow(row)
