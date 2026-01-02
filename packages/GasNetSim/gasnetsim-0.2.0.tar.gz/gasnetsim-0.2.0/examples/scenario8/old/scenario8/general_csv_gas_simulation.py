#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.constants import bar
import argparse

def read_csv_data(folder_path, nodes_file=None, pipelines_file=None, compressors_file=None):
    """
    Read CSV files for nodes, pipelines, and compressors.
    
    Parameters:
    folder_path (str): Path to folder containing CSV files
    nodes_file (str, optional): Custom nodes filename
    pipelines_file (str, optional): Custom pipelines filename  
    compressors_file (str, optional): Custom compressors filename
    
    Returns:
    dict: Dictionary containing DataFrames for nodes, pipelines, and compressors
    """
    folder = Path(folder_path)
    
    data = {}
    
    # Default file patterns
    if nodes_file is None:
        nodes_files = list(folder.glob("*nodes*.csv"))
        if not nodes_files:
            raise FileNotFoundError(f"No nodes CSV file found in {folder}")
        nodes_file = nodes_files[0]
    else:
        nodes_file = folder / nodes_file
        
    if pipelines_file is None:
        pipelines_files = list(folder.glob("*pipelines*.csv"))
        if not pipelines_files:
            raise FileNotFoundError(f"No pipelines CSV file found in {folder}")
        pipelines_file = pipelines_files[0]
    else:
        pipelines_file = folder / pipelines_file
        
    if compressors_file is None:
        compressors_files = list(folder.glob("*compressors*.csv"))
        if not compressors_files:
            raise FileNotFoundError(f"No compressors CSV file found in {folder}")
        compressors_file = compressors_files[0]
    else:
        compressors_file = folder / compressors_file
    
    # Read CSV files
    print(f"Reading nodes from: {nodes_file}")
    data['nodes'] = pd.read_csv(nodes_file, sep=';')
    
    print(f"Reading pipelines from: {pipelines_file}")
    data['pipelines'] = pd.read_csv(pipelines_file, sep=';')
    
    print(f"Reading compressors from: {compressors_file}")
    data['compressors'] = pd.read_csv(compressors_file, sep=';')
    
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
        if pd.notna(row['pipeline_index']):  # Skip empty rows
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
        if pd.notna(row['compressor_index']):  # Skip empty rows
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

