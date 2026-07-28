"""gauge.gt - load human winding annotations into scoreable pairs.

Input format: VC3D point-collection JSON (the spiral-input datasets), i.e.

    {"collections": {"<cid>": {"points": {"<pid>": {"p": [x, y, z],
                                                    "wind_a": <float>}},
                               "metadata": {"winding_is_absolute": bool}}}}

Coordinates in "p" are full-resolution voxels, order [x, y, z] (pass
p_order="zyx" if a file disagrees). Winding differences are only
meaningful within a collection; pairs are built within-collection only,
which matches how the July concordance work used these files.
"""


import json

import numpy as np


def load_points(path, p_order="xyz"):
    """Return (xyz (N,3) float64 full-res, wind (N,), collection_id (N,))."""
    doc = json.load(open(path))
    xs, ws, cs = [], [], []
    for cid, col in doc["collections"].items():
        for _, pt in col.get("points", {}).items():
            p = pt["p"]
            if p_order == "zyx":
                p = [p[2], p[1], p[0]]
            xs.append(p)
            ws.append(float(pt["wind_a"]))
            cs.append(cid)
    return (np.asarray(xs, dtype=np.float64),
            np.asarray(ws, dtype=np.float64),
            np.asarray(cs, dtype=object))


def build_pairs(xyz, wind, coll, max_dw=6, max_pairs=None, seed=1):
    """Within-collection pairs with integer winding difference 1..max_dw.

    Vectorized per collection (mesh collections reach thousands of
    points). max_pairs: deterministic thinning cap on the TOTAL number
    of pairs, uniform over collections' pair pools (rng seeded).

    Returns dict of arrays: a_idx, b_idx (indices into xyz), dw (int,
    positive; a is the lower-winding point of the pair).
    """
    a_all, b_all, d_all = [], [], []
    for cid in np.unique(coll):
        idx = np.nonzero(coll == cid)[0]
        if len(idx) < 2:
            continue
        W = wind[idx]
        for a0 in range(0, len(idx), 2000):
            a1 = min(a0 + 2000, len(idx))
            dw = W[:, None] - W[None, a0:a1]          # (n, chunk)
            r = np.round(dw)
            m = (np.abs(dw - r) <= 1e-6) & (np.abs(r) >= 1) & \
                (np.abs(r) <= max_dw)
            ii, jj = np.nonzero(m)
            jj = jj + a0
            keep = ii > jj                            # each pair once
            ii, jj = ii[keep], jj[keep]
            rr = np.round(W[ii] - W[jj]).astype(int)
            lo = np.where(rr > 0, jj, ii)
            hi = np.where(rr > 0, ii, jj)
            a_all.append(idx[lo])
            b_all.append(idx[hi])
            d_all.append(np.abs(rr))
    if not a_all:
        return {"a": np.empty(0, int), "b": np.empty(0, int),
                "dw": np.empty(0, int)}
    a = np.concatenate(a_all)
    b = np.concatenate(b_all)
    d = np.concatenate(d_all)
    if max_pairs is not None and len(d) > max_pairs:
        sel = np.random.default_rng(seed).choice(len(d), size=max_pairs,
                                                 replace=False)
        sel.sort()
        a, b, d = a[sel], b[sel], d[sel]
    return {"a": a, "b": b, "dw": d}
