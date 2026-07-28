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

import itertools
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


def build_pairs(xyz, wind, coll, max_dw=6):
    """Within-collection pairs with integer winding difference 1..max_dw.

    Returns dict of arrays: a_idx, b_idx (indices into xyz), dw (int,
    positive; a is the lower-winding point of the pair).
    """
    a_idx, b_idx, dws = [], [], []
    for cid in np.unique(coll):
        idx = np.nonzero(coll == cid)[0]
        for i, j in itertools.combinations(idx, 2):
            dw = wind[j] - wind[i]
            r = round(dw)
            if abs(dw - r) > 1e-6 or r == 0 or abs(r) > max_dw:
                continue
            if r > 0:
                a_idx.append(i), b_idx.append(j), dws.append(int(r))
            else:
                a_idx.append(j), b_idx.append(i), dws.append(int(-r))
    return {"a": np.asarray(a_idx, dtype=int),
            "b": np.asarray(b_idx, dtype=int),
            "dw": np.asarray(dws, dtype=int)}
