"""gauge.adapters - what a constraint generator must provide to be scored.

The whole interface is one dataclass:

    AdapterResult
        name           str, shown in reports
        points_xyz     (N, 3) float, full-resolution voxel coords, [x, y, z]
        winding        (N,) solved winding number per point (float or int;
                       relative offset is fine, only differences are scored)
        conf           (N,) confidence per point, higher = more confident.
                       Any monotone scale; used only for the calibration
                       curve (quantile bins). Pass ones if the generator
                       has no confidence notion.

Three ways to produce one:

  1. JSON file (no integration needed):
         {"name": "...", "points_xyz": [[x,y,z],...],
          "winding": [...], "conf": [...]}          -> load_json()
  2. winding-sync (abundantjoe), if installed      -> from_winding_sync()
  3. BFS baseline on the same winding-sync graph   -> from_winding_sync(
                                                        solver="bfs")

Implementation note (recorded for the GATE0 adendo): pair confidence for
the calibration curve is min(conf_a, conf_b) - the pair is only as
trustworthy as its weaker endpoint.
"""

import json
from dataclasses import dataclass

import numpy as np


@dataclass
class AdapterResult:
    name: str
    points_xyz: np.ndarray
    winding: np.ndarray
    conf: np.ndarray

    def __post_init__(self):
        self.points_xyz = np.asarray(self.points_xyz, dtype=np.float64)
        self.winding = np.asarray(self.winding, dtype=np.float64)
        if self.conf is None:
            self.conf = np.ones(len(self.winding))
        self.conf = np.asarray(self.conf, dtype=np.float64)
        n = len(self.points_xyz)
        assert self.winding.shape == (n,) and self.conf.shape == (n,), \
            "points_xyz, winding and conf must share length"


def load_json(path):
    d = json.load(open(path))
    return AdapterResult(
        name=d.get("name", path),
        points_xyz=d["points_xyz"],
        winding=d["winding"],
        conf=d.get("conf"))


def from_winding_sync(scroll, z, solver="l1", name=None):
    """Run abundantjoe/winding-sync on one slice and wrap the result.

    Requires winding_sync importable (pip install from his repo). The
    generator emits seed_coords (y, x) in the stats dict and the graph;
    z comes from the slice index. solver="l1" uses his L1 sync,
    solver="bfs" his BFS spanning-tree baseline on the SAME graph, which
    isolates solver quality from generator quality.

    Exact call signatures follow his run_winding_test.py; adjust the two
    marked lines if his API moved since commit 25842b6.
    """
    from winding_sync import constraints, solver as ws_solver

    graph, stats = constraints.generate(scroll=scroll, z=z)   # <- API line 1
    if solver == "l1":
        w = ws_solver.solve_l1(graph)                         # <- API line 2
    elif solver == "bfs":
        w = ws_solver.solve_bfs_tree(graph)
    else:
        raise ValueError(solver)

    yx = np.asarray(stats["seed_coords"], dtype=np.float64)   # (N, 2) y, x
    pts = np.column_stack([yx[:, 1], yx[:, 0],
                           np.full(len(yx), float(z))])       # x, y, z
    # per-point confidence: total incident edge weight
    conf = np.zeros(graph.n_nodes)
    np.add.at(conf, graph.edges[:, 0], graph.weights)
    np.add.at(conf, graph.edges[:, 1], graph.weights)
    label = name or f"winding-sync/{solver}"
    return AdapterResult(label, pts, np.asarray(w, float), conf)
