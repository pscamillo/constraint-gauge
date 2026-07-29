"""gauge.pairwise - subjects that predict dw for a PAIR, not winding per
point (addendum A13).

Two families of generator exist in this problem. One assigns a winding
number to every point it emits and the bench matches ground-truth points
to those nodes (gauge.adapters.AdapterResult). The other answers a
question about two given points: how many windings apart are they. The
E1 estimator of winding-ruler is of the second kind, and so are ray- or
integral-based predictors generally.

For a pairwise subject the matching rule of section 3 does not apply at
all: the subject is handed the ground-truth pair itself, so there is no
nearest-node search and no tolerance. Coverage (M4) becomes the fraction
of GT pairs the subject can answer, which for an integral-based
estimator is the fraction whose ray stays inside the available volume.
M1 and M2 are computed exactly as before.

This makes pairwise subjects EASIER on coverage and neither easier nor
harder on accuracy: they are asked precisely the question the bench
scores, with no localisation step in between. Any comparison with a
node-based subject must carry that difference, which is why the summary
records subject_kind.
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class PairwiseResult:
    """What a pairwise subject returns for a set of GT pairs.

    dw_pred   (P,) predicted signed winding difference, b minus a
    answered  (P,) bool, False where the subject declines (no coverage)
    conf      (P,) confidence per pair, any monotone scale
    """
    name: str
    dw_pred: np.ndarray
    answered: np.ndarray
    conf: np.ndarray = None
    stats: dict = field(default_factory=dict)

    def __post_init__(self):
        self.dw_pred = np.asarray(self.dw_pred, dtype=np.float64)
        self.answered = np.asarray(self.answered, dtype=bool)
        if self.conf is None:
            self.conf = np.ones(len(self.dw_pred))
        self.conf = np.asarray(self.conf, dtype=np.float64)
        n = len(self.dw_pred)
        assert self.answered.shape == (n,) and self.conf.shape == (n,)


def score_pairs(pairs, result):
    """Per-pair table for a pairwise subject, same columns as the
    node-based path so the metrics code is shared."""
    m = result.answered
    dw_true = pairs["dw"][m].astype(float)
    dw_pred = result.dw_pred[m]
    return {
        "dw_true": dw_true,
        "dw_pred": dw_pred,
        "dw_pred_round": np.round(dw_pred),
        "hit": np.round(dw_pred) == dw_true,
        "conf": result.conf[m],
        "a_dist": np.zeros(m.sum()),     # no matching step
        "b_dist": np.zeros(m.sum()),
    }


def summarize_pairs(pairs, result, table, n_bins=10):
    from gauge import metrics
    out = {}
    n = len(pairs["dw"])
    out["n_pairs_gt"] = int(n)
    out["n_scorable"] = int(result.answered.sum())
    out["M4_coverage"] = float(result.answered.mean()) if n else 0.0
    dw1 = table["dw_true"] == 1
    out["n_dw1"] = int(dw1.sum())
    out["M1_exact_dw1"] = float(table["hit"][dw1].mean()) if dw1.any() \
        else float("nan")
    out["M2_mae"] = float(np.abs(table["dw_pred"] -
                                 table["dw_true"]).mean()) \
        if len(table["dw_true"]) else float("nan")
    conf, hit = table["conf"], table["hit"].astype(float)
    bins = []
    ece_num = 0.0
    if len(conf) >= n_bins and len(np.unique(conf)) > 1:
        from gauge.metrics import _rank01
        qs = np.quantile(conf, np.linspace(0, 1, n_bins + 1))
        qs[-1] += 1e-9
        for k in range(n_bins):
            sel = (conf >= qs[k]) & (conf < qs[k + 1])
            if sel.any():
                bins.append({"bin": k, "n": int(sel.sum()),
                             "conf_mean": float(conf[sel].mean()),
                             "acc": float(hit[sel].mean())})
                ece_num += sel.sum() * abs(hit[sel].mean() -
                                           _rank01(conf, sel))
        out["M3_ece_rank"] = float(ece_num / len(conf))
    else:
        out["M3_ece_rank"] = float("nan")
    out["M3_bins"] = bins
    out["subject_kind"] = "pairwise"
    return out
