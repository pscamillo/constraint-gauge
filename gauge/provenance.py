"""gauge.provenance - subject-vs-GT provenance labels (addendum A7).

Rule (Iyán Dopico, declared against his own interest): every subject
declares provenance against EACH ground-truth arm before scoring, and
every published result carries the label. Three values:

    independent    subject and GT share no parent; the real test
    shared-parent  subject derives from data the GT also derives from
                   (e.g. a constraint chain built from the same stitched
                   labels that form the GT arm)
    in-sample      the subject was developed or tuned on these very
                   pairs (e.g. the E1 estimator on the z10000-11000
                   window it was calibrated against)

No shared-parent or in-sample line is comparable across subjects
without its label. Declarations live in a json registry so they are
reviewable and diffable, never inferred at runtime:

    {"<subject>": {"<gt_arm>": "independent|shared-parent|in-sample",
                   "note": "free text"}}

Unknown subject or unknown arm resolves to "undeclared", which the
runner reports and which blocks nothing technically — the block is
social: an undeclared line must not be published.
"""

import json
import os

VALID = ("independent", "shared-parent", "in-sample", "undeclared")

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data",
                             "provenance.json")


def load_registry(path=None):
    path = path or _DEFAULT_PATH
    if not os.path.exists(path):
        return {}
    return json.load(open(path))


def label_for(subject, gt_arm, registry=None, path=None):
    """Return (label, note) for a subject against one GT arm."""
    reg = registry if registry is not None else load_registry(path)
    entry = reg.get(subject)
    if not entry:
        return "undeclared", "subject not in the provenance registry"
    val = entry.get(gt_arm)
    if val is None:
        return "undeclared", f"no declaration against arm '{gt_arm}'"
    if val not in VALID:
        return "undeclared", f"invalid label '{val}' in registry"
    return val, entry.get("note", "")


def publishable(label):
    """A line may be published as a headline number only if it is
    independent. The others may be reported, always with the label."""
    return label == "independent"
