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


def _bfs_forest(graph):
    """Per-connected-component BFS spanning-tree winding (A16, alyalya).

    winding_sync.solver.solve_bfs_tree roots a single tree at node 0, so on
    a fragmented patch graph every node outside node 0's component keeps
    winding 0 and the baseline collapses toward constant. One root per
    component is the fair thing to beat: each component gets its own zero,
    which is exactly the relative-winding convention the bench scores under.
    """
    from collections import deque
    n = graph.n_nodes
    adj = [[] for _ in range(n)]
    for (i, j), d in zip(graph.edges, graph.deltas):
        adj[i].append((j, -int(d)))
        adj[j].append((i, int(d)))
    w = np.zeros(n, dtype=np.int64)
    seen = np.zeros(n, dtype=bool)
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for v, dl in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    w[v] = w[u] + dl
                    q.append(v)
    return w


def from_winding_sync(scroll, z, level=2, solver="l1", name=None,
                      bucket=("https://vesuvius-challenge-open-data"
                              ".s3.us-east-1.amazonaws.com"),
                      volumes=None, tile_threshold_gb=3.0, cache=None,
                      seed_stride_um=None):
    """Run abundantjoe/winding-sync on one z slice and wrap the result.

    Matches the API at winding-sync v0.2.0 (commit 20a31e1):
    constraints.build_constraints(img, voxel_um) -> (WindingGraph, stats)
    with stats["seed_coords"] as (n, 2) in (y, x) of the pyramid level,
    and solver.solve_l1 / solve_bfs_tree on that same graph.

    Coordinates are converted to FULL-RESOLUTION voxels of the volume
    (multiply by 2**level) so they land in the frame the mesh arm uses.

    solver="l1" is the subject; "bfs" is the baseline on the identical
    graph, which isolates solver quality from generator quality.
    """
    import numpy as _np
    from winding_sync.constraints import (build_constraints,
                                          build_constraints_tiled,
                                          TracingConfig)
    from winding_sync.solver import solve_l1, solve_bfs_tree
    from winding_sync.volume import VolumeSource

    vols = volumes or {
        "PHercParis4": ("20260411134726-2.400um-0.2m-78keV-masked.zarr",
                        2.400),
        "PHerc0358": ("20250821151737-9.362um-1.2m-113keV-masked.zarr",
                      9.362),
        "PHerc1447": ("20250521151220-8.640um-1.2m-116keV-masked.zarr",
                      8.640),
        "PHerc0800": ("20250521135224-8.640um-1.2m-116keV-masked.zarr",
                      8.640),
    }
    if scroll not in vols:
        raise SystemExit(f"unknown scroll {scroll}; known: "
                         f"{sorted(vols)}")
    fname, base_um = vols[scroll]
    src = VolumeSource.from_ome_zarr(f"{bucket}/{scroll}/volumes/{fname}",
                                     level=level, base_voxel_um=base_um,
                                     name=scroll)
    z_level = int(z) // (2 ** level)
    img = src.slice_at(z_level).astype(_np.float64)
    # seed_stride_um=None runs the author's default configuration; any
    # other value is OUR variant of his tool and must be labelled as a
    # separate subject, never reported as winding-sync itself (A11).
    cfg = None
    if seed_stride_um is not None:
        cfg = TracingConfig(seed_stride_um=float(seed_stride_um))
    need_gb = img.shape[0] * img.shape[1] * 4 * 6 / 1e9
    if need_gb > tile_threshold_gb:
        graph, stats = build_constraints_tiled(img, src.voxel_um,
                                               config=cfg, progress=True)
    else:
        graph, stats = build_constraints(img, src.voxel_um, config=cfg)

    if solver == "l1":
        w = solve_l1(graph)
    elif solver == "bfs":
        w = _bfs_forest(graph)          # A16: per-component roots
    elif solver == "bfs-single":
        w = solve_bfs_tree(graph)       # upstream behaviour, for comparison
    else:
        raise ValueError(solver)

    yx = _np.asarray(stats["seed_coords"], dtype=_np.float64)
    f = float(2 ** level)
    pts = _np.column_stack([yx[:, 1] * f, yx[:, 0] * f,
                            _np.full(len(yx), float(z))])
    conf = _np.zeros(graph.n_nodes)
    if graph.n_edges:
        _np.add.at(conf, graph.edges[:, 0], graph.weights)
        _np.add.at(conf, graph.edges[:, 1], graph.weights)
    default_stride = TracingConfig().seed_stride_um
    stride_used = (float(seed_stride_um) if seed_stride_um is not None
                   else float(default_stride))
    if name:
        label = name
    elif seed_stride_um is None:
        label = f"winding-sync/{solver}"
    else:
        label = f"winding-sync/{solver}@stride{int(stride_used)}"
    res = AdapterResult(label, pts, _np.asarray(w, float), conf)
    res.stats = {"n_seeds": int(stats.get("n_seeds", len(yx))),
                 "n_edges": int(graph.n_edges),
                 "level": level, "voxel_um": float(src.voxel_um),
                 "z_full_res": int(z), "z_level": z_level,
                 "tiled": bool(need_gb > tile_threshold_gb),
                 "seed_stride_um": stride_used,
                 "author_default_stride_um": float(default_stride),
                 "is_author_config": seed_stride_um is None}
    return res
