"""gauge.e1 - the E1 estimator of winding-ruler as a pairwise subject
(S-D, addenda A4 and A13).

Reimplements the prediction path of concordance/ruler_concordance_v1_5.py
verbatim: magnitude from the grad_mag ray integral scaled by k, sign from
the radial ordering about the umbilicus times orient.

    dw_pred = round(k * median_of_M_ray_integrals) * (orient * sign(r_b - r_a))

k and orient are NOT refitted here. They are the values the estimator
carried out of its development window (z10000-11000, split seed 2):

    k = 2.773, orient = +1

Refitting them per region would test the mechanism rather than the
calibration, and would apply a looser rule to this benchmark's own
estimator than A11 applies to anyone else's tool. So the frozen values
travel, and the held-out score is what they are worth outside the window
they came from.

Constants copied from the source: ENCODE_SCALE 1000, GRAD_MAG_FACTOR
0.25, LASAGNA_SCALE 4, trilinear sampling every 2 voxels, trapezoid
integration, 7 rays at +/- 6 voxels perpendicular in plane.
"""

import json
import os

import numpy as np
import zarr
from scipy.ndimage import map_coordinates

from gauge.pairwise import PairwiseResult

ENCODE_SCALE = 1000.0
GRAD_MAG_FACTOR = 0.25
DECODE = ENCODE_SCALE / GRAD_MAG_FACTOR
LASAGNA_SCALE = 4
K_FROZEN = 2.773
ORIENT_FROZEN = 1


def _ray_integral(sub, z0_full, a, b, sample_vx=2.0):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    dist = float(np.linalg.norm(b - a))
    if not (dist > 1e-9) or not np.isfinite(dist):
        return 0.0, True
    n = max(2, int(np.ceil(dist / sample_vx)) + 1)
    t = np.linspace(0.0, 1.0, n)
    pts = a[None, :] * (1.0 - t)[:, None] + b[None, :] * t[:, None]
    zi = (pts[:, 2] - z0_full) / LASAGNA_SCALE
    yi = pts[:, 1] / LASAGNA_SCALE
    xi = pts[:, 0] / LASAGNA_SCALE
    dz, dy, dx = sub.shape
    inside = (zi >= 0) & (zi <= dz - 1) & (yi >= 0) & (yi <= dy - 1) & \
             (xi >= 0) & (xi <= dx - 1)
    if not inside.all():
        return float("inf"), False
    dens = map_coordinates(sub, np.stack([zi, yi, xi]), order=1,
                           mode="nearest").astype(np.float64) / DECODE
    seg = dist / (n - 1)
    return float(np.sum(0.5 * (dens[:-1] + dens[1:]) * seg)), True


def _multiray(sub, z0_full, a, b, m_rays=7, max_offset_vx=6.0):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    d = b - a
    perp = np.array([-d[1], d[0], 0.0])
    nrm = np.linalg.norm(perp)
    if nrm < 1e-9:
        perp = np.array([1.0, 0.0, 0.0])
        nrm = 1.0
    perp /= nrm
    vals = []
    for off in np.linspace(-max_offset_vx, max_offset_vx, m_rays):
        v, ok = _ray_integral(sub, z0_full, a + perp * off, b + perp * off)
        if ok and np.isfinite(v):
            vals.append(v)
    if not vals:
        return float("inf"), False
    return float(np.median(vals)), True


def _load_umbilicus(dataset):
    d = json.load(open(os.path.join(dataset, "umbilicus.json")))
    if isinstance(d, dict):
        for key in ("control_points", "points", "umbilicus", "data"):
            if key in d and isinstance(d[key], (list, dict)):
                d = d[key]
                break
    if isinstance(d, dict):
        d = list(d.values())
    pts = []
    for item in d:
        if isinstance(item, dict):
            z, x, y = item.get("z"), item.get("x"), item.get("y")
            p = item.get("p")
            if p is not None and None in (z, x, y):
                x, y, z = float(p[0]), float(p[1]), float(p[2])
        else:
            x, y, z = float(item[0]), float(item[1]), float(item[2])
        if None not in (x, y, z):
            pts.append((float(z), float(x), float(y)))
    pts.sort()
    zs = np.array([p[0] for p in pts])
    xs = np.array([p[1] for p in pts])
    ys = np.array([p[2] for p in pts])

    def axis_xy(z):
        return (float(np.interp(z, zs, xs)), float(np.interp(z, zs, ys)))
    return axis_xy, len(pts)


def predict(gt_xyz, pairs, dataset, k=K_FROZEN, orient=ORIENT_FROZEN,
            band_vx=2000, margin_vx=64, name="E1", verbose=True):
    """Score every GT pair with the frozen E1.

    grad_mag is read in z bands so the whole volume is never resident.
    Pairs are grouped by the z of their midpoint; a pair whose ray leaves
    the loaded band or the volume is left unanswered, which costs
    coverage and never accuracy.
    """
    path = os.path.join(dataset, "lasagna_inputs",
                        "las_008_grad_mag.ome.zarr")
    arr = zarr.open(path, mode="r")["4"]
    axis_xy, n_umb = _load_umbilicus(dataset)
    if verbose:
        print(f"  E1: grad_mag {arr.shape}, umbilicus {n_umb} points, "
              f"k={k} orient={orient:+d} (frozen)")

    A = gt_xyz[pairs["a"]]
    B = gt_xyz[pairs["b"]]
    zmid = 0.5 * (A[:, 2] + B[:, 2])
    P = len(zmid)
    dw_pred = np.zeros(P)
    answered = np.zeros(P, dtype=bool)
    conf = np.zeros(P)

    order = np.argsort(zmid)
    bands = np.arange(zmid.min() - margin_vx, zmid.max() + band_vx,
                      band_vx)
    for b0 in bands:
        b1 = b0 + band_vx
        sel = order[(zmid[order] >= b0) & (zmid[order] < b1)]
        if len(sel) == 0:
            continue
        zlo = max(0.0, min(A[sel, 2].min(), B[sel, 2].min()) - margin_vx)
        zhi = max(A[sel, 2].max(), B[sel, 2].max()) + margin_vx
        z0 = int(zlo) // LASAGNA_SCALE
        z1 = min(arr.shape[0], (int(zhi) + LASAGNA_SCALE - 1) //
                 LASAGNA_SCALE + 1)
        if z1 <= z0:
            continue
        sub = np.asarray(arr[z0:z1, :, :])
        z0_full = z0 * LASAGNA_SCALE
        if verbose:
            print(f"    band z {int(zlo)}-{int(zhi)}: {len(sel)} pairs, "
                  f"grad_mag slab {sub.shape}")
        for i in sel:
            a, b = A[i], B[i]
            val, ok = _multiray(sub, z0_full, a, b)
            if not ok:
                continue
            ax, ay = axis_xy(0.5 * (a[2] + b[2]))
            ra = np.hypot(a[0] - ax, a[1] - ay)
            rb = np.hypot(b[0] - ax, b[1] - ay)
            rs = 1 if rb > ra else (-1 if rb < ra else 0)
            if rs == 0:
                continue
            dw_pred[i] = round(k * val) * (orient * rs)
            answered[i] = True
            # confidence: how far the scaled integral sits from the
            # rounding boundary. A value near .5 is a coin flip.
            frac = abs(k * val - round(k * val))
            conf[i] = 1.0 - 2.0 * frac
        del sub

    res = PairwiseResult(name, dw_pred, answered, conf)
    res.stats = {"k": k, "orient": int(orient), "frozen": True,
                 "source": "winding-ruler concordance v1_5",
                 "n_pairs": int(P), "n_answered": int(answered.sum())}
    return res
