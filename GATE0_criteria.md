# GATE0 — Pre-registered criteria: a calibration benchmark for winding
# constraint generators

TRANSLATION NOTE. The text below is an English translation of the sealed
body and of addenda A1 to A7, which were written in Portuguese. The
sealed original is immutable in the repository history and its published
hash still verifies:

    git show 3ceed9f:GATE0_criteria.md | sha256sum
    d4da5eb9f7e8ce4b2c372c19d9830b229218b8e2777ef3dfcc9a2332f0bcd064

Where a translation and the sealed original diverge, the original
governs. Nothing was softened, dropped or added in translation; addenda
from A6.3 onward were written in English and are untouched.

Project (working name): constraint-gauge
Author: pscamillo
Drafted: 2026-07-27
Reviewed and sealed: 2026-07-28
Status: FINAL FOR SEALING. Reviewed by the author on 28/07 (tau kept,
ablation hypothesis kept with its direction, arbitration judge kept).
After sealing: changes only by dated addendum, never by edit.

---

## 0. Purpose

To measure the per-location accuracy and the confidence calibration of
automatic winding constraint generators against human ground truth, with
criteria fixed before any number is produced.

The benchmark measures; it does not propose a new generator. A null
result ("no current generator reaches threshold X") is a valid
deliverable.

## 1. Subjects (fixed before running)

- S-A: abundantjoe/winding-sync (commit pinned on the day of the first
  measurement; record the hash here by addendum).
- S-B: the constraint chain from IyanDopico/vesuvius-sheet-tools
  (scripts/constraints, same pinning regime).
- S-C: BFS baseline (solve_bfs_tree from winding-sync, run on the SAME
  graph as S-A, which isolates solver from generator).

Additional subjects only by addendum. No subject is measured publicly
without a prior DM to its author (see section 7).

## 2. Ground truth

- GT-1: human annotated pairs from the spiral-input PHercParis4 dataset
  (HF snapshot to pin; the basis of the 706 radius-binned pairs by Iyán).
- GT-2: pairs from the stitched labels of PHerc1218 (9054 pairs; the
  flat-to-1.001 control already published).
- GT-3 (optional, by addendum): the team's 278 new fiber line
  annotations (HF buckets/scrollprize/datasets/tree/spiral/PHercParis4,
  uploaded 27/07) — included only if the format allows pair extraction
  under the same rule as section 3.

Dependency declaration (mandatory in any publication): GT-1 and GT-2 are
NOT independent of the winding atlas for pitch purposes — the 173 um
pitch of 1218 has the atlas as one of its three legs. For winding
accuracy (integer dw) the dependency does not apply: the pairs are
direct human annotation. For the pitch arbitration (section 6) the
independence rule is the one in 6.3.

## 3. Annotation-to-seed matching rule (pre-registered)

3.1 Every generator seed has a position (z, y, x) in volume space
    (winding-sync emits seed_coords; Iyán likewise via point
    collections).
3.2 An annotated pair (P, Q, dw_human) is SCORABLE for a generator if
    there are seeds s_P, s_Q with dist(P, s_P) <= tau and
    dist(Q, s_Q) <= tau.
3.3 tau = 0.5 x the scroll's median pitch, in voxels of the measured
    level. Rationale: beyond half a pitch the seed may sit on the
    neighbouring sheet and the match stops being interpretable. tau is
    FIXED; it will not be adjusted after seeing results.
3.4 Non-scorable pairs count towards COVERAGE, not accuracy. They
    neither penalise nor credit.
3.5 Nearest-neighbour ties: smallest euclidean distance; exact tie
    (unlikely) goes to the smaller seed index. Deterministic.
3.6 Sensitivity to tau (tau/2 and 2tau) is reported as a diagnostic,
    never as a primary metric.

## 4. Primary metrics (fixed)

- M1: per-location exact agreement on adjacent pairs (dw=1): the
      fraction of scorable pairs with dw_generator == dw_human.
- M2: mean absolute residual |dw_generator - dw_human| over scorable
      pairs (the metric that best separated L1 from BFS on real data:
      0.51 vs 1.75, per the winding-sync README).
- M3: calibration curve — declared confidence (weights) vs empirical
      accuracy, in 10 quantile bins; ECE reported.
- M4: coverage — the fraction of GT pairs that are scorable.

Secondary or diagnostic metrics may be added by addendum, but never
promoted to primary after the first measurement.

## 5. Pre-registered ablation: the spacing prior in S-A

Run winding-sync with CORPUS_SPACING_UM = 225.0 (his default) and 187.3
(atlas v2), all other parameters identical. Report dM1, dM2, dM4.
Registered hypothesis: the smaller prior improves M1 on Paris 4.
Direction and magnitude are a result, not a premise — publish whichever
way the sign falls.

## 6. Pitch arbitration (187.3 vs 225)

