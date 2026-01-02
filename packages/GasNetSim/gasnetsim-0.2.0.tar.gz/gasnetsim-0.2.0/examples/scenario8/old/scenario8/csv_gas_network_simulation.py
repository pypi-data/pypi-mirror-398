#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.constants import bar

def read_csv_data(folder_path):
    """
    Read CSV files for nodes, pipelines, and compressors.
    
    Parameters:
    folder_path (str): Path to folder containing CSV files
    
    Returns:
    dict: Dictionary containing DataFrames for nodes, pipelines, and compressors
    """
    folder = Path(folder_path)
    
    data = {}
    
    # Read nodes CSV
    nodes_file = folder / "minimal_network_with_compressor_nodes.csv"
    if nodes_file.exists():
        data['nodes'] = pd.read_csv(nodes_file, sep=';')
    else:
        raise FileNotFoundError(f"Nodes file not found: {nodes_file}")
    
    # Read pipelines CSV
    pipelines_file = folder / "minimal_network_with_compressor_pipelines.csv"
    if pipelines_file.exists():
        data['pipelines'] = pd.read_csv(pipelines_file, sep=';')
    else:
        raise FileNotFoundError(f"Pipelines file not found: {pipelines_file}")
    
    # Read compressors CSV
    compressors_file = folder / "minimal_network_with_compressor_compressors.csv"
    if compressors_file.exists():
        data['compressors'] = pd.read_csv(compressors_file, sep=';')
    else:
        raise FileNotFoundError(f"Compressors file not found: {compressors_file}")
    
    return data

def extract_network_parameters(data):
    """
    Extract network parameters from CSV data.
    
    Parameters:
    data (dict): Dictionary containing DataFrames for nodes, pipelines, and compressors
    
    Returns:
    dict: Dictionary containing extracted parameters
    """
    nodes_df = data['nodes']
    pipelines_df = data['pipelines'] 
    compressors_df = data['compressors']
    
    # Extract node information
    nodes = {}
    for _, row in nodes_df.iterrows():
        nodes[int(row['node_index'])] = {
            'pressure': row['pressure_pa'],
            'temperature': row['temperature_k'],
            'altitude': row['altitude_m'],
            'demand': row['flow_sm3_per_s'],
            'node_type': row['node_type']
        }
    
    # Extract pipeline information
    pipelines = {}
    for _, row in pipelines_df.iterrows():
        pipelines[int(row['pipeline_index'])] = {
            'inlet': int(row['inlet_index']),
            'outlet': int(row['outlet_index']),
            'diameter': row['diameter_m'],
            'length': row['length_m'],
            'roughness': row['roughness'],
            'efficiency': row['efficiency']
        }
    
    # Extract compressor information
    compressors = {}
    for _, row in compressors_df.iterrows():
        compressors[int(row['compressor_index'])] = {
            'inlet': int(row['inlet']),
            'outlet': int(row['outlet']),
            'compression_ratio': row['compression_ratio'],
            'efficiency': row['efficiency'],
            'process': row['thermodynamic_process']
        }
    
    return {
        'nodes': nodes,
        'pipelines': pipelines, 
        'compressors': compressors
    }

# Gas properties and constants
rho = 0.8  # kg/sm3
heating_value = 50  # MJ/kg
gas_turbine_efficiency = 0.35
compression_ratio = 1.2

def c_pipe(T1, T2, L, D, f, eta):
    """Calculate pipe constant for flow calculations."""
    return eta * D**2.5 / (f * L * rho * (T1 + T2) / 2)**0.5

def height_effect(h1, h2, p1, p2, T1, T2):
    """Calculate height effect correction."""
    g = 9.81
    R = 287
    return g * rho * (h2 - h1) * (T1 + T2) / (2 * R)

def flow_direction(p1, p2, height_effect):
    """Determine flow direction based on pressure difference."""
    return 1 if (p1**2 - p2**2 - height_effect) > 0 else -1

def compressor_power(mass_flow_rate, T_inlet, p_inlet, p_outlet):
    """Calculate compressor power consumption in MW."""
    if mass_flow_rate <= 0:
        return 0.0
    
    cp = 2.1  # kJ/kg·K for natural gas
    gamma = 1.3  # specific heat ratio
    
    compression_ratio = p_outlet / p_inlet
    
    power_kw = (cp * T_inlet * mass_flow_rate * 
                (compression_ratio**((gamma-1)/gamma) - 1) / 0.85)
    
    return power_kw / 1000  # Convert to MW

