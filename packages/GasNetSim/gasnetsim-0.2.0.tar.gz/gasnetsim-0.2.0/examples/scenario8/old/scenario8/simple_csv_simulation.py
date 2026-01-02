#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.constants import bar
import argparse

def read_network_csv(folder_path):
    """Read CSV files and return network data."""
    folder = Path(folder_path)
    
    # Find CSV files automatically
    nodes_file = list(folder.glob("*nodes*.csv"))[0]
    pipelines_file = list(folder.glob("*pipelines*.csv"))[0]
    compressors_file = list(folder.glob("*compressors*.csv"))[0]
    
    print(f"Reading nodes from: {nodes_file.name}")
    print(f"Reading pipelines from: {pipelines_file.name}")
    print(f"Reading compressors from: {compressors_file.name}")
    
    nodes = pd.read_csv(nodes_file, sep=';')
    pipelines = pd.read_csv(pipelines_file, sep=';')
    compressors = pd.read_csv(compressors_file, sep=';')
    
    return nodes, pipelines, compressors

def solve_gas_network_csv(folder_path, P2_power_mw=-300, use_gas_turbine_compressor=False):
    """
    Solve gas network using CSV files - adapted from your original function.
    """
    
    # Constants
    rho = 0.8  # kg/sm3
    heating_value = 50  # MJ/kg
    gas_turbine_efficiency = 0.35
    
    # Read CSV data
    nodes_df, pipelines_df, compressors_df = read_network_csv(folder_path)
    
    # Extract parameters from CSV
    # Assuming nodes are indexed 1-4 as in your original code
    node_data = {}
    for _, row in nodes_df.iterrows():
        idx = int(row['node_index'])
        node_data[idx] = {
            'pressure': row['pressure_pa'],
            'temperature': row['temperature_k'], 
            'altitude': row['altitude_m'],
            'demand': row['flow_sm3_per_s']
        }
    
    # Extract pipeline data
    pipeline_data = {}
    for _, row in pipelines_df.iterrows():
        if pd.notna(row['pipeline_index']):
            idx = int(row['pipeline_index'])
            pipeline_data[idx] = {
                'inlet': int(row['inlet_index']),
                'outlet': int(row['outlet_index']),
                'diameter': row['diameter_m'],
                'length': row['length_m'],
                'roughness': row['roughness'],
                'efficiency': row['efficiency']
            }
    
    # Extract compressor data
    compressor_data = compressors_df.iloc[0]  # Assume single compressor
    compression_ratio = compressor_data['compression_ratio']
    
    # Reference pressure from node 1
    p1 = node_data[1]['pressure'] / 1e5 * bar  # Convert Pa to bar
    
    # Node properties
    h1, h2, h3, h4 = [node_data[i]['altitude'] for i in range(1, 5)]
    T1, T2, T3, T4 = [node_data[i]['temperature'] for i in range(1, 5)]
    D2, D3 = node_data[2]['demand'], node_data[3]['demand']
    D4 = abs(P2_power_mw) / (heating_value * gas_turbine_efficiency)
    
    # Calculate pipe constants from CSV data
    def c_pipe(T1, T2, L, D, f, eta):
        return eta * D**2.5 / (f * L * rho * (T1 + T2) / 2)**0.5
    
    # Map pipelines to connections (assuming same topology as original)
    pipe_constants = {}
    for pipe_id, pipe in pipeline_data.items():
        inlet, outlet = pipe['inlet'], pipe['outlet']
        if (inlet, outlet) in [(1, 2), (2, 1)]:
            pipe_constants['12'] = c_pipe(T1, T2, pipe['length'], pipe['diameter'], 
                                        pipe['roughness'], pipe['efficiency'])
        elif (inlet, outlet) in [(3, 4), (4, 3)]:
            pipe_constants['34'] = c_pipe(T3, T4, pipe['length'], pipe['diameter'],
                                        pipe['roughness'], pipe['efficiency'])
        elif (inlet, outlet) in [(1, 4), (4, 1)]:
            pipe_constants['14'] = c_pipe(T1, T4, pipe['length'], pipe['diameter'],
                                        pipe['roughness'], pipe['efficiency'])
    
    c12 = pipe_constants.get('12', 0)
    c34 = pipe_constants.get('34', 0) 
    c14 = pipe_constants.get('14', 0)
    
    def height_effect(h1, h2, p1, p2, T1, T2):
        g, R = 9.81, 287
        return g * rho * (h2 - h1) * (T1 + T2) / (2 * R)
    
    def flow_direction(p1, p2, e):
        return 1 if (p1**2 - p2**2 - e) > 0 else -1
    
    def compressor_power(mass_flow_rate, T_inlet, p_inlet, p_outlet):
        if mass_flow_rate <= 0:
            return 0.0
        cp, gamma = 2.1, 1.3
        compression_ratio = p_outlet / p_inlet
        power_kw = (cp * T_inlet * mass_flow_rate * 
                    (compression_ratio**((gamma-1)/gamma) - 1) / 0.85)
        return power_kw / 1000
    
    # Newton-Raphson solver
    p = np.array([0.9 * p1, 0.8 * p1])
    tol, n_iter, max_iter = 1e-6, 0, 100
    err = 1
    
    while err > tol and n_iter < max_iter:
        p2, p4 = p
        p3 = p2 * compression_ratio
        
        # Height effects
        e12 = height_effect(h1, h2, p1, p2, T1, T2)
        e34 = height_effect(h3, h4, p3, p4, T3, T4)
        e14 = height_effect(h1, h4, p1, p4, T1, T4)
        
        # Flow rates
        q12 = flow_direction(p1, p2, e12) * c12 * abs(p1**2 - p2**2 - e12)**0.5
        q34 = flow_direction(p3, p4, e34) * c34 * abs(p3**2 - p4**2 - e34)**0.5
        q14 = flow_direction(p1, p4, e14) * c14 * abs(p1**2 - p4**2 - e14)**0.5
        
        q_compressor = q34 + D3
        gas_for_compressor = 0
        
        if use_gas_turbine_compressor:
            power_mw = compressor_power(q_compressor * rho, T2, p2, p3)
            gas_for_compressor = power_mw / (heating_value * gas_turbine_efficiency)
        
        # Residuals
        f_calculated = np.array([q12 - q_compressor - gas_for_compressor, q34 + q14])
        f_target = np.array([D2, D4])
        delta_f = f_target - f_calculated
        err = max(abs(delta_f))
        
        if err < tol:
            break
        
        # Jacobian
        dq12_dp2 = -c12 * p2 / abs(p1**2 - p2**2 - e12)**0.5
        dq34_dp4 = -c34 * p4 / abs(p3**2 - p4**2 - e34)**0.5
        dq14_dp4 = -c14 * p4 / abs(p1**2 - p4**2 - e14)**0.5
        dq34_dp2 = c34 * p3 * compression_ratio / abs(p3**2 - p4**2 - e34)**0.5
        
        j11 = dq12_dp2 - dq34_dp2
        j12 = -dq34_dp4
        j21 = dq34_dp2
        j22 = dq34_dp4 + dq14_dp4
        
        J = np.array([[j11, j12], [j21, j22]])
        
        # Update step
        p += np.linalg.solve(J, delta_f)
        n_iter += 1
    
    # Final Results
    p2, p4 = p
    p3 = p2 * compression_ratio
    
    e12 = height_effect(h1, h2, p1, p2, T1, T2)
    e34 = height_effect(h3, h4, p3, p4, T3, T4)
    e14 = height_effect(h1, h4, p1, p4, T1, T4)
    
    q12 = flow_direction(p1, p2, e12) * c12 * abs(p1**2 - p2**2 - e12)**0.5
    q34 = flow_direction(p3, p4, e34) * c34 * abs(p3**2 - p4**2 - e34)**0.5
    q14 = flow_direction(p1, p4, e14) * c14 * abs(p1**2 - p4**2 - e14)**0.5
    
    q_compressor = q34 + D3
    compressor_power_mw = compressor_power(q_compressor * rho, T2, p2, p3)
    gas_for_compressor = (compressor_power_mw / (heating_value * gas_turbine_efficiency) 
                         if use_gas_turbine_compressor else 0.0)
    
    return {
        'pressures': {'p1': p1/bar, 'p2': p2/bar, 'p3': p3/bar, 'p4': p4/bar},
        'flows': {'Pipe 1-2': q12, 'Compressor 2-3': q_compressor, 'Pipe 3-4': q34, 'Pipe 1-4': q14},
        'compressor': {'power_mw': compressor_power_mw, 'gas_consumption': gas_for_compressor},
        'convergence': {'iterations': n_iter, 'error': err},
        'csv_data': {
            'nodes': node_data,
            'pipelines': pipeline_data,
            'compressor': {
                'compression_ratio': compression_ratio,
                'efficiency': compressor_data['efficiency'],
                'process': compressor_data['thermodynamic_process']
            }
        }
    }

