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

    Memory is O(max_pairs), never O(all pairs): the pair count per
    (collection, w_lo, w_hi) block is computed from a winding histogram,
    which is exact and costs nothing, and each block is then sampled to
    its quota. Mesh collections reach 10^8+ pairs, so enumerating first
    and thinning after is not an option.

    Returns dict of arrays: a_idx, b_idx (indices into xyz), dw (int,
    positive; a is the lower-winding point of the pair). Collections
    with fewer than two windings contribute nothing.
    """
    rng = np.random.default_rng(seed)
    blocks = []          # (idx_lo, idx_hi, dw, n_pairs)
    total = 0
    for cid in np.unique(coll):
        idx = np.nonzero(coll == cid)[0]
        if len(idx) < 2:
            continue
        w = wind[idx]
        wr = np.round(w)
        integral = np.abs(w - wr) <= 1e-6
        idx, wr = idx[integral], wr[integral].astype(int)
        if len(idx) < 2:
            continue
        levels, inv = np.unique(wr, return_inverse=True)
        if len(levels) < 2:
            continue
        buckets = [idx[inv == k] for k in range(len(levels))]
        for a in range(len(levels)):
            for b in range(a + 1, len(levels)):
                dw = int(levels[b] - levels[a])
                if dw < 1 or dw > max_dw:
                    continue
                n = len(buckets[a]) * len(buckets[b])
                if n:
                    blocks.append((buckets[a], buckets[b], dw, n))
                    total += n
    if not blocks:
        return {"a": np.empty(0, int), "b": np.empty(0, int),
                "dw": np.empty(0, int)}

    frac = 1.0 if (max_pairs is None or total <= max_pairs) \
        else max_pairs / total
    A, B, D = [], [], []
    for lo, hi, dw, n in blocks:
        if frac >= 1.0:
            g = np.meshgrid(np.arange(len(lo)), np.arange(len(hi)),
                            indexing="ij")
            ia, ib = g[0].ravel(), g[1].ravel()
        else:
            k = int(round(n * frac))
            if k == 0:
                continue
            flat = rng.choice(n, size=k, replace=False)
            ia, ib = np.divmod(flat, len(hi))
        A.append(lo[ia]), B.append(hi[ib])
        D.append(np.full(len(ia), dw, dtype=int))
    return {"a": np.concatenate(A), "b": np.concatenate(B),
            "dw": np.concatenate(D)}
