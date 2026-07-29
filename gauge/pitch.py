"""gauge.pitch - spacing estimation and the 225-vs-187 arbitration
(GATE0 section 6, addendum A6.1).

The judge is the physical distance between human-annotated points on
ADJACENT windings. Two estimators are reported side by side, because
they answer different questions and disagree in a known direction:

  nearest   distance from each point to its NEAREST adjacent-winding
            neighbour, median over points. This is the quantity a
            constraint generator actually competes against (it is
            exactly 2 x the A2.2 tolerance), and it is an UPPER BOUND
            on true sheet spacing: two annotated points are rarely
            perpendicular across the gap, so any measured distance is
            at least the perpendicular one.

  allpairs  median over ALL adjacent-winding pairs. The literal reading
            of 6.1, reported for completeness. Strongly biased upward
            (it includes pairs far apart along the sheet), so it is a
            ceiling, not a competitor.

Convergence (A6.1): the nearest estimator's upward bias shrinks as
sampling gets denser, since a closer perpendicular partner becomes
available. Sampling the same arm at several densities therefore traces
a decreasing curve whose limit is the physical spacing. The curve is
the result; a single number from a single density is not.

Verdicts are those pre-registered in 6.2 (a) 187 compatible, 225 not;
(b) 225 compatible, 187 not; (c) both, in different regimes; (d)
neither; (e) GT insufficient to decide.
"""

import numpy as np

from gauge.localtau import gt_local_tau


def nearest_spacing_um(xyz, wind, coll, um_per_vox):
    """Per-point distance to the nearest adjacent-winding neighbour,
    in micrometres. This is 2 x the A2.2 tolerance by construction."""
    tau = gt_local_tau(xyz, wind, coll)
    return 2.0 * tau[np.isfinite(tau)] * um_per_vox


def allpairs_spacing_um(xyz, pairs, um_per_vox, max_pairs=200000,
                        seed=1):
    """Distance over all scored dw=1 pairs, in micrometres."""
    m = pairs["dw"] == 1
    a, b = pairs["a"][m], pairs["b"][m]
    if len(a) > max_pairs:
        sel = np.random.default_rng(seed).choice(len(a), max_pairs,
                                                 replace=False)
        a, b = a[sel], b[sel]
    return np.linalg.norm(xyz[a] - xyz[b], axis=1) * um_per_vox


def convergence(xyz, wind, coll, um_per_vox, fractions=(0.05, 0.1, 0.25,
                                                        0.5, 1.0),
                seed=1):
    """Nearest-estimator median at several sampling densities.

    Returns a list of dicts with the fraction kept, the resulting point
    count, and the median/quartiles of the estimate. A decreasing
    sequence is the expected signature of an upper-bound estimator
    converging from above.
    """
    rng = np.random.default_rng(seed)
    n = len(xyz)
    out = []
    for f in fractions:
        if f >= 1.0:
            sel = np.arange(n)
        else:
            sel = rng.choice(n, size=max(2, int(n * f)), replace=False)
            sel.sort()
        s = nearest_spacing_um(xyz[sel], wind[sel], coll[sel], um_per_vox)
        if len(s) < 10:
            continue
        out.append({"fraction": f, "points": int(len(sel)),
                    "n_est": int(len(s)),
                    "median_um": float(np.median(s)),
                    "q1_um": float(np.percentile(s, 25)),
                    "q3_um": float(np.percentile(s, 75))})
    return out


def extrapolate(curve):
    """Limit of the convergence curve as density grows.

    Geometry of the estimator: the nearest adjacent-winding partner sits
    at sqrt(d^2 + r^2), where d is the perpendicular spacing and r the
    lateral offset to the closest sampled point, with r^2 ~ A/n. So the
    convergence law is QUADRATIC in the estimate,

        median^2 = d^2 + b/n

    and a linear fit of median^2 against 1/n gives d^2 as the intercept.
    (A linear fit of median against n^-1/2 underestimates by ~16% on
    synthetic sheets of known spacing; see tests/test_pitch.py.)

    Returns (limit_um, slope, r2) or (nan, nan, nan) with fewer than
    three densities.
    """
    if len(curve) < 3:
        return float("nan"), float("nan"), float("nan")
    n = np.array([c["n_est"] for c in curve], float)
    y = np.array([c["median_um"] for c in curve], float) ** 2
    x = 1.0 / n
    A = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    limit = float(np.sqrt(coef[0])) if coef[0] > 0 else float("nan")
    return limit, float(coef[1]), r2


