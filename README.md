# constraint-gauge

A calibration benchmark for winding constraint generators in the
Vesuvius Challenge. It scores any generator per location against human
winding annotations, and reports whether its confidence means anything.

The winding constraints page lists "accurate (or have some way to
measure its confidence/accuracy)" as the first requirement for an ideal
generator. No shared instrument for that exists. This is one.

## How it works

Ground truth, two arms. Human point collections (PHerc Paris 4, 8156
within-collection pairs at dw 1-6). And human-verified segment meshes,
which state sheet identity by construction and come about 19x denser:
the extractor counts a segment's own wraps with no axis and no spacing
constant, one collection per mesh, seam wraps trimmed.

A generator provides points, a winding number per point, and a
confidence per point. That's the whole interface. If you don't want to
touch python, dump it as json:

    {"name": "...", "points_xyz": [[x,y,z], ...],
     "winding": [...], "conf": [...]}

    python run_gauge.py --gt relative_windings.json \
        --adapter json:yours.json --pitch-um 180 --um-per-vox 2.4

Matching tolerance is measured, not assumed: at each ground-truth point
it is half the distance to the nearest annotated neighbor on an
adjacent winding. No spacing constant, no umbilicus, no radial model.
Sparse regions fall back to the tightest available estimate. Tighter
costs coverage, never accuracy.

Metrics, fixed before any measurement: exact agreement on dw=1 pairs,
mean absolute residual, a confidence vs accuracy calibration curve, and
coverage. Every published figure is derived from the per-pair csv the
runner writes, never typed by hand.

## The rules were sealed first

GATE0_criteria.md in this repo was written, reviewed and hashed before
any external generator was measured:

    sha256 d4da5eb9f7e8ce4b2c372c19d9830b229218b8e2777ef3dfcc9a2332f0bcd064

That hash still verifies against the root commit. The matching rule,
the metrics, the subjects and the verdict criteria for the open pitch
question are all in there. Changes happen as dated addenda, never
edits.

## Status

The bench is open. run_gauge.py works today via the json adapter,
self-tested on the full Paris 4 annotations (8156 pairs, M1 1.000).
Mesh extraction validated on GP segment 20231022170901: 8 wraps,
matching an independent count.

Subjects so far: winding-sync (abundantjoe), BFS on the same graph as
the baseline, E1 (mine, held out on pairs it never saw), angle-binned
radial pitch (alyalya), constraint chain (Iyán Dopico). Every subject
declares provenance against each GT arm; results are labeled
independent / shared-parent / in-sample, and no number about a
generator goes public before its author has seen it.

Today's addenda came from review by Paul Henderson, sean (bruniss),
Iyán Dopico and alyalya, before any subject was scored.

MIT.
