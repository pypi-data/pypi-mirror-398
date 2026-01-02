#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic script for scenario8 network

This script analyzes the scenario8 network topology and identifies
potential issues that could cause simulation problems.
"""

from pathlib import Path
import GasNetSim as gns
from GasNetSim.components.utils.network_diagnostics import diagnose_network, export_diagnostics_report

if __name__ == "__main__":
    print("Loading scenario8 network...")
    network = gns.create_network_from_files({
        "nodes":"7nodes_with_compressors_fixed.csv",
        "pipelines":"7pipelines_with_compressors_fixed.csv",
        "compressors": "7compressors_with_compressors_fixed.csv"
    }, initialization_strategy='compressor_aware')

    print()
    print("Running diagnostics...")
    print()

    # Run comprehensive diagnostics
    diagnostics = diagnose_network(network, verbose=True)

    # Export to file
    export_diagnostics_report(network, 'scenario8_diagnostics.txt')

    # Additional analysis: Check which nodes are intermediate
    print()
    print("=" * 80)
    print("INTERMEDIATE NODE ANALYSIS")
    print("=" * 80)
    print()

    intermediate_nodes = []
    for node_id, node in network.nodes.items():
        if node.node_type == 'INTERMEDIATE':
            intermediate_nodes.append(node_id)

    print(f"Total intermediate nodes: {len(intermediate_nodes)}")

    if network.compressors:
        compressor_on_intermediate = []
        for idx, comp in network.compressors.items():
            if comp.inlet_index in intermediate_nodes or comp.outlet_index in intermediate_nodes:
                compressor_on_intermediate.append((idx, comp.inlet_index, comp.outlet_index))

        print(f"Compressors on intermediate nodes: {len(compressor_on_intermediate)}/{len(network.compressors)}")
        if compressor_on_intermediate:
            print()
            print("Details:")
            for idx, inlet, outlet in compressor_on_intermediate[:10]:  # Show first 10
                inlet_type = "INTER" if inlet in intermediate_nodes else "REAL"
                outlet_type = "INTER" if outlet in intermediate_nodes else "REAL"
                print(f"  Compressor {idx}: Node {inlet} ({inlet_type}) → Node {outlet} ({outlet_type})")

    print()
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()

    if diagnostics['summary']['has_critical_issues']:
        print("The network has issues that need to be addressed:")
        print()
        for issue in diagnostics['summary']['all_issues'][:5]:
            print(f"  • {issue}")
        print()
        print("Suggestions:")
        print("  1. Verify network data is correct and complete")
        print("  2. Check that supply/demand balance is feasible")
        print("  3. Ensure all nodes are reachable from reference nodes")
        print("  4. Consider simplifying the network for initial testing")
    else:
        print("No critical topology issues detected.")
        print("If simulation still fails, the issue may be:")
        print("  • Numerical instability due to network scale")
        print("  • Physical impossibility of satisfying constraints")
        print("  • Need for better solver parameters (underrelaxation, etc.)")

    print()
