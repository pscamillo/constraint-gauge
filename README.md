# constraint-gauge

A calibration benchmark for winding constraint generators in the
Vesuvius Challenge. It scores any generator per location against human
winding annotations, and reports whether its confidence means anything.

The winding constraints page lists "accurate (or have some way to
measure its confidence/accuracy)" as the first requirement for an ideal
generator. I could not find a shared instrument for that, so this is
one.

## What a submission gets you

- **External accuracy, per location.** Exact agreement at dw=1, mean
  absolute residual and coverage against human ground truth, on two
  independent arms. Internal consistency cannot tell you this; the gap
  between the two has already been measured at 0.670 vs 0.050 on the
  same graph.
- **A confidence calibration curve.** Whether your declared confidence
  predicts your accuracy, in deciles plus one number (M3_ece_rank).
  No other instrument in the ecosystem measures this; the first
  estimator measured (this author's own) turned out close to
  uninformative, which no internal check would have shown.
- **Your numbers reach you first.** No figure about your tool is
  published before you have seen it (GATE0 6.4/7.1). Held in every
  case so far.
- **Diagnosis, not a shame ranking.** A generator whose nodes cannot
  resolve the sheets is reported NOT SCORABLE with the ratio and the
  reason, never as a low score. The first case turned out to be a
  one-parameter fix, and the author had it before anyone else.
- **The cost is one JSON file.** Points, a winding per point, a
  confidence per point. Details below.

## Submitting a generator

One file. Points, a winding number per point, a confidence per point:

    {"name": "my-generator",
     "points_xyz": [[x, y, z], ...],
     "winding":    [12, 12, 13, ...],
     "conf":       [0.9, 0.4, 0.8, ...]}

Rules for the file, all of which matter:

- **Coordinates are full-resolution voxels of the volume the arm uses.**
  The two ground-truth arms live in different volumes: the annotated arm
  on the L2 grid of the 2.4 um rescan (9.6 um/vox; long mis-stated
as 7.91, A25), the mesh arm in full-resolution 2.4 um voxels. Pick the arm
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
        --pitch-um 180 --um-per-vox 9.6 \
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
author of this bench too, and bites him: the E1 estimator here is
`in-sample` on the window it was calibrated on and `shared-parent` on
the rest of the annotated arm, because its frozen parameters come from
a disjoint window of the same annotation campaign (A7.2). Its held-out
line is reported only with that label and is not a headline.

## How the ruler was checked

A benchmark's own numbers are worth what its verification is worth.

On 29/07 the whole repository was audited line by line: documents,
code, results and git history (GATE0 A20, fourteen items, plus A21).
No measurement moved. The only casualty was a provenance label that
favoured this benchmark's own author, relabelled against his interest
(A7.2).

**Does it return what it is given?** Corrupt the ground truth at known
rates and see whether the measured score matches the algebra. A pair
survives corruption if neither endpoint moved or if both moved the same
way, so the expected score is `(1-f)^2 + f^2/2`:

| corrupted | measured M1 | closed form |
|-----------|-------------|-------------|
| 0%        | 1.000       | 1.000       |
| 10%       | 0.814       | 0.815       |
| 30%       | 0.537       | 0.535       |
| 50%       | 0.378       | 0.375       |
| 100%      | 0.505       | 0.500       |

Maximum deviation 0.005 across every level. Note the floor that implies:
a fully corrupted subject scores 0.5, not 0, because correlated error
cancels in a difference. Any reading of a score has to keep that in mind.
`tests/test_mesharm_calibration.py`.

**Are the gates measured or argued?** The density precondition was
originally justified by an argument, that coarse nodes make winding
differences arbitrary. Measuring it refuted that: a perfect generator
snapped to coarser and coarser grids keeps M1 above 0.9 out to a node
gap 2.2x the sheet spacing, while coverage falls from 1.000 to 0.072.
The gate stayed, on a different and measured basis, that the pairs
surviving at low coverage skew toward loosely spaced regions and inflate
the score by selection. `tests/test_density_curve.py`,
`tests/test_density_bias.py`.

**Is each estimator checked against a known answer before use?** The
mesh wrap detector recovers a synthetic spiral of known 528 um spacing
to 0.0% error; the density-extrapolation estimator recovers synthetic
sheets of known 180 um spacing to 1.1%, after a first convergence model
that was off by 16% and was rejected by that same test before touching
real data. `tests/test_meshgt.py`, `tests/test_mesh_spacing.py`,
`tests/test_pitch.py`.

**Is the reimplementation faithful?** The E1 subject reimplements an
estimator that lives in another repository; the two agree to 0.000e+00
on 300 pairs, bit-identical rather than approximated.
`tests/test_e1_fidelity.py` (needs the winding-ruler repository and the
spiral dataset locally).

**What happened when checks failed.** Four results were invalidated by
this process before publication, one gate had its stated justification
replaced after measurement, and one exemption was written and reverted
in the same session. All of it is in `GATE0_criteria.md` as dated
addenda, with the superseded numbers left in place rather than removed.

The tests are scripts: run them as `python tests/test_X.py` (a pytest
shim, `tests/test_pytest_smoke.py`, collects the self-contained ones).
The synthetic tests need nothing. The density tests
(`test_density_bias.py`, `test_density_curve.py`) need the Paris 4
annotation file: pass its path as the first argument or set
`CG_GT_JSON`. The mesh calibration tests need the GP segment meshes
under `data/gp_meshes`. The fidelity test needs the winding-ruler
repository.

## How ground truth is built

**Annotated arm.** Human point collections, 8156 within-collection pairs
at dw 1-6 on PHerc Paris 4, on the L2 grid of the 2.4 um rescan
(9.6 um/vox, A25).

**Verified-mesh arm.** Human-verified GP segment meshes, which state
sheet identity by construction, in the 2.4 um volume. The extractor
counts a segment's own wraps with no axis and no spacing constant, one
collection per mesh, seam wraps trimmed. Nine meshes, 289171 points.

**The two arms live in the same scroll and overlap by about 95 mm**
once both are read in the same frame: annotated z times 4 spans
26108-69012 against the mesh band's 29420-73889 (A25 item 4). The
earlier no-overlap claim compared coordinates across frames; cross-arm
validation is possible in principle, nothing claimed until the A25
probe runs. Superseded text: the annotated arm sits
where the lasagna grad_mag field exists, the mesh arm above it. No
subject can be cross-validated across them.

**Matching tolerance is measured, not assumed.** At each ground-truth
point it is half the distance to the nearest annotated neighbour on an
adjacent winding. No spacing constant, no umbilicus, no radial model.
Tighter costs coverage, never accuracy.

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

**Two independent methods agree on the Paris 4 median: 180.0 vs
182.4 um, 1.3% apart.** Sheet spacing is not a constant and this
headline does not claim one: it varies inside the scroll (per-mesh
medians 170.7-199.5 in the GP-mesh band before the two wrap-skip
cases at 262 and 343, A6.4; the annotated band lower in the scroll
reads about 176 um at the correct 9.6 um/vox frame (A25), in
agreement with this band rather than in tension with it). What the agreement supports is the
methods, not a number for the scroll: nine verified meshes with a
direct point-to-curve estimator (median 180.0, 95% across meshes
[173.6, 199.5]) against the atlas periodicity estimate (182.4),
independent in input, method and parameters. The bench itself never
uses a spacing constant anywhere: matching tolerance is measured at
each ground-truth point (A2.2).

**Internal agreement is not external accuracy.** On one slice of Paris 4,
winding-sync's own `consistency()` reports 0.670 exact agreement between
its constraints while the same field scores 0.050 against verified mesh
ground truth (probe and raw output: `tools/probe_ws_consistency.py`). Its L1 solver does beat the BFS baseline on the identical
graph, 0.050 against 0.017, so the ceiling sits in the constraints
rather than the reconciliation. One slice, one scroll, not a
characterisation of the tool, and the author had every number before it
was published.

**The bench's own estimator, held out.** E1 with its parameters frozen
from a 1000-slice development window scores M1 0.923 at dw=1 (n=1718)
on the pairs outside that window, against 0.900 inside it: the
calibration transfers with no degradation. The line is shared-parent
on this arm (A7.2), fitted on a disjoint window of the same annotation
campaign, so it is not a headline comparable with other subjects. Its
confidence, measured for the first time over all scorable pairs
(dw 1-6), is close to uninformative and not monotone: 0.42 in the
least-confident decile, 0.53 in the most-confident, peaking at 0.59 in
between.

## Subjects

Scored: winding-sync/l1 at our stride variant (A11), BFS forest
baseline on the same graph, E1 (mine, held out, shared-parent per
A7.2), and Aleksei Drobkov's three dense structure-tensor variants,
the first independent subject to clear the density gate (ratio 0.51,
coverage 1.000). Gated NOT SCORABLE at author configuration:
winding-sync default stride. Registered, not yet run: Iyán Dopico's
constraint chain (S-F), the PHerc1218 arm (GT-2), and the section 5
spacing-prior ablation.

Addenda so far came from review by Paul Henderson, sean (bruniss),
djosey, Iyán Dopico and Aleksei Drobkov, whose submission also found a
bug in this repository's baseline solver.

Built in pair programming with Claude (Anthropic), who also performed
the line-by-line audit recorded as A20 (disclosure in A23). Every
number, commit and decision here was verified and made by the author.

MIT.
