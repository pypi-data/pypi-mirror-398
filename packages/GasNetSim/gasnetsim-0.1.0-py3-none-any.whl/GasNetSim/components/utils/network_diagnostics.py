"""
Network Topology Diagnostics Tool

This module provides functions to analyze and diagnose potential issues
in gas network topology, particularly for networks with compressors.

Author: Created for GasNetSim
Date: 2025
"""

import numpy as np
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


def check_network_connectivity(network):
    """
    Check if all nodes in the network are reachable from reference nodes.

    Args:
        network: Network object

    Returns:
        dict: Diagnostic information including:
            - connected_nodes: Set of nodes reachable from reference nodes
            - disconnected_nodes: Set of unreachable nodes
            - num_components: Number of disconnected components
            - component_sizes: List of component sizes
    """
    # Build adjacency list (bidirectional)
    adjacency = defaultdict(set)

    if network.pipelines:
        for pipeline in network.pipelines.values():
            adjacency[pipeline.inlet_index].add(pipeline.outlet_index)
            adjacency[pipeline.outlet_index].add(pipeline.inlet_index)

    if network.compressors:
        for compressor in network.compressors.values():
            adjacency[compressor.inlet_index].add(compressor.outlet_index)
            # Note: Compressors are unidirectional, but for connectivity check we allow both
            adjacency[compressor.outlet_index].add(compressor.inlet_index)

    if network.resistances:
        for resistance in network.resistances.values():
            adjacency[resistance.inlet_index].add(resistance.outlet_index)
            adjacency[resistance.outlet_index].add(resistance.inlet_index)

    if network.shortpipes:
        for shortpipe in network.shortpipes.values():
            adjacency[shortpipe.inlet_index].add(shortpipe.outlet_index)
            adjacency[shortpipe.outlet_index].add(shortpipe.inlet_index)

    # BFS from reference nodes
    visited = set()
    queue = deque(network.reference_nodes)
    visited.update(network.reference_nodes)

    while queue:
        node = queue.popleft()
        for neighbor in adjacency[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # Find disconnected nodes
    all_nodes = set(network.nodes.keys())
    disconnected = all_nodes - visited

    # Find all components (including disconnected ones)
    components = []
    remaining = all_nodes - visited

    while remaining:
        component = set()
        start = next(iter(remaining))
        comp_queue = deque([start])
        component.add(start)

        while comp_queue:
            node = comp_queue.popleft()
            for neighbor in adjacency[node]:
                if neighbor not in component and neighbor in remaining:
                    component.add(neighbor)
                    comp_queue.append(neighbor)

        components.append(component)
        remaining -= component

    return {
        'connected_nodes': visited,
        'disconnected_nodes': disconnected,
        'num_disconnected': len(disconnected),
        'num_components': len(components) + (1 if visited else 0),
        'component_sizes': [len(visited)] + [len(c) for c in components],
        'disconnected_components': components,
    }


def check_mass_balance_feasibility(network):
    """
    Check if the network's supply and demand balance is feasible.

    Args:
        network: Network object

    Returns:
        dict: Mass balance information
    """
    total_supply = 0
    total_demand = 0
    supply_nodes = []
    demand_nodes = []

    for node_id, node in network.nodes.items():
        if node.volumetric_flow is not None:
            flow = node.volumetric_flow
            if flow < 0:  # Supply (negative flow convention)
                total_supply += abs(flow)
                supply_nodes.append((node_id, flow))
            elif flow > 0:  # Demand
                total_demand += flow
                demand_nodes.append((node_id, flow))

    balance = total_supply - total_demand

    return {
        'total_supply': total_supply,
        'total_demand': total_demand,
        'balance': balance,
        'balance_pct': (balance / total_demand * 100) if total_demand > 0 else 0,
        'num_supply_nodes': len(supply_nodes),
        'num_demand_nodes': len(demand_nodes),
        'supply_nodes': supply_nodes,
        'demand_nodes': demand_nodes,
        'is_balanced': abs(balance) < 1e-6,
    }


def check_compressor_configuration(network):
    """
    Analyze compressor placement and configuration.

    Args:
        network: Network object

    Returns:
        dict: Compressor configuration analysis
    """
    if not network.compressors:
        return {'has_compressors': False}

    issues = []
    compressor_info = []

    for idx, compressor in network.compressors.items():
        inlet_node = network.nodes.get(compressor.inlet_index)
        outlet_node = network.nodes.get(compressor.outlet_index)

        info = {
            'index': idx,
            'inlet': compressor.inlet_index,
            'outlet': compressor.outlet_index,
            'ratio': compressor.compression_ratio,
            'efficiency': compressor.efficiency,
        }

        # Check if nodes exist
        if inlet_node is None:
            issues.append(f"Compressor {idx}: Inlet node {compressor.inlet_index} not found")
            info['inlet_missing'] = True
        else:
            info['inlet_type'] = inlet_node.node_type
            info['inlet_pressure'] = inlet_node.pressure

        if outlet_node is None:
            issues.append(f"Compressor {idx}: Outlet node {compressor.outlet_index} not found")
            info['outlet_missing'] = True
        else:
            info['outlet_type'] = outlet_node.node_type
            info['outlet_pressure'] = outlet_node.pressure

        # Check if nodes are reference nodes (unusual)
        if inlet_node and inlet_node.node_type == 'reference':
            issues.append(f"Compressor {idx}: Inlet is a reference node (unusual)")

        if outlet_node and outlet_node.node_type == 'reference':
            issues.append(f"Compressor {idx}: Outlet is a reference node (may cause conflicts)")

        # Check for series compressors (outlet of one is inlet of another)
        for other_idx, other in network.compressors.items():
            if other_idx != idx and other.inlet_index == compressor.outlet_index:
                info['series_with'] = other_idx

        compressor_info.append(info)

    return {
        'has_compressors': True,
        'num_compressors': len(network.compressors),
        'compressors': compressor_info,
        'issues': issues,
        'num_issues': len(issues),
    }


def check_reference_nodes(network):
    """
    Analyze reference node configuration.

    Args:
        network: Network object

    Returns:
        dict: Reference node analysis
    """
    ref_info = []
    issues = []

    if not network.reference_nodes:
        issues.append("No reference nodes defined - network has no pressure anchor")

    for ref_id in network.reference_nodes:
        node = network.nodes.get(ref_id)
        if node is None:
            issues.append(f"Reference node {ref_id} not found in network")
            continue

        info = {
            'node_id': ref_id,
            'pressure': node.pressure,
            'flow': node.volumetric_flow,
            'has_demand': node.volumetric_flow is not None and node.volumetric_flow != 0,
        }

        if node.pressure is None:
            issues.append(f"Reference node {ref_id} has no pressure defined")

        # Check connections
        connections = []
        if network.pipelines:
            for p in network.pipelines.values():
                if p.inlet_index == ref_id or p.outlet_index == ref_id:
                    connections.append(('pipeline', p.pipeline_index))

        if network.compressors:
            for c in network.compressors.values():
                if c.inlet_index == ref_id:
                    connections.append(('compressor_inlet', c.compressor_index))
                if c.outlet_index == ref_id:
                    connections.append(('compressor_outlet', c.compressor_index))
                    issues.append(f"Reference node {ref_id} is compressor outlet (may cause constraint conflicts)")

        info['num_connections'] = len(connections)
        info['connections'] = connections

        if len(connections) == 0:
            issues.append(f"Reference node {ref_id} has no connections (isolated)")

        ref_info.append(info)

    return {
        'num_reference_nodes': len(network.reference_nodes),
        'reference_nodes': ref_info,
        'issues': issues,
        'num_issues': len(issues),
    }


def diagnose_network(network, verbose=True):
    """
    Perform comprehensive network diagnostics.

    Args:
        network: Network object
        verbose: If True, print diagnostic report

    Returns:
        dict: Complete diagnostic information
    """
    diagnostics = {
        'network_size': {
            'num_nodes': len(network.nodes),
            'num_pipelines': len(network.pipelines) if network.pipelines else 0,
            'num_compressors': len(network.compressors) if network.compressors else 0,
            'num_resistances': len(network.resistances) if network.resistances else 0,
        },
        'connectivity': check_network_connectivity(network),
        'mass_balance': check_mass_balance_feasibility(network),
        'compressors': check_compressor_configuration(network),
        'reference_nodes': check_reference_nodes(network),
    }

    # Aggregate all issues
    all_issues = []

    conn = diagnostics['connectivity']
    if conn['num_disconnected'] > 0:
        all_issues.append(f"Network has {conn['num_disconnected']} disconnected nodes")
        all_issues.append(f"Network has {conn['num_components']} separate components")

    mb = diagnostics['mass_balance']
    if not mb['is_balanced']:
        all_issues.append(f"Mass balance mismatch: {mb['balance']:.2f} sm³/s ({mb['balance_pct']:.1f}%)")

    if mb['num_supply_nodes'] == 0:
        all_issues.append("No supply nodes defined")

    all_issues.extend(diagnostics['compressors'].get('issues', []))
    all_issues.extend(diagnostics['reference_nodes']['issues'])

    diagnostics['summary'] = {
        'all_issues': all_issues,
        'num_issues': len(all_issues),
        'has_critical_issues': len(all_issues) > 0,
    }

    if verbose:
        print_diagnostic_report(diagnostics)

    return diagnostics


def print_diagnostic_report(diagnostics):
    """
    Print a formatted diagnostic report.

    Args:
        diagnostics: Diagnostic dictionary from diagnose_network()
    """
    print("=" * 80)
    print("NETWORK TOPOLOGY DIAGNOSTIC REPORT")
    print("=" * 80)
    print()

    # Network size
    size = diagnostics['network_size']
    print(f"Network Size:")
    print(f"  • Nodes: {size['num_nodes']}")
    print(f"  • Pipelines: {size['num_pipelines']}")
    print(f"  • Compressors: {size['num_compressors']}")
    print(f"  • Resistances: {size['num_resistances']}")
    print()

    # Connectivity
    conn = diagnostics['connectivity']
    print(f"Connectivity Analysis:")
    print(f"  • Connected nodes: {len(conn['connected_nodes'])}/{size['num_nodes']}")
    print(f"  • Disconnected nodes: {conn['num_disconnected']}")
    print(f"  • Number of components: {conn['num_components']}")
    if conn['num_components'] > 1:
        print(f"  • Component sizes: {conn['component_sizes']}")
    if conn['num_disconnected'] > 0:
        print(f"  ⚠️  WARNING: {conn['num_disconnected']} nodes unreachable from reference nodes")
        if conn['num_disconnected'] <= 10:
            print(f"     Disconnected nodes: {sorted(list(conn['disconnected_nodes']))}")
    print()

    # Mass balance
    mb = diagnostics['mass_balance']
    print(f"Mass Balance:")
    print(f"  • Total supply: {mb['total_supply']:.2f} sm³/s")
    print(f"  • Total demand: {mb['total_demand']:.2f} sm³/s")
    print(f"  • Balance: {mb['balance']:.2f} sm³/s ({mb['balance_pct']:.2f}%)")
    print(f"  • Supply nodes: {mb['num_supply_nodes']}")
    print(f"  • Demand nodes: {mb['num_demand_nodes']}")
    if not mb['is_balanced']:
        print(f"  ⚠️  WARNING: Network is not mass-balanced")
    print()

    # Reference nodes
    ref = diagnostics['reference_nodes']
    print(f"Reference Nodes:")
    print(f"  • Count: {ref['num_reference_nodes']}")
    for ref_info in ref['reference_nodes']:
        print(f"  • Node {ref_info['node_id']}: {ref_info['pressure']/1e5:.1f} bar, "
              f"{ref_info['num_connections']} connections")
    if ref['num_issues'] > 0:
        print(f"  ⚠️  {ref['num_issues']} issue(s) with reference nodes")
    print()

    # Compressors
    comp = diagnostics['compressors']
    if comp['has_compressors']:
        print(f"Compressor Configuration:")
        print(f"  • Count: {comp['num_compressors']}")

        # Check for intermediate nodes
        intermediate_count = sum(1 for c in comp['compressors']
                                if c.get('inlet_type') == 'INTERMEDIATE' or c.get('outlet_type') == 'INTERMEDIATE')
        if intermediate_count > 0:
            print(f"  • Compressors on intermediate nodes: {intermediate_count}/{comp['num_compressors']}")
            print(f"    (Intermediate nodes are auto-generated when splitting long pipelines)")

        if comp['num_issues'] > 0:
            print(f"  ⚠️  {comp['num_issues']} issue(s) with compressor configuration")
    print()

    # Summary
    summary = diagnostics['summary']
    print("=" * 80)
    if summary['num_issues'] == 0:
        print("✅ No critical issues detected")
    else:
        print(f"⚠️  {summary['num_issues']} POTENTIAL ISSUE(S) DETECTED:")
        print()
        for i, issue in enumerate(summary['all_issues'], 1):
            print(f"  {i}. {issue}")
    print("=" * 80)


def export_diagnostics_report(network, output_file='network_diagnostics.txt'):
    """
    Export diagnostic report to a text file.

    Args:
        network: Network object
        output_file: Output file path
    """
    import sys
    from io import StringIO

    # Capture print output
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    diagnostics = diagnose_network(network, verbose=True)

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    with open(output_file, 'w') as f:
        f.write(output)

    print(f"Diagnostic report exported to: {output_file}")

    return diagnostics
