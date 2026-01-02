#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path

import pytest

from wascal_simulation import (
    read_wascal_network,
    WascalGasNetworkSimulator,
    wascal_network_simulation,
    export_network_summary,
)


FIXTURE_DIR = Path(__file__).parent
WASCAL_DIR = FIXTURE_DIR / "wascal"


def test_can_read_wascal_csvs():
    assert WASCAL_DIR.exists(), f"Missing CSV folder: {WASCAL_DIR}"
    nodes, pipelines, compressors = read_wascal_network(WASCAL_DIR)
    assert len(nodes) > 0, "No nodes loaded"
    assert len(pipelines) > 0, "No pipelines loaded"
    # compressors may be optional but should exist in this scenario
    assert compressors is not None
    print(f"Loaded CSVs: nodes={len(nodes)}, pipes={len(pipelines)}, compressors={len(compressors)}")


def test_validation_and_reference_nodes():
    sim = WascalGasNetworkSimulator(WASCAL_DIR)
    v = sim.validation
    # print validation for quick debugging
    print(f"Validation: missing={v['missing_nodes']}, bad_pipes={v['bad_pipelines']}, bad_compressors={v['bad_compressors']}")
    assert isinstance(v['reference_nodes'], list)
    assert len(sim.nodes) == v['nodes_count']


def test_solve_smoke_debug():
    # Smoke run: small iter count with debug prints
    results = wascal_network_simulation(
        WASCAL_DIR,
        max_iter=10,
        tolerance=1e-2,
        debug=True,
        debug_every=1,
        debug_top=5,
    )
    assert results is not None
    assert 'pressures' in results
    assert 'network_stats' in results
    conv = results['convergence']
    print(f"Convergence: iter={conv['iterations']}, err={conv['error']:.3e}, ok={conv['converged']}")
    if 'debug' in results:
        dbg = results['debug']
        print(f"Residual history (first 5): {dbg['residual_history'][:5]}")
        if dbg['iteration_samples']:
            last = dbg['iteration_samples'][-1]
            print(f"Top residual nodes (iter {last['iter']}): {last['top_residuals']}")


def test_export_summary(tmp_path: Path):
    out_file = export_network_summary(WASCAL_DIR, output_file='wascal_network_summary.txt')
    assert Path(out_file).exists()
    print(f"Summary written to: {out_file}")


if __name__ == '__main__':
    # Allow running this file directly for quick checks without pytest
    test_can_read_wascal_csvs()
    test_validation_and_reference_nodes()
    test_solve_smoke_debug()
    test_export_summary(Path('.'))