def verdict(limit_um, ci_lo, ci_hi, claims=((187.3, "atlas"),
                                            (225.0, "winding-sync"))):
    """Pre-registered verdict from 6.2, applied to an interval."""
    inside = [(v, n) for v, n in claims if ci_lo <= v <= ci_hi]
    if len(inside) == 1:
        other = [n for v, n in claims if (v, n) not in inside]
        return ("a" if inside[0][0] < 200 else "b",
                f"{inside[0][0]} ({inside[0][1]}) compatible, "
                f"{', '.join(other)} not")
    if len(inside) == len(claims):
        return "c", "both claims fall inside the interval"
    if not inside:
        return "d", "neither claim falls inside the interval"
    return "e", "ground truth insufficient to decide"


def extrapolate_ci(xyz, wind, coll, um_per_vox, n_boot=40,
                   fractions=(0.05, 0.1, 0.25, 0.5, 1.0), seed=1):
    """Bootstrap interval on the extrapolated limit.

    Each replicate resamples the GT points with replacement, rebuilds
    the whole convergence curve on the replicate, and refits. Returns
    (limit, lo, hi, r2_median, curve) with lo/hi the 2.5 and 97.5
    percentiles across replicates.
    """
    curve = convergence(xyz, wind, coll, um_per_vox, fractions, seed)
    limit, _, r2 = extrapolate(curve)
    rng = np.random.default_rng(seed)
    n = len(xyz)
    lims, r2s = [], []
    for _ in range(n_boot):
        sel = rng.integers(0, n, size=n)
        c = convergence(xyz[sel], wind[sel], coll[sel], um_per_vox,
                        fractions, seed)
        li, _, rr = extrapolate(c)
        if np.isfinite(li):
            lims.append(li), r2s.append(rr)
    if len(lims) < 5:
        return limit, float("nan"), float("nan"), r2, curve
    return (limit, float(np.percentile(lims, 2.5)),
            float(np.percentile(lims, 97.5)),
            float(np.median(r2s)), curve)


def validate_extrapolation(limit, lo, hi, curve, min_r2=0.9,
                           plateau_tol=0.10):
    """Validity gate for a density-extrapolated estimate (A6.3).

    An extrapolated limit may only support a verdict if
      1. the fit explains the curve: r2 >= min_r2
      2. the point estimate lies inside its own bootstrap interval
      3. the curve has reached a plateau: the last two densities differ
         by less than plateau_tol
    Otherwise the arm returns verdict (e), ground truth insufficient.

    Returns (ok, reasons) with reasons listing every failed check.
    """
    reasons = []
    n = np.array([c["n_est"] for c in curve], float)
    y = np.array([c["median_um"] for c in curve], float) ** 2
    x = 1.0 / n
    A = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(((y - pred) ** 2).sum()) / ss_tot if ss_tot > 0 \
        else float("nan")
    if not (r2 >= min_r2):
        reasons.append(f"fit r2 {r2:.3f} < {min_r2}")
    if not (np.isfinite(limit) and lo <= limit <= hi):
        reasons.append(f"point estimate {limit:.1f} outside its own "
                       f"interval [{lo:.1f}, {hi:.1f}]")
    med = [c["median_um"] for c in curve]
    if len(med) >= 2:
        rel = abs(med[-1] - med[-2]) / max(med[-1], 1e-9)
        if rel > plateau_tol:
            reasons.append(f"curve has not reached a plateau: last two "
                           f"densities differ by {rel:.0%}")
    return (len(reasons) == 0), reasons