def solve_gas_network_from_csv(csv_folder_path, P2_power_mw=-300, use_gas_turbine_compressor=False):
    """
    Solve gas network using CSV input files.
    
    Parameters:
    csv_folder_path (str): Path to folder containing CSV files
    P2_power_mw (float): Power demand at node 2 in MW (negative for consumption)
    use_gas_turbine_compressor (bool): Whether to use gas turbine for compressor drive
    
    Returns:
    dict: Dictionary containing solution results
    """
    
    # Read CSV data
    data = read_csv_data(csv_folder_path)
    params = extract_network_parameters(data)
    
    # Extract network structure
    nodes = params['nodes']
    pipelines = params['pipelines']
    compressors = params['compressors']
    
    # Get reference pressure from CSV (node 1)
    p1 = nodes[1]['pressure'] / 1e5 * bar  # Convert Pa to bar
    
    # Get node properties
    node_heights = {i: nodes[i]['altitude'] for i in nodes}
    node_temps = {i: nodes[i]['temperature'] for i in nodes}
    node_demands = {i: nodes[i]['demand'] for i in nodes}
    
    # Calculate pipe constants from CSV data
    pipe_constants = {}
    for pipe_id, pipe_data in pipelines.items():
        inlet_node = pipe_data['inlet']
        outlet_node = pipe_data['outlet']
        T1 = node_temps[inlet_node]
        T2 = node_temps[outlet_node]
        
        pipe_constants[pipe_id] = c_pipe(
            T1, T2, pipe_data['length'], pipe_data['diameter'],
            pipe_data['roughness'], pipe_data['efficiency']
        )
    
    # Get compressor properties
    compressor = list(compressors.values())[0]  # Assuming single compressor
    compression_ratio = compressor['compression_ratio']
    
    # Convert power demand to gas demand
    D4 = abs(P2_power_mw) / (heating_value * gas_turbine_efficiency)
    
    # Initialize pressure estimates
    p = np.array([0.9 * p1, 0.8 * p1])
    tol, n_iter, max_iter = 1e-6, 0, 100
    err = 1
    
    while err > tol and n_iter < max_iter:
        p2, p4 = p
        p3 = p2 * compression_ratio
        
        # Height effects for each pipeline
        height_effects = {}
        for pipe_id, pipe_data in pipelines.items():
            inlet_node = pipe_data['inlet']
            outlet_node = pipe_data['outlet']
            
            if inlet_node == 1 and outlet_node == 2:
                h1, h2 = node_heights[1], node_heights[2]
                T1, T2 = node_temps[1], node_temps[2]
                height_effects[pipe_id] = height_effect(h1, h2, p1, p2, T1, T2)
            elif inlet_node == 3 and outlet_node == 4:
                h3, h4 = node_heights[3], node_heights[4]
                T3, T4 = node_temps[3], node_temps[4]
                height_effects[pipe_id] = height_effect(h3, h4, p3, p4, T3, T4)
            elif inlet_node == 1 and outlet_node == 4:
                h1, h4 = node_heights[1], node_heights[4]
                T1, T4 = node_temps[1], node_temps[4]
                height_effects[pipe_id] = height_effect(h1, h4, p1, p4, T1, T4)
        
        # Calculate flow rates for each pipeline
        flows = {}
        for pipe_id, pipe_data in pipelines.items():
            inlet_node = pipe_data['inlet']
            outlet_node = pipe_data['outlet']
            
            if inlet_node == 1 and outlet_node == 2:
                e12 = height_effects[pipe_id]
                flows[pipe_id] = (flow_direction(p1, p2, e12) * pipe_constants[pipe_id] * 
                                abs(p1**2 - p2**2 - e12)**0.5)
            elif inlet_node == 3 and outlet_node == 4:
                e34 = height_effects[pipe_id]
                flows[pipe_id] = (flow_direction(p3, p4, e34) * pipe_constants[pipe_id] * 
                                abs(p3**2 - p4**2 - e34)**0.5)
            elif inlet_node == 1 and outlet_node == 4:
                e14 = height_effects[pipe_id]
                flows[pipe_id] = (flow_direction(p1, p4, e14) * pipe_constants[pipe_id] * 
                                abs(p1**2 - p4**2 - e14)**0.5)
        
        # Find flows by pipeline connection
        q12 = next(flows[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 1 and pdata['outlet'] == 2)
        q34 = next(flows[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 3 and pdata['outlet'] == 4)
        q14 = next(flows[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 1 and pdata['outlet'] == 4)
        
        # Compressor flow calculation
        q_compressor = q34 + node_demands[3]
        gas_for_compressor = 0
        
        if use_gas_turbine_compressor:
            power_mw = compressor_power(q_compressor * rho, node_temps[2], p2, p3)
            gas_for_compressor = power_mw / (heating_value * gas_turbine_efficiency)
        
        # Mass balance equations
        f_calculated = np.array([
            q12 - q_compressor - gas_for_compressor,  # Node 2 balance
            q34 + q14  # Node 4 balance
        ])
        f_target = np.array([node_demands[2], D4])
        delta_f = f_target - f_calculated
        err = max(abs(delta_f))
        
        if err < tol:
            break
        
        # Calculate Jacobian matrix
        # Find height effects needed for derivatives
        e12 = next(height_effects[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 1 and pdata['outlet'] == 2)
        e34 = next(height_effects[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 3 and pdata['outlet'] == 4)
        e14 = next(height_effects[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 1 and pdata['outlet'] == 4)
        
        # Find pipe constants
        c12 = next(pipe_constants[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 1 and pdata['outlet'] == 2)
        c34 = next(pipe_constants[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 3 and pdata['outlet'] == 4)
        c14 = next(pipe_constants[pid] for pid, pdata in pipelines.items() 
                  if pdata['inlet'] == 1 and pdata['outlet'] == 4)
        
        dq12_dp2 = -c12 * p2 / abs(p1**2 - p2**2 - e12)**0.5
        dq34_dp4 = -c34 * p4 / abs(p3**2 - p4**2 - e34)**0.5
        dq14_dp4 = -c14 * p4 / abs(p1**2 - p4**2 - e14)**0.5
        dq34_dp2 = c34 * p3 * compression_ratio / abs(p3**2 - p4**2 - e34)**0.5
        
        j11 = dq12_dp2 - dq34_dp2
        j12 = -dq34_dp4
        j21 = dq34_dp2
        j22 = dq34_dp4 + dq14_dp4
        
        J = np.array([[j11, j12], [j21, j22]])
        
        # Update pressures
        p += np.linalg.solve(J, delta_f)
        n_iter += 1
    
    # Final results calculation
    p2, p4 = p
    p3 = p2 * compression_ratio
    
    # Recalculate final flows
    final_flows = {}
    for pipe_id, pipe_data in pipelines.items():
        inlet_node = pipe_data['inlet']
        outlet_node = pipe_data['outlet']
        
        if inlet_node == 1 and outlet_node == 2:
            e12 = height_effect(node_heights[1], node_heights[2], p1, p2, 
                              node_temps[1], node_temps[2])
            final_flows['Pipe 1-2'] = (flow_direction(p1, p2, e12) * pipe_constants[pipe_id] * 
                                      abs(p1**2 - p2**2 - e12)**0.5)
        elif inlet_node == 3 and outlet_node == 4:
            e34 = height_effect(node_heights[3], node_heights[4], p3, p4, 
                              node_temps[3], node_temps[4])
            final_flows['Pipe 3-4'] = (flow_direction(p3, p4, e34) * pipe_constants[pipe_id] * 
                                      abs(p3**2 - p4**2 - e34)**0.5)
        elif inlet_node == 1 and outlet_node == 4:
            e14 = height_effect(node_heights[1], node_heights[4], p1, p4, 
                              node_temps[1], node_temps[4])
            final_flows['Pipe 1-4'] = (flow_direction(p1, p4, e14) * pipe_constants[pipe_id] * 
                                      abs(p1**2 - p4**2 - e14)**0.5)
    
    q_compressor_final = final_flows['Pipe 3-4'] + node_demands[3]
    compressor_power_mw = compressor_power(q_compressor_final * rho, node_temps[2], p2, p3)
    gas_for_compressor_final = (compressor_power_mw / (heating_value * gas_turbine_efficiency) 
                              if use_gas_turbine_compressor else 0.0)
    
    return {
        'pressures': {
            'p1': p1/bar, 'p2': p2/bar, 'p3': p3/bar, 'p4': p4/bar
        },
        'flows': {
            'Pipe 1-2': final_flows['Pipe 1-2'],
            'Compressor 2-3': q_compressor_final,
            'Pipe 3-4': final_flows['Pipe 3-4'],
            'Pipe 1-4': final_flows['Pipe 1-4']
        },
        'compressor': {
            'power_mw': compressor_power_mw,
            'gas_consumption': gas_for_compressor_final
        },
        'convergence': {
            'iterations': n_iter,
            'error': err
        },
        'network_data': {
            'nodes': nodes,
            'pipelines': pipelines,
            'compressors': compressors
        }
    }

def print_results(results):
    """Print simulation results in a formatted way."""
    print("=" * 60)
    print("GAS NETWORK SIMULATION RESULTS")
    print("=" * 60)
    
    print("\nPRESSURES (bar):")
    for node, pressure in results['pressures'].items():
        print(f"  {node}: {pressure:.2f}")
    
    print("\nFLOW RATES (sm³/s):")
    for component, flow in results['flows'].items():
        print(f"  {component}: {flow:.3f}")
    
    print("\nCOMPRESSOR:")
    print(f"  Power consumption: {results['compressor']['power_mw']:.2f} MW")
    print(f"  Gas consumption: {results['compressor']['gas_consumption']:.3f} sm³/s")
    
    print("\nCONVERGENCE:")
    print(f"  Iterations: {results['convergence']['iterations']}")
    print(f"  Final error: {results['convergence']['error']:.2e}")
    
    print("=" * 60)

if __name__ == "__main__":
    # Test with minimal example
    csv_folder = "./minimal_example"
    
    print("Testing CSV-based gas network simulation...")
    
    # Run simulation with electric compressor
    results_electric = solve_gas_network_from_csv(
        csv_folder, 
        P2_power_mw=-300, 
        use_gas_turbine_compressor=False
    )
    
    print("\nRESULTS WITH ELECTRIC COMPRESSOR:")
    print_results(results_electric)
    
    # Run simulation with gas turbine compressor
    results_gas_turbine = solve_gas_network_from_csv(
        csv_folder, 
        P2_power_mw=-300, 
        use_gas_turbine_compressor=True
    )
    
    print("\n\nRESULTS WITH GAS TURBINE COMPRESSOR:")
    print_results(results_gas_turbine)