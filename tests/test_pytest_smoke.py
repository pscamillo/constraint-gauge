"""pytest collection shim (A20 item 11).

The suite is script-style by design (each test prints its evidence and
asserts). This shim lets `pytest tests/` collect and run the
self-contained ones from a clean checkout. Tests needing external data
(density: CG_GT_JSON; mesh calibration: data/gp_meshes; fidelity:
CG_WINDING_RULER + CG_DATASET) stay script-only and are documented in
the README.
"""

import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(__file__)

SELF_CONTAINED = [
    "test_synthetic.py",
    "test_gt_tau.py",
    "test_localtau.py",
    "test_planar.py",
    "test_density.py",
    "test_mesh_spacing.py",
    "test_meshgt.py",
    "test_pitch.py",
]


@pytest.mark.parametrize("script", SELF_CONTAINED)
def test_script(script):
    r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                       capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, f"{script} failed:\n{r.stdout}\n{r.stderr}"