6.1 Question: which spacing estimator agrees with the pitch implied by
    the annotated pairs (the physical distance between dw=1 pairs), on
    the same scrolls, at the same declared resolution.
6.2 Possible verdicts (written beforehand): (a) 187.3 compatible, 225
    not; (b) 225 compatible, 187.3 not; (c) both compatible in different
    regimes (e.g. a radial dependency explains it); (d) neither
    compatible; (e) ground truth insufficient to decide. All are
    publishable.
6.3 Independence: the judge is the physical distance of the human
    annotated pairs, not any automatic estimator. The atlas does NOT
    take part as evidence in the arbitration — only as one of the
    measured parties.
6.4 Public framing: a joint measurement of two methods, never a
    correction of an author. No name in the verdict before the DM of
    section 7.

## 7. Conduct

7.1 DM to abundantjoe with this document's spec BEFORE any public run of
    S-A; likewise results before any public post. Same rule for Iyán on
    S-B (less formality, existing partnership).
7.2 Affirmative errata, never defensive. Public figures derived only by
    an aggregation script from the CSVs (the aggregate.py rule — no
    hand-typed number in a public artefact).
7.3 Public artefacts in English, plain register (no em dashes, no
    parallel triads, one question per message). Internal docs in
    Portuguese.

## 8. Recorded external conditions

