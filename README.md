# constraint-gauge

A calibration benchmark for winding constraint generators in the
Vesuvius Challenge. It scores any generator per location against human
winding annotations, and reports whether its confidence means anything.

The winding constraints page lists "accurate (or have some way to
measure its confidence/accuracy)" as the first requirement for an ideal
generator. No shared instrument for that exists. This is one.

## How it works

Ground truth: human winding annotations from the published point
collections (PHerc Paris 4, 8156 within-collection pairs at dw 1-6) and
the stitched instance labels on PHerc1218 (9k pairs). GP segment meshes
are the next source, with wrap overlap accounted for.

A generator provides points, a winding number per point, and a
confidence per point. That's the whole interface. If you don't want to
touch python, dump it as json:

    {"name": "...", "points_xyz": [[x,y,z], ...],
     "winding": [...], "conf": [...]}

    python run_gauge.py --gt relative_windings.json \
        --adapter json:yours.json --pitch-um 187.3 --um-per-vox 2.4

Metrics, fixed before any measurement: exact agreement on dw=1 pairs,
mean absolute residual, a confidence vs accuracy calibration curve, and
coverage. Every published figure is derived from the per-pair csv the
runner writes, never typed by hand.

## The rules were sealed first

GATE0_criteria.md in this repo was written, reviewed and hashed before
any external generator was measured:

    sha256 d4da5eb9f7e8ce4b2c372c19d9830b229218b8e2777ef3dfcc9a2332f0bcd064

The matching rule, the metrics, the subjects and the verdict criteria
for the open pitch question (225 vs 187 um) are all in there and cannot
change now. Additions happen as dated addenda, never edits.

First subjects: winding-sync (abundantjoe), BFS on the same graph as
the baseline, and my own E1 estimator, scored held-out on pairs it
never saw during development. No number about anyone's generator goes
public before its author has seen it.

## Status

Harness validated on synthetic ground truth with known answers and on
the real Paris 4 annotations (reproduces the 706-pair z10000-11000
window from the July concordance work exactly). First real scores
pending author confirmation of the winding-sync entry point.

MIT.
