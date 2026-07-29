# constraint-gauge

A calibration benchmark for winding constraint generators in the
Vesuvius Challenge. It scores any generator per location against human
winding annotations, and reports whether its confidence means anything.

The winding constraints page lists "accurate (or have some way to
measure its confidence/accuracy)" as the first requirement for an ideal
generator. No shared instrument for that exists. This is one.

## Submitting a generator

One file. Points, a winding number per point, a confidence per point:

    {"name": "my-generator",
     "points_xyz": [[x, y, z], ...],
     "winding":    [12, 12, 13, ...],
     "conf":       [0.9, 0.4, 0.8, ...]}

Rules for the file, all of which matter:

- **Coordinates are full-resolution voxels of the volume the arm uses.**
  The two ground-truth arms live in different volumes: the annotated arm
  in the 7.91 um volume, the mesh arm in the 2.4 um one. Pick the arm
  you are targeting and use its frame.
- **Winding may be relative.** Only differences are scored, so any
  global offset is fine. Orientation must be consistent within a
  collection.
- **Confidence may be any monotone scale.** It is used for the
  calibration curve, never as a weight. Pass ones if your generator has
  no confidence notion.
- **A single-plane generator is fine.** If every point shares one z, the
  bench switches to planar matching automatically.

Then:

    # annotated arm
    python run_gauge.py --gt relative_windings.json \
        --adapter json:yours.json --subject my-generator \
        --gt-arm paris4-annotations \
        --pitch-um 180 --um-per-vox 7.91 \
        --out-prefix results/mine_annotations

    # verified-mesh arm
    python run_gauge.py --gt-mesh data/gp_meshes --mesh-stride 4 \
        --adapter json:yours.json --subject my-generator \
        --gt-arm paris4-meshes \
        --pitch-um 180 --um-per-vox 2.4 --max-pairs 40000 \
        --out-prefix results/mine_meshes

Output is `<prefix>_pairs.csv`, one row per scored pair and the source
of every figure, plus `<prefix>_summary.json`.

## What the bench checks before it scores anything

**Density.** A generator can only say which sheet a point is on where it
emits nodes finer than the sheets. If the typical gap between your
nodes exceeds the local sheet spacing, the run is reported NOT SCORABLE
with the ratio, never as a low score: a low score would be a claim about
your accuracy, and that is not one. On PHerc Paris 4 the sheets sit
about 75 voxels apart.

**Provenance.** Every subject declares, per ground-truth arm, whether it
is `independent`, `shared-parent` (it derives from data the GT also
derives from) or `in-sample` (it was developed on those very pairs).
Declarations live in `data/provenance.json` and every result carries its
label. An undeclared line must not be published. The rule applies to the
author of this bench too: the E1 estimator here is `in-sample` on the
window it was calibrated on, and only its held-out line is comparable
with anyone else's.

## How ground truth is built

**Annotated arm.** Human point collections, 8156 within-collection pairs
at dw 1-6 on PHerc Paris 4.

**Verified-mesh arm.** Human-verified GP segment meshes, which state
sheet identity by construction and come about 100x denser. The
extractor counts a segment's own wraps with no axis and no spacing
constant, one collection per mesh, seam wraps trimmed. Nine meshes,
289171 points.

**Matching tolerance is measured, not assumed.** At each ground-truth
point it is half the distance to the nearest annotated neighbour on an
adjacent winding. No spacing constant, no umbilicus, no radial model.
Sparse regions fall back to the tightest available estimate. Tighter
costs coverage, never accuracy.

Metrics, fixed before any measurement: exact agreement on dw=1 pairs,
mean absolute residual, a confidence vs accuracy calibration curve, and
coverage.

## The rules were sealed first

`GATE0_criteria.md` was written, reviewed and hashed before any external
generator was measured:

    sha256 d4da5eb9f7e8ce4b2c372c19d9830b229218b8e2777ef3dfcc9a2332f0bcd064

That hash still verifies against the root commit. Changes happen as
dated addenda, never edits, including the ones that invalidated results
already produced.

## Standing results

**Sheet spacing on PHerc Paris 4: 180.0 um**, 95% across meshes
[173.6, 199.5], from nine verified meshes with a direct point-to-curve
estimator. Independent of the winding atlas in input, method and
parameters; the atlas entry for Paris 4 is 182.4 um, 1.3% away.

**First scored subject.** On one slice of Paris 4, winding-sync's own
`consistency()` reports 0.670 exact agreement between its constraints
while the same field scores 0.050 against verified mesh ground truth.
One slice, one scroll, not a characterisation of the tool, and the
author had the numbers before they were published. Density, match
quality, scale and offset were ruled out first. Details in A12.

## Subjects

winding-sync (abundantjoe), BFS on the same graph as the baseline, E1
(mine, held out), angle-binned radial pitch (alyalya), constraint chain
(Iyán Dopico).

Addenda so far came from review by Paul Henderson, sean (bruniss), Iyán
Dopico and alyalya.

MIT.
