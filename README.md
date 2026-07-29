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
- **Your nodes must be finer than the sheets.** On the annotated arm the
  sheets sit about 18 voxels apart, on the mesh arm about 75. A
  generator laying nodes more coarsely than that is reported NOT
  SCORABLE rather than scored, for reasons under "what the bench checks"
  below. This is usually a submission parameter, not a redesign.
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

If your generator answers about a PAIR rather than assigning a winding
per point, it is a pairwise subject: see `gauge/pairwise.py`. Those skip
matching entirely and are not directly comparable with node-based ones.

## What the bench checks before it scores anything

**Density.** Scoring a generator whose nodes are more spaced than the
sheets does not fail the way you might expect. A perfect generator
snapped to coarse grids keeps M1 above 0.9 out to a node gap 2.2x the
sheet spacing; what collapses is coverage, from 1.000 to 0.072. The
problem is that the surviving pairs are not a fair sample: they skew
toward regions where sheets are loosely spaced, median tolerance rising
58%. A high score at low coverage measures where you could be matched,
not how good your field is. So the bench reports NOT SCORABLE with the
ratio instead. Measured in `tests/test_density_curve.py` and
`tests/test_density_bias.py`.

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
at dw 1-6 on PHerc Paris 4, in the 7.91 um volume.

**Verified-mesh arm.** Human-verified GP segment meshes, which state
sheet identity by construction, in the 2.4 um volume. The extractor
counts a segment's own wraps with no axis and no spacing constant, one
collection per mesh, seam wraps trimmed. Nine meshes, 289171 points.

**The two arms do not overlap** and never will: the annotated arm sits
where the lasagna grad_mag field exists, the mesh arm above it. No
subject can be cross-validated across them.

**Matching tolerance is measured, not assumed.** At each ground-truth
point it is half the distance to the nearest annotated neighbour on an
adjacent winding. No spacing constant, no umbilicus, no radial model.
Tighter costs coverage, never accuracy.

**Does the ruler measure correctly?** Corrupt the mesh GT at known rates
and the arm returns the closed form `(1-f)^2 + f^2/2` to within 0.005 at
every level. Note the floor that implies: a fully corrupted adapter
scores 0.5, not 0, because correlated error cancels in a difference.
`tests/test_mesharm_calibration.py`.

Metrics, fixed before any measurement: exact agreement on dw=1 pairs,
mean absolute residual, a confidence vs accuracy calibration curve, and
coverage.

## The rules were sealed first

`GATE0_criteria.md` was written, reviewed and hashed before any external
generator was measured:

    git show 3ceed9f:GATE0_criteria.md | sha256sum
    d4da5eb9f7e8ce4b2c372c19d9830b229218b8e2777ef3dfcc9a2332f0bcd064

That hash still verifies. Changes happen as dated addenda, never edits,
including the ones that invalidated results already produced and the one
that replaced a gate's stated justification after measuring it.

## Standing results

**Sheet spacing on PHerc Paris 4: 180.0 um**, 95% across meshes
[173.6, 199.5], from nine verified meshes with a direct point-to-curve
estimator. Independent of the winding atlas in input, method and
parameters; the atlas entry for Paris 4 is 182.4 um, 1.3% away.

**Internal agreement is not external accuracy.** On one slice of Paris 4,
winding-sync's own `consistency()` reports 0.670 exact agreement between
its constraints while the same field scores 0.050 against verified mesh
ground truth. Its L1 solver does beat the BFS baseline on the identical
graph, 0.050 against 0.017, so the ceiling sits in the constraints
rather than the reconciliation. One slice, one scroll, not a
characterisation of the tool, and the author had every number before it
was published.

**The bench's own estimator, held out.** E1 with its parameters frozen
from a 1000-slice development window scores M1 0.923 at dw=1 on the 7450
pairs outside that window, the same figure as inside it. Its confidence,
measured for the first time, is close to uninformative: 0.42 to 0.53
across deciles.

## Subjects

winding-sync (abundantjoe), BFS forest baseline, E1 (mine, held out),
three structure-tensor variants (alyalya), constraint chain (Iyán
Dopico).

Addenda so far came from review by Paul Henderson, sean (bruniss), Iyán
Dopico and alyalya, whose submission also found a bug in this
repository's baseline solver.

MIT.