def print_results(results):
    """Print results in a formatted way."""
    print("\n" + "="*60)
    print("GAS NETWORK SIMULATION RESULTS (from CSV)")
    print("="*60)
    
    print("\nNETWORK CONFIGURATION:")
    nodes = results['csv_data']['nodes']
    for node_id in sorted(nodes.keys()):
        node = nodes[node_id]
        print(f"  Node {node_id}: P={node['pressure']/1e5:.1f} bar, "
              f"T={node['temperature']:.1f} K, "
              f"H={node['altitude']:.1f} m, "
              f"D={node['demand']:.1f} sm³/s")
    
    print(f"\nCompressor: {results['csv_data']['compressor']['compression_ratio']:.1f} ratio, "
          f"{results['csv_data']['compressor']['efficiency']:.2f} efficiency")
    
    print("\nSOLUTION:")
    print("Pressures (bar):")
    for node, pressure in results['pressures'].items():
        print(f"  {node}: {pressure:.2f}")
    
    print("\nFlow Rates (sm³/s):")
    for component, flow in results['flows'].items():
        print(f"  {component}: {flow:.3f}")
    
    print(f"\nCompressor Power: {results['compressor']['power_mw']:.2f} MW")
    print(f"Gas Consumption: {results['compressor']['gas_consumption']:.3f} sm³/s")
    
    print(f"\nConvergence: {results['convergence']['iterations']} iterations, "
          f"error = {results['convergence']['error']:.2e}")
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple Gas Network Simulation from CSV')
    parser.add_argument('csv_folder', help='Path to folder with CSV files')
    parser.add_argument('--power-mw', type=float, default=-300,
                       help='Power demand in MW (default: -300)')
    parser.add_argument('--gas-turbine', action='store_true',
                       help='Use gas turbine compressor')
    
    args = parser.parse_args()
    
    try:
        print("Running CSV-based gas network simulation...")
        
        # Electric compressor
        results1 = solve_gas_network_csv(
            args.csv_folder, 
            P2_power_mw=args.power_mw, 
            use_gas_turbine_compressor=False
        )
        
        print("\nRESULTS - ELECTRIC COMPRESSOR:")
        print_results(results1)
        
        if args.gas_turbine:
            # Gas turbine compressor
            results2 = solve_gas_network_csv(
                args.csv_folder,
                P2_power_mw=args.power_mw,
                use_gas_turbine_compressor=True
            )
            
            print("\n\nRESULTS - GAS TURBINE COMPRESSOR:")
            print_results(results2)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()