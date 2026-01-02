#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import sys


def ensure_gns_on_path():
    here = Path(__file__).resolve()
    for p in here.parents:
        candidate = p / "gasnetsim"
        if (candidate / "GasNetSim").exists():
            sys.path.insert(0, str(candidate))
            return True
    return False


def main(folder, max_iter, tol):
    ok = ensure_gns_on_path()
    if not ok:
        print("Could not locate local GasNetSim package; please run from repo.")
        sys.exit(1)

    import GasNetSim as gns

    folder = Path(folder)
    print(f"Running GasNetSim on folder: {folder}")
    network = gns.create_network_from_folder(folder)
    print(
        f"Network: nodes={len(network.nodes)}, pipelines={len(network.pipelines) if network.pipelines else 0}, compressors={len(network.compressors) if network.compressors else 0}"
    )

    try:
        network.simulation(tracking_method=None, max_iter=max_iter, tol=tol)
        print("Simulation converged.")
    except Exception as e:
        print(f"Simulation raised: {e}")

    # Print reference nodes and a few sample pressures
    print(f"Reference nodes: {network.reference_nodes}")
    for nid in sorted(list(network.nodes.keys()))[:10]:
        n = network.nodes[nid]
        print(f"  Node {nid}: {n.pressure/1e5 if n.pressure else 0:.2f} bar, flow={n.volumetric_flow}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run GasNetSim on scenario 8 WASCAL inputs")
    parser.add_argument("folder", nargs="?", default="./wascal", help="Path to CSV folder")
    parser.add_argument("--max-iter", type=int, default=50)
    parser.add_argument("--tol", type=float, default=1e-3)
    args = parser.parse_args()

    main(args.folder, args.max_iter, args.tol)