class GasNetworkSimulator:
    """Gas network simulator using CSV input data."""
    
    def __init__(self, csv_folder_path, nodes_file=None, pipelines_file=None, compressors_file=None):
        """Initialize simulator with CSV data."""
        self.rho = 0.8  # kg/sm3
        self.heating_value = 50  # MJ/kg
        self.gas_turbine_efficiency = 0.35
        
        # Read and parse CSV data
        self.raw_data = read_csv_data(csv_folder_path, nodes_file, pipelines_file, compressors_file)
        self.params = extract_network_parameters(self.raw_data)
        
        # Extract network components
        self.nodes = self.params['nodes']
        self.pipelines = self.params['pipelines']
        self.compressors = self.params['compressors']
        
        print(f"Loaded network with {len(self.nodes)} nodes, {len(self.pipelines)} pipelines, {len(self.compressors)} compressors")
        
        # Pre-calculate pipe constants
        self._calculate_pipe_constants()
    
    def _calculate_pipe_constants(self):
        """Pre-calculate pipe constants for flow calculations."""
        self.pipe_constants = {}
        
        for pipe_id, pipe_data in self.pipelines.items():
            inlet_node = pipe_data['inlet']
            outlet_node = pipe_data['outlet']
            T1 = self.nodes[inlet_node]['temperature']
            T2 = self.nodes[outlet_node]['temperature']
            
            self.pipe_constants[pipe_id] = self._c_pipe(
                T1, T2, pipe_data['length'], pipe_data['diameter'],
                pipe_data['roughness'], pipe_data['efficiency']
            )
    
    def _c_pipe(self, T1, T2, L, D, f, eta):
        """Calculate pipe constant for flow calculations."""
        return eta * D**2.5 / (f * L * self.rho * (T1 + T2) / 2)**0.5
    
    def _height_effect(self, h1, h2, p1, p2, T1, T2):
        """Calculate height effect correction."""
        g = 9.81
        R = 287
        return g * self.rho * (h2 - h1) * (T1 + T2) / (2 * R)
    
    def _flow_direction(self, p1, p2, height_effect):
        """Determine flow direction based on pressure difference."""
        return 1 if (p1**2 - p2**2 - height_effect) > 0 else -1
    
    def _compressor_power(self, mass_flow_rate, T_inlet, p_inlet, p_outlet):
        """Calculate compressor power consumption in MW."""
        if mass_flow_rate <= 0:
            return 0.0
        
        cp = 2.1  # kJ/kg·K for natural gas
        gamma = 1.3  # specific heat ratio
        
        compression_ratio = p_outlet / p_inlet
        
        power_kw = (cp * T_inlet * mass_flow_rate * 
                    (compression_ratio**((gamma-1)/gamma) - 1) / 0.85)
        
        return power_kw / 1000  # Convert to MW
    
    def get_reference_node(self):
        """Find the reference node (usually the first one with reference type)."""
        for node_id, node_data in self.nodes.items():
            if node_data.get('node_type') == 'reference':
                return node_id
        # If no reference type found, use node with highest pressure
        return max(self.nodes.keys(), key=lambda k: self.nodes[k]['pressure'])
    
    def solve_network(self, P2_power_mw=-300, use_gas_turbine_compressor=False, max_iter=100, tolerance=1e-6):
        """
        Solve the gas network using Newton-Raphson method.
        
        Parameters:
        P2_power_mw (float): Power demand in MW (negative for consumption)
        use_gas_turbine_compressor (bool): Whether to use gas turbine for compressor drive
        max_iter (int): Maximum number of iterations
        tolerance (float): Convergence tolerance
        
        Returns:
        dict: Dictionary containing solution results
        """
        
        # Get reference pressure
        ref_node = self.get_reference_node()
        p_ref = self.nodes[ref_node]['pressure'] / 1e5 * bar  # Convert Pa to bar
        
        # Initialize pressure estimates (excluding reference node)
        pressure_nodes = [node_id for node_id in self.nodes.keys() if node_id != ref_node]
        n_vars = len(pressure_nodes)
        
        # Initial pressure guess
        p = np.array([0.9 * p_ref * (1 - 0.1 * i) for i in range(n_vars)])
        
        # Convert power demand to gas demand
        D_power = abs(P2_power_mw) / (self.heating_value * self.gas_turbine_efficiency)
        
        n_iter = 0
        err = 1
        
        while err > tolerance and n_iter < max_iter:
            
            # Create pressure dictionary
            pressures = {ref_node: p_ref}
            for i, node_id in enumerate(pressure_nodes):
                pressures[node_id] = p[i]
            
            # Add compressor pressure relationships
            for comp_id, comp_data in self.compressors.items():
                inlet_node = comp_data['inlet']
                outlet_node = comp_data['outlet']
                compression_ratio = comp_data['compression_ratio']
                
                if inlet_node in pressures:
                    pressures[outlet_node] = pressures[inlet_node] * compression_ratio
                elif outlet_node in pressures:
                    pressures[inlet_node] = pressures[outlet_node] / compression_ratio
            
            # Calculate flows for all pipelines
            flows = {}
            height_effects = {}
            
            for pipe_id, pipe_data in self.pipelines.items():
                inlet_node = pipe_data['inlet']
                outlet_node = pipe_data['outlet']
                
                # Height effect
                h1 = self.nodes[inlet_node]['altitude']
                h2 = self.nodes[outlet_node]['altitude']
                T1 = self.nodes[inlet_node]['temperature']
                T2 = self.nodes[outlet_node]['temperature']
                
                p1 = pressures[inlet_node]
                p2 = pressures[outlet_node]
                
                height_effects[pipe_id] = self._height_effect(h1, h2, p1, p2, T1, T2)
                
                # Flow calculation
                flows[pipe_id] = (self._flow_direction(p1, p2, height_effects[pipe_id]) * 
                                 self.pipe_constants[pipe_id] * 
                                 abs(p1**2 - p2**2 - height_effects[pipe_id])**0.5)
            
            # Calculate compressor flows
            compressor_flows = {}
            gas_consumption = {}
            
            for comp_id, comp_data in self.compressors.items():
                inlet_node = comp_data['inlet']
                outlet_node = comp_data['outlet']
                
                # Find connected pipelines
                outflow = sum(flows[pid] for pid, pdata in self.pipelines.items() 
                             if pdata['inlet'] == outlet_node)
                node_demand = self.nodes[outlet_node]['demand']
                
                compressor_flows[comp_id] = outflow + node_demand
                
                # Gas consumption for gas turbine compressor
                if use_gas_turbine_compressor:
                    mass_flow = compressor_flows[comp_id] * self.rho
                    T_inlet = self.nodes[inlet_node]['temperature']
                    p_inlet = pressures[inlet_node]
                    p_outlet = pressures[outlet_node]
                    
                    power_mw = self._compressor_power(mass_flow, T_inlet, p_inlet, p_outlet)
                    gas_consumption[comp_id] = power_mw / (self.heating_value * self.gas_turbine_efficiency)
                else:
                    gas_consumption[comp_id] = 0.0
            
            # Set up mass balance equations
            equations = []
            targets = []
            
            for i, node_id in enumerate(pressure_nodes):
                # Sum all flows into and out of this node
                flow_balance = 0.0
                node_demand = self.nodes[node_id]['demand']
                
                # Pipeline flows
                for pipe_id, pipe_data in self.pipelines.items():
                    if pipe_data['outlet'] == node_id:
                        flow_balance += flows[pipe_id]
                    elif pipe_data['inlet'] == node_id:
                        flow_balance -= flows[pipe_id]
                
                # Compressor flows
                for comp_id, comp_data in self.compressors.items():
                    if comp_data['outlet'] == node_id:
                        flow_balance += compressor_flows[comp_id]
                    elif comp_data['inlet'] == node_id:
                        flow_balance -= compressor_flows[comp_id]
                        flow_balance -= gas_consumption[comp_id]  # Gas consumption
                
                equations.append(flow_balance)
                
                # Target depends on node type
                if node_id == 2:  # Assuming node 2 has power demand
                    targets.append(node_demand)
                elif node_id == 4:  # Assuming node 4 has gas turbine
                    targets.append(D_power)
                else:
                    targets.append(node_demand)
            
            # Calculate residuals
            f_calculated = np.array(equations)
            f_target = np.array(targets)
            delta_f = f_target - f_calculated
            err = max(abs(delta_f))
            
            if err < tolerance:
                break
            
            # Simple Jacobian approximation (could be improved)
            J = np.eye(n_vars) * -1000  # Diagonal approximation
            
            # Update pressures
            try:
                dp = np.linalg.solve(J, delta_f)
                p += dp * 0.1  # Damping factor for stability
            except np.linalg.LinAlgError:
                print(f"Singular matrix at iteration {n_iter}")
                break
            
            n_iter += 1
        
        # Final results
        final_pressures = {ref_node: p_ref}
        for i, node_id in enumerate(pressure_nodes):
            final_pressures[node_id] = p[i]
        
        # Add compressor pressures
        for comp_id, comp_data in self.compressors.items():
            inlet_node = comp_data['inlet']
            outlet_node = comp_data['outlet']
            compression_ratio = comp_data['compression_ratio']
            
            if inlet_node in final_pressures:
                final_pressures[outlet_node] = final_pressures[inlet_node] * compression_ratio
        
        # Final flow calculations
        final_flows = {}
        for pipe_id, pipe_data in self.pipelines.items():
            inlet_node = pipe_data['inlet']
            outlet_node = pipe_data['outlet']
            
            p1 = final_pressures[inlet_node]
            p2 = final_pressures[outlet_node]
            
            h1 = self.nodes[inlet_node]['altitude']
            h2 = self.nodes[outlet_node]['altitude']
            T1 = self.nodes[inlet_node]['temperature']
            T2 = self.nodes[outlet_node]['temperature']
            
            height_eff = self._height_effect(h1, h2, p1, p2, T1, T2)
            
            final_flows[f'Pipe {inlet_node}-{outlet_node}'] = (
                self._flow_direction(p1, p2, height_eff) * self.pipe_constants[pipe_id] * 
                abs(p1**2 - p2**2 - height_eff)**0.5
            )
        
        # Final compressor calculations
        final_compressor_data = {}
        for comp_id, comp_data in self.compressors.items():
            inlet_node = comp_data['inlet']
            outlet_node = comp_data['outlet']
            
            outflow = sum(final_flows[f'Pipe {outlet_node}-{pdata["outlet"]}'] 
                         for pid, pdata in self.pipelines.items() 
                         if pdata['inlet'] == outlet_node and f'Pipe {outlet_node}-{pdata["outlet"]}' in final_flows)
            
            comp_flow = outflow + self.nodes[outlet_node]['demand']
            final_flows[f'Compressor {inlet_node}-{outlet_node}'] = comp_flow
            
            # Power calculation
            mass_flow = comp_flow * self.rho
            T_inlet = self.nodes[inlet_node]['temperature']
            p_inlet = final_pressures[inlet_node]
            p_outlet = final_pressures[outlet_node]
            
            power_mw = self._compressor_power(mass_flow, T_inlet, p_inlet, p_outlet)
            gas_cons = power_mw / (self.heating_value * self.gas_turbine_efficiency) if use_gas_turbine_compressor else 0.0
            
            final_compressor_data[comp_id] = {
                'power_mw': power_mw,
                'gas_consumption': gas_cons
            }
        
        return {
            'pressures': {f'p{k}': v/bar for k, v in final_pressures.items()},
            'flows': final_flows,
            'compressors': final_compressor_data,
            'convergence': {
                'iterations': n_iter,
                'error': err
            },
            'network_data': {
                'nodes': self.nodes,
                'pipelines': self.pipelines,
                'compressors': self.compressors
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
    
    print("\nCOMPRESSORS:")
    for comp_id, comp_data in results['compressors'].items():
        print(f"  Compressor {comp_id}:")
        print(f"    Power consumption: {comp_data['power_mw']:.2f} MW")
        print(f"    Gas consumption: {comp_data['gas_consumption']:.3f} sm³/s")
    
    print("\nCONVERGENCE:")
    print(f"  Iterations: {results['convergence']['iterations']}")
    print(f"  Final error: {results['convergence']['error']:.2e}")
    
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gas Network Simulation from CSV files')
    parser.add_argument('csv_folder', help='Path to folder containing CSV files')
    parser.add_argument('--nodes-file', help='Custom nodes CSV filename')
    parser.add_argument('--pipelines-file', help='Custom pipelines CSV filename')
    parser.add_argument('--compressors-file', help='Custom compressors CSV filename')
    parser.add_argument('--power-demand', type=float, default=-300, 
                       help='Power demand in MW (default: -300)')
    parser.add_argument('--gas-turbine', action='store_true',
                       help='Use gas turbine for compressor drive')
    
    args = parser.parse_args()
    
    try:
        # Initialize simulator
        simulator = GasNetworkSimulator(
            args.csv_folder,
            args.nodes_file,
            args.pipelines_file, 
            args.compressors_file
        )
        
        # Run simulation
        results = simulator.solve_network(
            P2_power_mw=args.power_demand,
            use_gas_turbine_compressor=args.gas_turbine
        )
        
        print_results(results)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()