- C1: RESOLVED. sean (bruniss) replied by DM, 27/07 21:16: the team has
  no automatic eval for generators and is not building one at the
  moment, and recorded that it would consider one useful ("not that we
  dont think it would be useful"). No duplication; publication
  unimpeded.
- C2: pin commits and snapshots of every subject and GT on the day of
  the first measurement, by addendum with hashes.

## 9. Sealing

After review: `sha256sum GATE0_criteria.md` recorded in a public place
(a gist or the repository's first commit) before the first measurement
of S-A/S-B.

---


## ADDENDA (dated; the sealed body above stays as sealed)

### A1 — 2026-07-28 — subject and GT pins (partially satisfies C2)
- S-A winding-sync: commit 25842b6 (abundantjoe/winding-sync).
- GT-1 Paris 4 relative_windings.json: local snapshot validated on
  28/07 (2173 points, 254 collections, 8156 pairs at dw 1-6;
  reproduces the 706 pairs of the z10000-11000 window from the July
  work). File hash to be recorded at the first scored run.

### A2 — 2026-07-28 — local tau (prompted by Paul Henderson, #general)
Acknowledged limitation of 3.3: a tau derived from the MEDIAN pitch can
cross a sheet where local packing is tight (spacing varies about 4x
within one crop; the radial binning of Paris 4 runs 136-259 um).
Mitigations already in force: unmatched pairs cost coverage and never
accuracy (3.4); the per-pair CSV records both match distances, so
matches in tight regions are auditable.
Adopted fix: a LOCAL tau derived from the local spacing (radius-
dependent on Paris 4 via the radial binning already measured; the
general rule to be specified in A2.1 before any public number). The
median tau of 3.3 remains as a fallback where no local measurement
exists. No public number is released before A2.1 is committed.

### A3 — 2026-07-28 — GP meshes as a priority GT source
(prompted by sean/bruniss, Paul Henderson and djosey, #general)
GT-3 promoted: human-verified GP segments of Paris 4 (sean's list, with
the wrap overlap at the seam to be discounted) and the merged tifxyz of
PHerc1667 (djosey; no overlap). Dense surface GT carries sheet
continuity that sparse points do not, and makes a tight tau affordable.
The point collections (GT-1/GT-2) remain valid; pair extraction from
the meshes will be specified in A3.1 with the overlap rule explicit.

### A4 — 2026-07-28 — additional subjects
- S-D: the E1 estimator from winding-ruler (author of this benchmark).
  Reported on two lines: in-sample (706 pairs at z10000-11000, used in
  development) and held-out (all other pairs, never seen). Only the
  held-out line is comparable with the other subjects.
- S-E: alyalya's angle-binned radial pitch variant
  (abundantjoe/winding-sync#1), by an invitation accepted in #general.

### A5 — 2026-07-28 — operational parameters of the first Paris 4 run
pitch-um 180 (human anchor; matching tolerance only, not evidence),
um-per-vox 2.4. Recorded that any value in 175-190 gives the same
verdicts via the tau/2-2tau diagnostic of 3.6.

### A6 — 2026-07-28 — pair confidence (implementation decision)
conf_pair = min(conf_a, conf_b): a pair is worth what its weaker
endpoint is worth. Fixed before any measurement of an external subject.

### A2.1 — 2026-07-28 — the local tau rule (implements A2)
tau(p) = 0.5 x pitch_local(r(p)); r = in-plane distance to the scroll
axis (per-scroll config or the median (x, y) of the GT); pitch_local by
lookup in a MEASURED per-scroll radial table
(data/paris4_pitch_table.json for Paris 4, from the July binning of the
human pairs, 136-259 um). Nearest-bin extrapolation at both ends of the
table — below the innermost bin the median would be looser than the
local pitch, which is exactly the cross-sheet hazard; the median of 3.3
applies only where there is no table.
Demonstrated in tests/test_localtau.py: median tau poisoned by
cross-sheet matches (M1 0.840), local tau clean (M1 1.000) at the cost
of coverage (0.830 -> 0.757). Public numbers unblocked.

### A2.2 — 2026-07-28 — tau from the annotations (prompted by
sean/bruniss and Paul Henderson, #general; supersedes A2.1 as the
primary rule)
Criticism accepted: winding-to-winding spacing is not a meaningful
constant, and radius to the umbilicus does not correlate with winding
under deformation (Paul's crop shows drastic variation over a short
distance). New rule, with no geometry: tau(p) = 0.5 x the distance to
the nearest annotated point on an adjacent winding in the SAME
collection — measured at the point, no constant, no axis, no radial
model. Fallback chain where annotation is sparse: min(tau_annotation,
tau_table A2.1, tau_median 3.3) — the tightest wins; tighter costs
coverage, never accuracy. Demonstrated in tests/test_gt_tau.py: defined
on 100% of the synthetic points, M1 1.000 with no geometry at all. The
radial table of A2.1 is demoted to a fallback.

### A3.1 — 2026-07-28 — GT extraction from the verified meshes
(implements A3; a rule with no geometry, consistent with A2.2)
Source: human-verified GP segments, tifxyz format, in the variant
registered on the same volume as the annotations where one exists
(PHercParis4/segments/<id>/mesh/<id>-on-<volume>-<um>.tifxyz).
Winding assignment with NO axis and NO constant: along the mid row of
the arc axis, a self-proximity chain — the next node is the nearest 3D
point among those that have already wrapped (chord < 0.5 x arc, a
dimensionless criterion); winding(u) = the index of the chain interval.
The mesh counts its own wraps.
Overlap (sean's warning): each mesh is its own collection, cross-mesh
pairs do not exist; the first and last wraps are discarded by default
(trim=1). The merged 1667 tifxyz (djosey) runs with trim=0.
Frames: each GT arm is scored in the frame of the volume the mesh is
registered on; different frames are not compared.
Validated on 20231022170901 (Paris 4): 8 wraps detected, matching
alyalya's independent count in #general; arcs per wrap monotone
16511 -> 12264 vox; 41755 points after trim, about 19x the density of
the annotation arm.

### A7 — 2026-07-28 — subject-vs-GT provenance (prompted by Iyán
Dopico, who declared it against his own interest; text approved by him
before the commit)
S-F: the constraint chain from IyanDopico/vesuvius-sheet-tools. The
chain descends from the same stitched labels that form GT-2 (1218):
subject and ruler share a parent on that arm. General rule adopted:
EVERY subject declares provenance against EACH GT arm before being
scored, and every published result is labelled independent /
shared-parent / in-sample. For S-F: Paris 4 = independent test; 1218 =
reported with a shared-parent asterisk. For S-D (E1, by the author of
this benchmark): the z10000-11000 window = in-sample; all other pairs =
independent. No shared-parent or in-sample line is comparable across
subjects without its label.

### A3.2 — 2026-07-29 — wrap crossing by return depth, five-row consensus
(supersedes the chain detector of A3.1; prompted by a failure on a real
mesh)
Rule: a wrap return is the first contiguous run where
chord <= 5 x (smallest chord ahead) AND chord < 0.5 x arc; the node is
the argmin of the chord in that run. The smallest chord ahead IS a
measurement of the local sheet spacing, so both criteria are
dimensionless and self-derived: no axis, no pitch constant.
Consensus: the chain runs on 5 well-covered grid rows; the modal count
wins and the best modal row gives the boundaries. A fold that fools one
row does not fool five heights.
Result on the 10 GP meshes of Paris 4: 10/10 extract, arcs monotone in
all of them; the mesh that failed (20231005123336) goes from 1 spurious
wrap of 93k vox to 4 wraps of about 23k (4 x 23.3k = the total arc, to
the voxel). Four meshes count one wrap fewer than the single-row read:
the conservative direction — undercounting loses coverage and never
corrupts labels, since the wraps kept are internally consistent.
Arm totals: 271864 mesh points plus 2173 annotated, same frame
(volume 20260411134726, z max 75784 fits both).
[Superseded in part by A6.3: the two arms are NOT in the same frame.]

### A7.1 — 2026-07-29 — provenance in the code (implements A7)
Registry in data/provenance.json: per subject, one label per GT arm
(independent / shared-parent / in-sample) plus a justification note.
The runner stamps every summary with subject, gt_arm, provenance and
publishable_as_headline; an undeclared subject or arm comes out
UNDECLARED with a warning. The block is social, not technical: an
unlabelled line is not published. Declared today: winding-sync/l1 and
/bfs (independent on all three arms), E1 (in-sample on the annotated
arm; E1/held-out independent), Iyán's chain (shared-parent on 1218,
independent on Paris 4, by the author's own declaration), alyalya's
angle-binned variant (independent).

### A3.3 — 2026-07-29 — adaptive trim and single-winding collections
The seam trim (A3.1) applies only when at least 2 windings survive it;
otherwise the extraction runs untrimmed. A collection that still ends
up with a single winding is DISCARDED: with no neighbouring winding
there is no dw>=1 pair and no measured tau, so carrying those points
would only expose them to the loose fallback.
Effect on the 10 Paris 4 meshes: 20231031143852 and 20231106155351
recovered with trim=0 (3 windings each, +22853 points), 20231210121321
discarded (1 wrap). Final arm: 9 meshes, 289171 points, A2.2 tau
measured on 100% of them, range 3.4-37.5 vox. The median fallback is no
longer used anywhere in the mesh arm.

### A8 — 2026-07-29 — scale (implementation fix, no effect on any rule)
build_pairs now counts pairs from a winding histogram and samples per
block: memory O(max_pairs), not O(all pairs). Nearest-neighbour
searches (the matcher and the A2.2 tau) now use a KD-tree with a
chunked brute-force fallback. No criterion changed; the same self-test
that consumed 31 GB and did not finish now runs in 2.4 s with 775 MB.

### A6.1 — 2026-07-29 — the arbitration's estimator and convergence curve
(records the method BEFORE any real measurement; the verdict remains
the one in 6.2)
Two estimators reported side by side. NEAREST: the distance from each
annotated point to its nearest neighbour on an adjacent winding, median
over points — exactly 2x the A2.2 tolerance, that is, the quantity a
generator actually competes against. It is an UPPER BOUND on the
perpendicular spacing: two annotated points are rarely perpendicular
across the gap. ALLPAIRS: the median over all dw=1 pairs, the literal
reading of 6.1, reported as a ceiling.
Convergence curve: the nearest estimator's bias shrinks with sampling
density. Sampling the same arm at several densities traces a decreasing
curve whose limit is the physical spacing. Convergence law derived from
the geometry: the nearest partner sits at sqrt(d^2 + r^2) with
r^2 ~ A/n, so median^2 = d^2 + b/n, and the intercept of a linear fit
of median^2 against 1/n gives d^2. Interval by bootstrap over the GT
points (the curve is rebuilt on each replicate).
Validated in tests/test_pitch.py against synthetic sheets of KNOWN
spacing (180 um): the estimator never underestimates, decreases with
density, extrapolated limit 181.9 um (error 1.1%, r2 0.999), allpairs
4971 um confirming it is a ceiling and not a competitor. Error on
record: the first model tried (linear in n^-1/2) underestimated by 16%
and was rejected by the synthetic test itself, before any contact with
real data.

### A6.2 — 2026-07-29 — the roles of the two arms in the arbitration
(recorded BEFORE any real measurement)
The MESH arm (A3.1/A3.3) is the ARBITER: neither the atlas (187.3) nor
winding-sync (225) used the verified GP segments as input. The
ANNOTATED arm has a DECLARED DEPENDENCY with the 187.3: this author's
atlas was calibrated against Paris 4 human annotations, so it shares
input with that claim, even though the quantity and the method differ.
Consequence fixed before the number: a confirmation of 187.3 coming
only from the annotated arm does NOT count as confirmation. A verdict
against either claim counts on both arms. Rule 6.4 applies equally to
the 225 and to the 187.3: each author sees it first.

### A6.4 — 2026-07-29 — wrap-skip correction, and the invalidation of
the run that preceded it
INVALIDATION. The 12:xx mesh run printed verdict (a), favouring this
author's own 187.3, and it does not count. The exclusion threshold that
produced it (implied/measured < 0.8) was chosen AFTER seeing the table
of ratios, and the choice decides the verdict: the median over all nine
meshes is 248.9 um, compatible with 225; over the five survivors it is
180.0 um, compatible with 187.3. A post-hoc criterion that moves the
answer to the author's own claim is exactly the degree of freedom
pre-registration exists to remove. Not published, not counted.
RULE, stated by principle rather than fitted. A spiral whose arc per
wrap shrinks by dA implies radial growth dA/2pi per wrap; comparing
that with the measured gap gives ratio = implied/measured. If the chain
merged k wraps into one, the measured gap is k times the true spacing
and the ratio lands near 1/k. So: k = round(1/ratio) applied when
k >= 2, and the mesh is ACCEPTED only if the corrected ratio falls in
[0.75, 1.6], the band that unskipped meshes occupy on geometric
grounds (measured slightly below implied because scrolls are not
circular). The correction predicts its own factor before that factor is
known, so it is falsifiable: a mesh whose CORRECTED ratio still misses
the band is rejected, not rescaled again.
The bootstrap resamples MESHES, not points: adjacent grid cells measure
nearly the same gap, and point-level resampling gave a spurious 0.7 um
interval.
Verdicts from the next run under this rule count, whichever way they
fall.

### A6.5 — 2026-07-29 — the arbitration as posed compares different
populations: verdict (e) on scope
The two claims are not statements about PHerc Paris 4. The 225 um comes
from winding-sync's README as a median over the 13 Grand Prize scrolls
(207-259 um), and Paris 4 is not among them. The 187.3 um is this
author's atlas median over 35+ scrolls, not its Paris 4 entry. The
measurement made here covers ONE scroll, and one that is outside the
first claim's population, so neither claim can be confirmed or refuted
by it. Section 6.2's verdicts (a)-(d) do not apply and the arm returns
(e), for scope rather than data quality. Recorded BEFORE looking up
either method's per-scroll value for Paris 4.
The well-posed version, adopted for the next round: both methods emit a
per-scroll number, so the comparison is what each method assigns TO
PARIS 4 against what the gauge measures ON PARIS 4. That requires the
atlas's Paris 4 entry and a winding-sync run on Paris 4 (subject S-A),
and it is like for like.
STANDING RESULT, independent of the arbitration. The gauge's own
measurement holds on its own terms: sheet spacing on PHerc Paris 4 =
180.0 um, 95% interval across meshes [173.6, 199.5], from nine
human-verified GP segment meshes, direct point-to-curve estimator, no
axis and no spacing constant, each mesh median an upper bound by about
1.3%. Robustness: the five meshes needing no wrap-skip correction give
the same 180.0 um median as all nine.

### A6.6 — 2026-07-29 — Paris 4, like for like: the gauge against the
atlas entry (partial; the winding-sync side is still missing)
Sources, each from its author's published artefact.
  atlas, PHerc Paris 4, pyramid level 1 after the 22 July errata:
  182.4 um. Source: pscamillo/winding-ruler, results/
  atlas_collection_v2.csv, commit f23ae5a, row PHercParis4, column
  lambda_med_um. Quoted in that repo's README line 34.
  gauge, PHerc Paris 4, nine human-verified GP segment meshes, direct
  point-to-curve estimator (A6.3), wrap-skip corrected (A6.4):
  180.0 um, 95% across meshes [173.6, 199.5].
Agreement: +1.3%, the atlas entry inside the gauge interval.
WHAT THIS IS NOT. The +1.3% figure is not a new finding: it is already
published in the winding-ruler README (18 July), computed against a
reference of about 180 um that was itself ANCHORED TO THE PARIS 4 HUMAN
ANNOTATIONS — the same annotations that chose the atlas's gap-closing
parameter. Claiming discovery here would be self-citation.
WHAT IT IS. The gauge replaces that dependent reference with an
independent one. The nine GP segment meshes were never an input to the
atlas, at any stage, and the estimator needs no calibrated parameter,
no axis and no spacing constant. The anchored number and the
unanchored one land 1.3% apart. That is confirmation by substitution of
reference, not by re-measuring the same source.
STRENGTH AND WEAKNESS, stated together. Strong on independence: no
shared input, no shared estimator family, no tuned parameter. Weak on
precision: with nine meshes the interval spans 26 um, so 182.4 would
fall inside it even if the atlas were several percent off. This
confirms that the atlas entry is not grossly wrong on Paris 4; it does
not certify it to better than about 15%.
STILL OPEN. The arbitration of 6.2 needs the other side: what
winding-sync assigns to Paris 4 specifically, run as subject S-A. Until
that exists, no verdict on either claim. Under 6.4, both authors see
their numbers before anything is published.

### A6.3 — 2026-07-29 — direct mesh estimator, validity gates, and a
frame erratum
(RECORD-KEEPING NOTE: this text was written and committed in message
form as ebb4abe but never landed in the file; it is appended here on
discovery, out of numerical order and after A6.6. Nothing else was
edited. From here on addenda are written in English: GATE0 is a public
artefact and several of the people credited in it cannot read
Portuguese. The sealed body stays verbatim and its hash d4da5eb9 still
verifies against the root commit.)

ERRATUM to A3.2. The claim "same frame, the volume z max 75784 fits
both" is WRONG. The spiral-input annotations live in the 7.91 um
volume (bbox x,y up to ~6600, z up to 17252; in the 2.4 um volume that
region would be 11 mm across, implausible for 254 collections spanning
several wraps), while the GP meshes live in the 2.4 um one. They are
DIFFERENT FRAMES. Each arm is scored in its own frame with its own
um-per-vox, and a generator supplies coordinates in the frame of the
arm it is scored on. The first arbitration run used 2.4 um on the
annotated arm and returned 46 um spacing, physically impossible, which
is how the error surfaced.

DIRECT ESTIMATOR (meshes). The grid samples each wrap densely along u
(one grid step, 20 vox) compared with the gap between wraps (60-100
vox), so the distance from a point on wrap k to the CURVE of wrap k+1
at the same height v IS the perpendicular spacing, with second-order
error step^2/(8 d^2), about 1.3%, always upward. No extrapolation and
no axis. Validated on a synthetic spiral of KNOWN spacing (528 um):
median 528.0 um, error 0.0%, q1-q3 spread 0.3 um. Where a direct
estimator exists it decides; the A6.1 extrapolation is for sparse arms.

VALIDITY GATES for the extrapolation, which A6.1 lacked. An
extrapolated limit may support a verdict only if the fit explains the
curve (r2 >= 0.9), the point estimate lies INSIDE its own bootstrap
interval, and the curve has reached a plateau (last two densities
within 10%). Failing any of these, the arm returns verdict (e).

INVALIDATION OF THE FIRST RUN. It produced no valid verdict on either
arm. Annotated: r2 0.557 and the wrong frame. Meshes: point estimate
144.2 outside its own interval [211.1, 230.7] and a curve still falling
steeply (960 -> 245 um, no plateau). The "(b)" printed by that run is
an arithmetic artefact, NOT evidence for 225. None of those numbers
were published.

### A6.7 — 2026-07-29 — the published result files carry a verdict the
document overrides
results/arb_meshes.json, committed with A6.6, records
verdict "a" with the note "187.3 (atlas) compatible, winding-sync not".
That verdict is SUPERSEDED by A6.5: the runner applies section 6.2
mechanically and does not know the scope argument, so it compared a
one-scroll measurement against claims that are medians over other
scroll populations. The governing verdict for the mesh arm is (e), on
scope. The file is left in place rather than rewritten, with this
addendum as the correction of record, and the runner will carry a scope
field so the mismatch cannot recur.
The measurement inside that file stands unchanged and is not affected:
Paris 4 sheet spacing 180.0 um, 95% across meshes [173.6, 199.5].

### A9 — 2026-07-29 — planar matching for slice-based generators
(sealed before the first subject run it applies to)
winding-sync and generators like it work one z slice at a time: every
node lives on a single plane. The mesh GT is a 3D cloud spanning tens
of thousands of voxels in z, so under 3D matching almost no GT point is
reachable and coverage is zero by construction rather than by quality.
Rule: when an adapter's points share one z, a GT point is ELIGIBLE if
|z_gt - z_plane| <= its own tau, and matching then uses in-plane (x, y)
distance against that same tau. The slab thickness is not a free
parameter; it is the tolerance that already governs matching
everywhere. Coverage is reported against the eligible subset, and the
summary records planar_matching and the plane's z so a planar line is
never silently compared with a volumetric one.
Demonstrated in tests/test_planar.py: a perfect single-plane generator
scores M1 = 1.0 under planar matching against a 3D sheet cloud.

### A10 — 2026-07-29 — density precondition: can this generator be
scored at all?
Per-location scoring asks which sheet a point sits on. A generator can
only answer where it emits nodes finer than the sheets. If the typical
gap between neighbouring generator nodes exceeds the local sheet
spacing, a ground-truth point has no node of its own: the nearest node
belongs to a neighbouring sheet and the winding difference read there
is arbitrary, however good the generator's internal solution is.
Gate, a PRECONDITION and not a metric: node_gap = median nearest-
neighbour distance among generator nodes; sheet_gap = twice the median
A2.2 tolerance of the GT in the scored region; ratio = node_gap /
sheet_gap. ratio < 1 means sheets are resolved and scoring is
meaningful. ratio >= 1 is reported as NOT SCORABLE together with the
ratio, never as a low score. The distinction is the point: a low score
is a claim about accuracy, and this is not one.
FIRST APPLICATION, and the reason the gate exists. winding-sync v0.2.0
(commit 20a31e1) has TracingConfig.seed_stride_um = 260 um by design,
while PHerc Paris 4 sheets sit about 180 um apart. Measured node gap on
z 57200: 82 vox at pyramid level 2 and 86 vox at level 1 (the stride is
in micrometres, so the pyramid level does not change it) against a
75 vox sheet gap, ratio 1.09 and 1.15. The M1 of 0.05 obtained before
this gate existed is NOT a result about winding-sync and is recorded
only as the diagnostic that led here. The generator's own field is
locally coherent on that slice: 70% of neighbouring seeds differ by at
most one winding.
This is an actionable finding about a parameter, not a defect of the
method, and it is invisible to any internal consistency measure. Under
6.4 the author sees it before it goes anywhere.

### A12 — 2026-07-29 — first scored subject: winding-sync on PHerc
Paris 4, one slice, and the gap between internal and external agreement
SCOPE, stated first because it bounds everything below. ONE slice
(z 57200 full-res) of ONE scroll (PHerc Paris 4), at pyramid level 2.
Paris 4 is not among the 13 Grand Prize scrolls the tool targets. These
numbers are not a characterisation of winding-sync, and nothing here
should be read as one.
CONFIGURATIONS. Author default (TracingConfig.seed_stride_um = 260 um)
is NOT SCORABLE on this slice by A10: node gap 82-89 vox against a
75 vox sheet gap, ratio 1.09-1.18. Two variants of OURS, same code and
solver with the stride lowered, pass the gate: 160 um gives node gap
68 vox in the scored region, ratio 0.91; 120 um gives 21.5 vox over the
whole slice. Variants are labelled winding-sync/l1@stride<N> and are
not the author's configuration (A11).
RESULT, at stride 160 um, mesh arm, planar matching, 7495 pairs at
dw=1:
  internal, by the tool's own consistency(): satisfied_exactly 0.670,
  within_one 0.881, mean_abs_residual 0.611
  external, against human-verified mesh GT: M1 0.050, M2 21.5
The two measure different things and disagree completely. The tool's
README says it in advance: "Internal consistency is not correctness. Do
not optimise self-consistency." This is that sentence with numbers on
both sides, from the same graph and the same slice.
WHAT WAS RULED OUT before concluding. Sampling density: raising it from
ratio 1.18 to 0.91 left M1 unchanged (0.052 to 0.050). Match quality:
stratifying by match distance, pairs matched within 0-10 vox score 5.4%
exact against 5.0% for pairs matched at 30-40 vox, so the tolerance is
not what is losing the signal. Scale or offset: dw_pred on dw=1 pairs
has median 1.0 but median absolute value 19, symmetric and wide, which
is dispersion rather than a factor or a shift.
CORROBORATION, independent of our scoring. The recovered field spans
216 windings on this slice (BFS on the same graph spans 257), against
roughly 70-90 wraps for this scroll by the winding atlas. A field that
is internally coherent and globally inflated is consistent with what
the external score reports.
The author received these numbers by DM before this commit, per 6.4.

### A13 — 2026-07-29 — pairwise subjects, a second kind of generator
Two families exist in this problem. A NODE-BASED subject assigns a
winding number to every point it emits, and the bench matches
ground-truth points to those nodes under section 3. A PAIRWISE subject
answers a question about two given points: how many windings apart are
they. winding-sync is the first kind; the E1 estimator of winding-ruler
is the second, and so are ray or integral based predictors generally.
For a pairwise subject the matching rule does not apply at all: the
subject is handed the ground-truth pair itself, so there is no
nearest-node search, no tolerance, and the A10 density gate is moot.
Coverage becomes the fraction of GT pairs the subject can answer, which
for an integral estimator is the fraction whose ray stays inside the
available volume.
This makes pairwise subjects EASIER on coverage and neither easier nor
harder on accuracy: they are asked precisely the question the bench
scores, with no localisation step in between. A pairwise M1 and a
node-based M1 are therefore NOT directly comparable, and every summary
records subject_kind so the difference travels with the number.

### A14 — 2026-07-29 — S-D: the E1 estimator of this benchmark's own
author, scored held-out
FIDELITY FIRST. gauge/e1.py reimplements the prediction path of
winding-ruler concordance/ruler_concordance_v1_5.py. Verified against
the original on 300 pairs of the development window: maximum absolute
difference between the two ray integrals 0.000e+00. Bit-identical, not
approximated.
FROZEN PARAMETERS. k = 2.773 and orient = +1, the values the estimator
carried out of its development window (z10000-11000, split seed 2).
They are NOT refitted per region. Refitting would test the mechanism
rather than the calibration, and would apply a looser rule to this
benchmark's own estimator than A11 applies to anyone else's tool.
RESULT, annotated arm, PHerc Paris 4:
  in-sample (706 pairs inside the development window):
    M1 0.900 at dw=1 (n=201), M2 0.390, M4 1.000
  held-out (7450 pairs outside it, the comparable line):
    M1 0.923 at dw=1 (n=1718), M2 0.575, M4 1.000
The calibration transfers. Parameters fitted on a 1000-slice window
hold their dw=1 accuracy on a sample 8.5x larger and geographically
disjoint from it, with no adjustment. The July criterion for this
estimator was >= 80% at dw=1; the held-out line gives 92.3%.
WHAT GOT WORSE, and was expected: M2 rises from 0.390 to 0.575, which
is the known degradation at larger |dw| (92% at dw=1 against 18% at
dw=6 in the July table). E1 is a unit-step estimator; a constraint
chain does not jump, so dw=1 is the load-bearing case.
WHAT IS NEW AND NEGATIVE. The confidence curve, measured on real data
for the first time because M3 did not exist in July: on the held-out
line the least-confident decile scores 0.42 and the most-confident
0.53. Eleven points of spread means the distance from the rounding
boundary barely predicts whether the answer is right. The estimator's
confidence is close to uninformative, and no internal measure would
have shown this.
NOT COMPARABLE with A12. The 0.923 here and the 0.050 there are on
different arms and, more importantly, different subject kinds (A13).
E1 is handed the pair; winding-sync has to localise the points among
its own nodes first. Any table putting them side by side must carry
both differences.
Order of measurement, for the record: the external subject was scored
first, with a gate that protected it from an unfair number, and the
author's own estimator second, with fidelity verified and its own
weakness published.

### A15 — 2026-07-29 — S-C: the BFS baseline, and what it says about
A12
The pre-registered role of S-C (section 1) is to separate solver from
generator: the same graph, the same seeds, the same constraints, only
the reconciliation differs. Run on the identical graph as
winding-sync/l1@stride160, same slice z 57200, same mesh arm:
  L1  (winding-sync)   M1 0.050 at dw=1, M2 21.5
  BFS (villa baseline) M1 0.017 at dw=1, M2 25.5
TWO CONCLUSIONS, and the first is favourable to the tool under test.
First: the L1 formulation's advantage is REAL and shows up against
human ground truth, not only in self-consistency. It recovers three
times as many exact answers as the spanning-tree baseline on the same
inputs and lowers the mean residual. The winding-sync README measures
that gap internally (0.703 against 0.629 exact agreement, residual 0.51
against 1.75); this is the external counterpart, on the arm the tool
never saw.
Second, and it re-reads A12: the ceiling is in the CONSTRAINTS, not in
the solver. The better of the two solvers still reaches only 0.050,
which means the graph handed to it does not carry the information the
question needs on this slice. A12 reported the gap between internal and
external agreement; S-C locates that gap upstream of the reconciliation
step.
Scope is unchanged from A12: one slice, one scroll, and Paris 4 is not
among the 13 GP scrolls the tool targets. The stride is our variant per
A11, applied identically to both solvers so the comparison is clean.

### A16 — 2026-07-29 — BFS forest, and an audit of the bench's own code
by alyalya
alyalya, submitting to the bench, also read its source and sent a diff.
The substantive point: winding_sync.solver.solve_bfs_tree roots a single
spanning tree at node 0, so on a fragmented patch graph every node
outside node 0's component keeps winding 0 and the baseline collapses
toward constant. One root per component is the fair thing to beat, since
each component carries its own zero, which is the relative-winding
convention the bench scores under.
Adopted. gauge/adapters.py now uses a per-component BFS forest for
solver="bfs"; the upstream single-root behaviour remains available as
solver="bfs-single" for comparison.
IMPACT ON A15, measured before adopting: the graph at z 57200 has 688
components, but the largest holds 99.0% of nodes and node 0 sits in it,
so single-root left only 1.0% of nodes zeroed. Rerun with the forest:
M1 0.017 and M2 25.5, identical to the single-root figures. A15 stands
unchanged, now on the correct baseline. The criticism was right in
principle and immaterial on this slice, and both halves are recorded.

### A17 — 2026-07-29 — is the mesh arm measuring correctly? and the two
arms never meet
THE ARMS DO NOT OVERLAP, and this is a hard limit rather than an
inconvenience. The annotated arm sits where the lasagna grad_mag field
exists (z up to about 18948 full-res); the mesh arm sits above it
(z 29420-73889). A subject built on that field cannot be scored on the
mesh arm at all: running E1 there returns coverage 0.000, every pair
unanswered, because the field it integrates does not exist in that
region. So no subject can be cross-validated across the two arms, and a
number from one arm can never be checked against the other.
SANITY FROM INSIDE, since cross-validation is unavailable. Feed the mesh
arm adapters whose error rate is known by construction: take the mesh GT
itself and corrupt a fraction f of windings by +/-1. A pair still scores
if neither endpoint was corrupted or if both moved the same way, so

    P(hit) = (1-f)^2 + f^2/2

Measured against that closed form on 30000 pairs:
    f=0%   M1 1.000 (form 1.000)
    f=10%  M1 0.814 (form 0.815)
    f=30%  M1 0.537 (form 0.535)
    f=50%  M1 0.378 (form 0.375)
    f=100% M1 0.505 (form 0.500)
Maximum deviation 0.005. The arm returns what it is given, to three
decimal places, at every level. Coverage is unaffected by accuracy, as
it should be.
THE FLOOR IS NOT ZERO, and this changes how any score is read. A fully
corrupted adapter scores 0.5, because half its corrupted pairs move
together and the shared error cancels in the difference. Correlated
error is partly invisible to a metric on differences. Consequently a
subject scoring 0.050 at dw=1, as winding-sync does on the slice in A12,
is not merely wrong: it is below the correlated-error floor and below
what uniform random assignment would give, which means its field
disagrees with the ground truth in a structured way rather than noisily.
Recorded as tests/test_mesharm_calibration.py so the check reruns.
