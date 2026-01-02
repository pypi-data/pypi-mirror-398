#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.constants import bar
import argparse
import warnings
warnings.filterwarnings('ignore')

def read_wascal_network(folder_path):
    """Read WASCAL CSV files and return network data."""
    folder = Path(folder_path)
    
    # Find CSV files automatically
    nodes_file = list(folder.glob("*nodes*.csv"))[0]
    pipelines_file = list(folder.glob("*pipelines*.csv"))[0]
    
    # Look for compressors file - it might have "compressors" in the name
    compressor_patterns = ["*compressors*.csv", "*compressor*.csv"]
    compressors_file = None
    for pattern in compressor_patterns:
        compressors_files = list(folder.glob(pattern))
        if compressors_files:
            # Make sure we don't pick the pipelines file by mistake
            for cf in compressors_files:
                if "pipeline" not in cf.name.lower():
                    compressors_file = cf
                    break
            if compressors_file:
                break
    
    print(f"Reading nodes from: {nodes_file.name}")
    print(f"Reading pipelines from: {pipelines_file.name}")
    if compressors_file:
        print(f"Reading compressors from: {compressors_file.name}")
    else:
        print("No compressors file found")
    
    nodes = pd.read_csv(nodes_file, sep=';')
    pipelines = pd.read_csv(pipelines_file, sep=';')
    compressors = pd.read_csv(compressors_file, sep=';') if compressors_file else pd.DataFrame()
    
    return nodes, pipelines, compressors

def analyze_wascal_network(folder_path):
    """
    Analyze the WASCAL network structure and extract key information.
    """
    
    # Read CSV data
    nodes_df, pipelines_df, compressors_df = read_wascal_network(folder_path)
    
    print("\n" + "="*60)
    print("WASCAL NETWORK ANALYSIS")
    print("="*60)
    
    # Clean the data (remove NaN rows)
    nodes_clean = nodes_df.dropna(subset=['node_index']).copy()
    pipelines_clean = pipelines_df.dropna(subset=['pipeline_index']).copy()
    compressors_clean = compressors_df.dropna(subset=['compressor_index']).copy() if 'compressor_index' in compressors_df.columns else pd.DataFrame()
    
    print(f"\nNetwork Scale:")
    print(f"  Nodes: {len(nodes_clean)}")
    print(f"  Pipelines: {len(pipelines_clean)}")
    print(f"  Compressors: {len(compressors_clean)}")
    
    # Analyze nodes
    print(f"\nNode Types:")
    node_types = nodes_clean['node_type'].value_counts()
    for node_type, count in node_types.items():
        print(f"  {node_type}: {count}")
    
    # Find reference nodes (with pressure data)
    reference_nodes = nodes_clean[nodes_clean['pressure_pa'].notna()]
    print(f"\nReference Nodes (with pressure):")
    for _, row in reference_nodes.iterrows():
        node_idx = int(row['node_index'])
        pressure_bar = row['pressure_pa'] / 1e5
        print(f"  Node {node_idx}: {pressure_bar:.1f} bar")
    
    # Analyze demand nodes
    demand_nodes = nodes_clean[nodes_clean['flow_sm3_per_s'].notna() & (nodes_clean['flow_sm3_per_s'] != 1.0)]
    print(f"\nDemand Nodes (with significant flow):")
    for _, row in demand_nodes.iterrows():
        node_idx = int(row['node_index'])
        flow = row['flow_sm3_per_s']
        if abs(flow) > 10:  # Only show significant flows
            print(f"  Node {node_idx}: {flow:.1f} sm³/s")
    
    # Analyze pipeline diameters and lengths
    print(f"\nPipeline Statistics:")
    print(f"  Average diameter: {pipelines_clean['diameter_m'].mean():.2f} m")
    print(f"  Average length: {pipelines_clean['length_m'].mean()/1000:.1f} km")
    print(f"  Total network length: {pipelines_clean['length_m'].sum()/1000:.1f} km")
    
    # Analyze compressors
    if len(compressors_clean) > 0:
        print(f"\nCompressor Configuration:")
        print(f"  Average compression ratio: {compressors_clean['compression_ratio'].mean():.3f}")
        print(f"  Average efficiency: {compressors_clean['efficiency'].mean():.2f}")
    else:
        print(f"\nNo compressors found in dataset")
    
    print("="*60)
    
    return {
        'nodes': nodes_clean,
        'pipelines': pipelines_clean,
        'compressors': compressors_clean,
        'reference_nodes': reference_nodes,
        'demand_nodes': demand_nodes
    }

class WascalGasNetworkSimulator:
    """WASCAL Gas network simulator using Newton-Raphson method."""
    
    def __init__(self, folder_path):
        """Initialize simulator with WASCAL CSV data."""
        self.rho = 0.717  # kg/sm3 for hydrogen (from WASCAL data)
        self.heating_value = 120  # MJ/kg for hydrogen
        self.gas_turbine_efficiency = 0.35
        
        # Read and parse CSV data
        self.nodes_df, self.pipelines_df, self.compressors_df = read_wascal_network(folder_path)
        
        # Clean data
        self.nodes_clean = self.nodes_df.dropna(subset=['node_index']).copy()
        self.pipelines_clean = self.pipelines_df.dropna(subset=['pipeline_index']).copy()
        self.compressors_clean = self.compressors_df.dropna(subset=['compressor_index']).copy() if 'compressor_index' in self.compressors_df.columns else pd.DataFrame()
        
        # Convert to dictionaries for easier access
        self.nodes = {}
        for _, row in self.nodes_clean.iterrows():
            # Handle missing values with defaults
            pressure = row.get('pressure_pa', np.nan)
            
            # Temperature handling - check for NaN or empty values
            temp_val = row.get('temperature_k', 288.15)
            if pd.isna(temp_val) or temp_val == '' or temp_val is None:
                temperature = 288.15  # Default 15°C = 288.15K
            else:
                temperature = float(temp_val)
                
            # Altitude handling
            alt_val = row.get('altitude_m', 0.0)
            if pd.isna(alt_val) or alt_val == '':
                altitude = 0.0
            else:
                altitude = float(alt_val) if alt_val != '' else 0.0
                
            flow = row.get('flow_sm3_per_s', 0.0)
            node_type = row.get('node_type', 'junction')
            
            # Convert flow to demand (negative for withdrawal/consumption)
            # In WASCAL data, positive flows are actually demands, so we make them negative
            if pd.notna(flow) and flow != 1.0 and flow > 0:  # 1.0 is placeholder
                demand = -abs(flow)  # Make demand negative (withdrawal)
            else:
                demand = 0.0
            
            self.nodes[int(row['node_index'])] = {
                'pressure': pressure,
                'temperature': temperature,
                'altitude': altitude,
                'demand': demand,  # Negative for withdrawal
                'node_type': node_type,
                'original_flow': flow  # Keep original for reference
            }
        
        self.pipelines = {}
        for _, row in self.pipelines_clean.iterrows():
            # Set default values for missing columns
            roughness = 0.01  # Default roughness for steel pipes (mm)
            efficiency = 0.95  # Default pipeline efficiency
            
            self.pipelines[int(row['pipeline_index'])] = {
                'inlet': int(row['inlet_index']),
                'outlet': int(row['outlet_index']),
                'diameter': row['diameter_m'],
                'length': row['length_m'],
                'roughness': roughness,  # Use default
                'efficiency': efficiency,  # Use default
                'friction_method': row.get('friction_method', 'chen')
            }
        
        self.compressors = {}
        for _, row in self.compressors_clean.iterrows():
            self.compressors[int(row['compressor_index'])] = {
                'inlet': int(row['inlet']),
                'outlet': int(row['outlet']),
                'compression_ratio': row['compression_ratio'],
                'efficiency': row['efficiency'],
                'process': row['thermodynamic_process']
            }
        
        print(f"Loaded WASCAL network: {len(self.nodes)} nodes, {len(self.pipelines)} pipelines, {len(self.compressors)} compressors")

        # Apply preprocessing: group-based scaling and pipeline modifications
        self._preprocess_network()
        
        # Calculate total demand and add supply at reference nodes
        total_demand = sum(node['demand'] for node in self.nodes.values())
        print(f"Total network demand: {abs(total_demand):.1f} sm³/s")
        
        # Balance network by adding supply at reference nodes
        if total_demand < 0:  # There is net demand
            ref_nodes = self.get_reference_nodes()
            if ref_nodes:
                supply_per_ref = abs(total_demand) / len(ref_nodes)
                for ref_node in ref_nodes:
                    self.nodes[ref_node]['demand'] = supply_per_ref  # Positive = supply
                print(f"Added {supply_per_ref:.1f} sm³/s supply to each reference node")
        
        # Pre-calculate pipe constants
        self._calculate_pipe_constants()

        # Precompute validation results for quick access
        self.validation = self._validate_network()

    def _validate_network(self):
        """Validate connectivity and data sanity. Returns a dict summary."""
        missing_nodes = set()
        bad_pipes = []
        for pid, p in self.pipelines.items():
            if p['inlet'] not in self.nodes or p['outlet'] not in self.nodes:
                bad_pipes.append(pid)
                if p['inlet'] not in self.nodes:
                    missing_nodes.add(p['inlet'])
                if p['outlet'] not in self.nodes:
                    missing_nodes.add(p['outlet'])

        bad_compressors = []
        for cid, c in self.compressors.items():
            if c['inlet'] not in self.nodes or c['outlet'] not in self.nodes:
                bad_compressors.append(cid)
                if c['inlet'] not in self.nodes:
                    missing_nodes.add(c['inlet'])
                if c['outlet'] not in self.nodes:
                    missing_nodes.add(c['outlet'])

        ref_nodes = self.get_reference_nodes()

        return {
            'missing_nodes': sorted(missing_nodes),
            'bad_pipelines': sorted(bad_pipes),
            'bad_compressors': sorted(bad_compressors),
            'reference_nodes': ref_nodes,
            'nodes_count': len(self.nodes),
            'pipelines_count': len(self.pipelines),
            'compressors_count': len(self.compressors),
        }
    
    def _preprocess_network(self):
        """Apply group-based scaling and pipeline modifications before simulation."""
        print("\nApplying network preprocessing...")
        
        # Define groups
        exclude_node = 32
        group_a = {34, 35, 37, 39, 41, 70, 71, 72}
        
        # Calculate initial production for each group
        total_prod_A_sm3_s = 0
        total_prod_B_sm3_s = 0
        
        for idx, node_data in self.nodes.items():
            if node_data['original_flow'] != 1.0 and idx != exclude_node:  # Skip placeholders and excluded node
                original_flow = node_data['original_flow']
                if pd.notna(original_flow) and original_flow > 0:
                    if idx in group_a:
                        total_prod_A_sm3_s += original_flow
                    else:
                        total_prod_B_sm3_s += original_flow
        
        print(f"Initial production Group A (Sm3/s): {total_prod_A_sm3_s:.1f}")
        print(f"Initial production Group B (Sm3/s): {total_prod_B_sm3_s:.1f}")
        
        # Convert Sm³/s → bcm/year for scaling factor computation
        sm3s_to_bcm_y = lambda flow: flow * 60 * 60 * 24 * 365 / 1e9
        
        target_total_production = 30  # bcm/year for each group
        
        scaling_factor_A = (sm3s_to_bcm_y(total_prod_A_sm3_s) / target_total_production 
                           if total_prod_A_sm3_s != 0 else 1)
        scaling_factor_B = (sm3s_to_bcm_y(total_prod_B_sm3_s) / target_total_production 
                           if total_prod_B_sm3_s != 0 else 1)
        
        print(f"Scaling factor Group A: {scaling_factor_A:.3f}")
        print(f"Scaling factor Group B: {scaling_factor_B:.3f}")
        
        # Modify pipeline properties
        for pipe_id, pipe_data in self.pipelines.items():
            pipe_data['diameter'] = 1.23  # Set diameter to 1.23 m
            pipe_data['efficiency'] = 1.0  # Set efficiency to 1.0
        
        print("Pipeline properties updated: diameter = 1.23 m, efficiency = 1.0")
        
        # Apply scaling to node demands
        for idx, node_data in self.nodes.items():
            if node_data['original_flow'] != 1.0 and idx != exclude_node:
                original_flow = node_data['original_flow']
                if pd.notna(original_flow) and original_flow > 0:
                    if idx in group_a:
                        # Apply scaling for group A
                        new_demand = -original_flow / scaling_factor_A
                        node_data['demand'] = new_demand
                    else:
                        # Apply scaling for group B
                        new_demand = -original_flow / scaling_factor_B
                        node_data['demand'] = new_demand
        
        # Calculate final production after scaling
        total_prod_A_final = 0
        total_prod_B_final = 0
        
        for idx, node_data in self.nodes.items():
            demand = node_data['demand']
            if demand < 0 and idx != exclude_node:  # Negative demand means production
                if idx in group_a:
                    total_prod_A_final += demand
                else:
                    total_prod_B_final += demand
        
        cumulative_production = total_prod_A_final + total_prod_B_final
        
        print(f"Final production Group A (Sm3/s): {total_prod_A_final:.1f}")
        print(f"Final production Group B (Sm3/s): {total_prod_B_final:.1f}")
        print(f"Cumulative production (Sm3/s): {cumulative_production:.1f}")
        print("Network preprocessing completed.\n")
    
    def _calculate_pipe_constants(self):
        """Pre-calculate pipe constants for flow calculations."""
        self.pipe_constants = {}
        
        for pipe_id, pipe_data in self.pipelines.items():
            inlet_node = pipe_data['inlet']
            outlet_node = pipe_data['outlet']
            T1 = self.nodes[inlet_node]['temperature']
            T2 = self.nodes[outlet_node]['temperature']
            
            # Debug the inputs
            if pipe_id <= 3:  # Debug first few pipes
                print(f"  Pipe {pipe_id}: T1={T1}, T2={T2}, L={pipe_data['length']}, D={pipe_data['diameter']}")
                print(f"    roughness={pipe_data['roughness']}, efficiency={pipe_data['efficiency']}")
            
            c_pipe = self._c_pipe(
                T1, T2, pipe_data['length'], pipe_data['diameter'],
                pipe_data['roughness'], pipe_data['efficiency']
            )
            
            if not np.isfinite(c_pipe):
                print(f"  Warning: Invalid pipe constant for pipe {pipe_id}: {c_pipe}")
                
            self.pipe_constants[pipe_id] = c_pipe
    
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
        
        cp = 14.3  # kJ/kg·K for hydrogen
        gamma = 1.4  # specific heat ratio for hydrogen
        
        compression_ratio = p_outlet / p_inlet
        
        power_kw = (cp * T_inlet * mass_flow_rate * 
                    (compression_ratio**((gamma-1)/gamma) - 1) / 0.85)
        
        return power_kw / 1000  # Convert to MW
    
    def get_reference_nodes(self):
        """Find reference nodes with specified pressures."""
        ref_nodes = []
        for node_id, node_data in self.nodes.items():
            node_type = node_data.get('node_type')
            p = node_data.get('pressure')
            # Prefer explicit "reference" tags; fall back to any node with pressure set
            if (node_type == 'reference' and pd.notna(p)) or (node_type is None and pd.notna(p)):
                ref_nodes.append(node_id)
        return ref_nodes
    
    def solve_network(self, max_iter=200, tolerance=1e-2, debug=False, debug_every=1, debug_top=5):
        """
        Solve the WASCAL gas network using Newton-Raphson method.
        """
        print("\n" + "="*60)
        print("WASCAL GAS NETWORK HYDRAULIC SIMULATION")
        print("="*60)
        
        # Get reference nodes and their pressures
        ref_nodes = self.get_reference_nodes()
        if not ref_nodes:
            print("Error: No reference nodes found!")
            return None
        
        print(f"Reference nodes: {ref_nodes}")
        if debug:
            print(f"Validation: missing_nodes={self.validation['missing_nodes']}, bad_pipelines={self.validation['bad_pipelines']}, bad_compressors={self.validation['bad_compressors']}")
        
        # Create list of unknown pressure nodes (excluding reference nodes)
        unknown_nodes = [node_id for node_id in self.nodes.keys() if node_id not in ref_nodes]
        n_vars = len(unknown_nodes)
        
        print(f"Solving for {n_vars} unknown pressures")
        
        if n_vars == 0:
            print("All nodes have reference pressures - no solving needed.")
            ref_pressures = {node_id: self.nodes[node_id]['pressure'] for node_id in ref_nodes}
            return self._build_results(ref_nodes, ref_pressures, 0, 0, True)
        
        # Initial pressure guess - start with average of reference pressures
        avg_ref_pressure = np.mean([self.nodes[node_id]['pressure'] for node_id in ref_nodes])
        print(f"Average reference pressure: {avg_ref_pressure/1e5:.2f} bar")
        
        # Better initial guess - slight pressure drop from reference nodes
        p = np.full(n_vars, avg_ref_pressure * 0.98)  # 2% lower than reference
        
        n_iter = 0
        err = 1
        max_pressure_change = 0
        
        print(f"Starting Newton-Raphson iteration...")
        
        # Debug: Check pipe constants
        pipe_const_values = list(self.pipe_constants.values())
        print(f"Pipe constants: min={min(pipe_const_values):.2e}, max={max(pipe_const_values):.2e}")
        if any(not np.isfinite(c) or c <= 0 for c in pipe_const_values):
            print("Warning: Invalid pipe constants detected!")

        # Debug storage
        debug_info = {'residual_history': [], 'max_pressure_change_history': [], 'iteration_samples': []}
        
        while err > tolerance and n_iter < max_iter:
            # Create pressure dictionary
            pressures = {}
            
            # Set reference pressures
            for node_id in ref_nodes:
                pressures[node_id] = self.nodes[node_id]['pressure']
            
            # Set unknown pressures
            for i, node_id in enumerate(unknown_nodes):
                pressures[node_id] = p[i]
            
            # Handle compressor pressure relationships
            for comp_id, comp_data in self.compressors.items():
                inlet_node = comp_data['inlet']
                outlet_node = comp_data['outlet']
                compression_ratio = comp_data['compression_ratio']
                
                if inlet_node in pressures and outlet_node not in ref_nodes:
                    pressures[outlet_node] = pressures[inlet_node] * compression_ratio
                elif outlet_node in pressures and inlet_node not in ref_nodes:
                    pressures[inlet_node] = pressures[outlet_node] / compression_ratio
            
            # Calculate flows and mass balance residuals
            equations = []
            
            for i, node_id in enumerate(unknown_nodes):
                if node_id in pressures:  # Skip if pressure controlled by compressor
                    flow_balance = 0.0
                    node_demand = self.nodes[node_id].get('demand', 0)
                    if pd.notna(node_demand) and node_demand != 1.0:  # 1.0 is placeholder
                        node_demand = node_demand
                    else:
                        node_demand = 0.0
                    
                    # Calculate pipeline flows into/out of this node
                    for pipe_id, pipe_data in self.pipelines.items():
                        inlet_node = pipe_data['inlet']
                        outlet_node = pipe_data['outlet']
                        
                        if inlet_node in pressures and outlet_node in pressures:
                            p1 = pressures[inlet_node]
                            p2 = pressures[outlet_node]
                            
                            # Height effect
                            h1 = self.nodes[inlet_node]['altitude']
                            h2 = self.nodes[outlet_node]['altitude']
                            T1 = self.nodes[inlet_node]['temperature']
                            T2 = self.nodes[outlet_node]['temperature']
                            
                            height_eff = self._height_effect(h1, h2, p1, p2, T1, T2)
                            
                            # Flow calculation with numerical safety
                            pressure_diff = p1**2 - p2**2 - height_eff
                            if abs(pressure_diff) < 1e-10:
                                flow = 0.0  # Avoid sqrt of very small numbers
                            else:
                                flow = (self._flow_direction(p1, p2, height_eff) * 
                                       self.pipe_constants[pipe_id] * 
                                       abs(pressure_diff)**0.5)
                            
                            # Add to balance based on flow direction
                            if outlet_node == node_id:
                                flow_balance += flow
                            elif inlet_node == node_id:
                                flow_balance -= flow
                    
                    # Mass balance equation: inflow - outflow + demand = 0
                    # Note: in this script we store consumption as negative demand
                    # (withdrawal < 0) and supply as positive. Therefore the
                    # residual must add the signed demand.
                    residual = flow_balance + node_demand
                    equations.append(residual)
                else:
                    equations.append(0.0)  # Controlled by compressor
            
            # Calculate error with debugging
            equations_array = np.array(equations)
            print(f"  Iteration {n_iter}: {len(equations_array)} equations")

            if len(equations_array) > 0:
                finite_mask = np.isfinite(equations_array)
                if np.all(finite_mask):
                    err = np.max(np.abs(equations_array))
                    print(f"  Max residual: {err:.2e}")
                    if debug and (n_iter % debug_every == 0):
                        # Track top residual nodes
                        abs_res = np.abs(equations_array)
                        idx_sorted = np.argsort(-abs_res)
                        sample = []
                        for k in idx_sorted[:min(debug_top, len(idx_sorted))]:
                            nid = unknown_nodes[k]
                            sample.append((int(nid), float(equations_array[k])))
                        debug_info['residual_history'].append(float(err))
                        debug_info['iteration_samples'].append({'iter': int(n_iter), 'top_residuals': sample})
                else:
                    non_finite_count = np.sum(~finite_mask)
                    print(f"  Warning: {non_finite_count} non-finite equations at iteration {n_iter}")
                    print(f"  Equations sample: {equations_array[:5]}")
                    err = np.inf
                    break
            else:
                print("  Warning: No equations generated")
                err = np.inf
                break
            
            if err < tolerance:
                print(f"  Converged at iteration {n_iter}, error = {err:.2e}")
                break
            
            # Gauss-Seidel successive substitution - much more robust for large networks
            if len(equations) == n_vars:
                # Update pressures node by node using Gauss-Seidel
                max_pressure_change = 0
                
                for i, node_id in enumerate(unknown_nodes):
                    old_pressure = p[i]
                    
                    # Calculate required pressure to balance flows at this node
                    node_demand = self.nodes[node_id].get('demand', 0)
                    total_inflow = 0
                    total_conductance = 0  # Sum of pipeline conductances
                    
                    # Examine all pipelines connected to this node
                    for pipe_id, pipe_data in self.pipelines.items():
                        inlet_node = pipe_data['inlet']
                        outlet_node = pipe_data['outlet']
                        
                        if inlet_node == node_id or outlet_node == node_id:
                            # This pipeline is connected to our node
                            other_node = outlet_node if inlet_node == node_id else inlet_node
                            
                            if other_node in pressures:
                                other_pressure = pressures[other_node]
                                k = self.pipe_constants[pipe_id]
                                
                                # Linearized conductance approximation
                                if other_pressure > 1000:  # Avoid division by very small pressures
                                    conductance = k / (2 * (other_pressure/1e5)**0.5)  # Linearized around other node
                                    total_conductance += conductance
                                    
                                    # Expected flow contribution
                                    if inlet_node == node_id:
                                        # Flow out of this node
                                        total_inflow -= conductance * other_pressure
                                    else:
                                        # Flow into this node
                                        total_inflow += conductance * other_pressure
                    
                    # Update pressure to satisfy mass balance
                    if total_conductance > 1e-10:
                        # Linearized nodal balance: C * p + (total_inflow + demand) ≈ 0
                        # Solve for p to drive residual toward zero.
                        target_pressure = - (total_inflow + node_demand) / total_conductance
                        
                        # Adaptive relaxation factor for better convergence
                        if n_iter < 10:
                            relaxation = 0.5  # Aggressive early
                        elif n_iter < 50:
                            relaxation = 0.2  # Moderate 
                        elif err > 5000:
                            relaxation = 0.1  # Conservative for high residuals
                        else:
                            relaxation = 0.05  # Very conservative near convergence
                        
                        new_pressure = old_pressure + relaxation * (target_pressure - old_pressure)
                        
                        # Keep pressures reasonable
                        new_pressure = max(avg_ref_pressure * 0.3, min(avg_ref_pressure * 1.2, new_pressure))
                        
                        # Update pressure array and pressure dictionary
                        p[i] = new_pressure
                        pressures[node_id] = new_pressure
                        
                        pressure_change = abs(new_pressure - old_pressure)
                        max_pressure_change = max(max_pressure_change, pressure_change)
                
                # Check convergence based on both mass balance residual AND pressure changes
                if n_iter > 0 and err < tolerance:  # Primary: mass balance must be satisfied
                    print(f"  Converged based on mass balance residual: {err:.2e}")
                    break
                elif n_iter > 0 and max_pressure_change < 100 and err < 1000:  # Secondary: small changes + reasonable residual
                    print(f"  Converged based on pressure stability: max Δp = {max_pressure_change:.1f} Pa, residual = {err:.1e}")
                    break
            
            n_iter += 1
            
            if debug:
                debug_info['max_pressure_change_history'].append(float(max_pressure_change))
            if n_iter % 10 == 0:
                print(f"  Iteration {n_iter}, error = {err:.2e}")
        
        # Build final results
        final_pressures = {}
        for node_id in ref_nodes:
            final_pressures[node_id] = self.nodes[node_id]['pressure']
        
        for i, node_id in enumerate(unknown_nodes):
            final_pressures[node_id] = p[i]
        
        # Handle compressor pressures
        for comp_id, comp_data in self.compressors.items():
            inlet_node = comp_data['inlet']
            outlet_node = comp_data['outlet']
            compression_ratio = comp_data['compression_ratio']
            
            if inlet_node in final_pressures:
                final_pressures[outlet_node] = final_pressures[inlet_node] * compression_ratio
        
        # Check if we converged based on proper criteria
        converged = (err < tolerance) or (max_pressure_change < 100 and err < 1000) if n_iter > 0 else False
        return self._build_results(ref_nodes, final_pressures, n_iter, err, converged, debug_info if debug else None)
    
    def _build_results(self, ref_nodes, final_pressures, n_iter=0, err=0, converged=False, debug_info=None):
        """Build results dictionary."""
        
        # Calculate final flows
        final_flows = {}
        total_flow = 0
        
        for pipe_id, pipe_data in self.pipelines.items():
            inlet_node = pipe_data['inlet']
            outlet_node = pipe_data['outlet']
            
            if inlet_node in final_pressures and outlet_node in final_pressures:
                p1 = final_pressures[inlet_node]
                p2 = final_pressures[outlet_node]
                
                h1 = self.nodes[inlet_node]['altitude']
                h2 = self.nodes[outlet_node]['altitude']
                T1 = self.nodes[inlet_node]['temperature']
                T2 = self.nodes[outlet_node]['temperature']
                
                height_eff = self._height_effect(h1, h2, p1, p2, T1, T2)
                
                flow = (self._flow_direction(p1, p2, height_eff) * 
                       self.pipe_constants[pipe_id] * 
                       abs(p1**2 - p2**2 - height_eff)**0.5)
                
                final_flows[f'Pipeline {inlet_node}-{outlet_node}'] = flow
                total_flow += abs(flow)
        
        result = {
            'pressures': {f'Node {k}': v/1e5 for k, v in final_pressures.items()},  # Convert to bar
            'flows': final_flows,
            'convergence': {
                'iterations': n_iter,
                'error': err,
                'converged': converged
            },
            'network_stats': {
                'total_nodes': len(self.nodes),
                'total_pipelines': len(self.pipelines),
                'total_compressors': len(self.compressors),
                'reference_nodes': ref_nodes,
                'total_flow_magnitude': total_flow
            }
        }
        if debug_info is not None:
            result['debug'] = debug_info
        return result

def wascal_network_simulation(folder_path, **solve_kwargs):
    """
    Perform full hydraulic simulation of the WASCAL network.
    """
    
    # Initialize simulator
    simulator = WascalGasNetworkSimulator(folder_path)
    
    # Run simulation
    results = simulator.solve_network(**solve_kwargs)
    
    return results

def export_pressure_results(results, output_file='wascal_pressure_results.csv'):
    """Export nodal pressure results to CSV file."""
    if results is None:
        print("No results to export.")
        return
    
    import csv
    pressure_items = list(results['pressures'].items())
    
    # Sort by node number
    def extract_node_number(item):
        node_name, pressure = item
        return int(node_name.split()[-1])
    
    pressure_items_sorted = sorted(pressure_items, key=extract_node_number)
    
    # Write to CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Node_ID', 'Pressure_bar', 'Pressure_Pa'])
        
        for node_name, pressure_bar in pressure_items_sorted:
            node_id = int(node_name.split()[-1])
            pressure_pa = pressure_bar * 1e5
            writer.writerow([node_id, f'{pressure_bar:.3f}', f'{pressure_pa:.1f}'])
    
    print(f"Pressure results exported to: {output_file}")

def print_simulation_results(results):
    """Print hydraulic simulation results in a formatted way."""
    if results is None:
        print("No simulation results to display.")
        return
    
    print(f"\nSIMULATION RESULTS:")
    print("="*60)
    
    # Network statistics
    stats = results['network_stats']
    print(f"Network: {stats['total_nodes']} nodes, {stats['total_pipelines']} pipelines, {stats['total_compressors']} compressors")
    print(f"Reference nodes: {stats['reference_nodes']}")
    
    # Convergence info
    conv = results['convergence']
    if conv['converged']:
        print(f"✓ Converged in {conv['iterations']} iterations (error: {conv['error']:.2e})")
    else:
        print(f"✗ Did not converge after {conv['iterations']} iterations (error: {conv['error']:.2e})")
    
    # All pressure results
    print(f"\nALL NODAL PRESSURES (bar):")
    pressure_items = list(results['pressures'].items())
    
    # Sort by node number for easier reading
    def extract_node_number(item):
        node_name, pressure = item
        return int(node_name.split()[-1])  # Extract number from "Node X"
    
    pressure_items_sorted = sorted(pressure_items, key=extract_node_number)
    
    # Print in columns for better readability
    for i, (node, pressure) in enumerate(pressure_items_sorted):
        if i % 4 == 0:  # New line every 4 nodes
            print()
        print(f"  {node}: {pressure:.2f} bar", end="    ")
    print()  # Final newline
    
    # Highlight reference nodes
    ref_nodes = stats['reference_nodes']
    print(f"\nReference node pressures (supply points):")
    for node_id in ref_nodes:
        node_name = f"Node {node_id}"
        if node_name in results['pressures']:
            print(f"  {node_name}: {results['pressures'][node_name]:.2f} bar")
    
    # Flow statistics
    flows = results['flows']
    if flows:
        flow_values = list(flows.values())
        print(f"\nFLOW STATISTICS:")
        print(f"  Total flow magnitude: {stats['total_flow_magnitude']:.1f} sm³/s")
        print(f"  Number of pipelines: {len(flows)}")
        print(f"  Max flow: {max(abs(f) for f in flow_values):.1f} sm³/s")
        print(f"  Min flow: {min(abs(f) for f in flow_values):.1f} sm³/s")
        print(f"  Average flow: {np.mean([abs(f) for f in flow_values]):.1f} sm³/s")
    
    print("="*60)

def export_network_summary(folder_path, output_file='wascal_network_summary.txt'):
    """Export a concise network summary based on CSV inputs.

    This avoids running the full simulation and provides quick, robust
    metrics derived directly from the input files.
    """
    # Read CSVs
    nodes_df, pipelines_df, compressors_df = read_wascal_network(folder_path)

    # Clean
    nodes = nodes_df.dropna(subset=['node_index']).copy()
    pipelines = pipelines_df.dropna(subset=['pipeline_index']).copy()
    compressors = compressors_df.dropna(subset=['compressor_index']).copy() if 'compressor_index' in compressors_df.columns else pd.DataFrame()

    # Counts
    nodes_count = len(nodes)
    pipelines_count = len(pipelines)
    compressors_count = len(compressors)

    # Safe helpers
    def to_float(x, default=0.0):
        try:
            return float(x)
        except Exception:
            return default

    # Pipeline volume (sum over pi*(D^2/4)*L)
    if pipelines_count:
        diam = pipelines['diameter_m'].astype(float)
        length = pipelines['length_m'].astype(float)
        total_pipeline_volume_m3 = float(np.sum(np.pi * (diam**2) / 4.0 * length))
    else:
        total_pipeline_volume_m3 = 0.0

    # Supply/Demand (CSV convention: 1.0 means placeholder/no-demand)
    total_supply = 0.0
    total_demand = 0.0
    if 'flow_sm3_per_s' in nodes.columns:
        for v in nodes['flow_sm3_per_s']:
            if pd.notna(v) and v != 1.0:
                if v > 0:
                    total_demand += float(v)
                elif v < 0:
                    total_supply += float(-v)

    flow_balance = total_supply - total_demand

    # Pressure range (bar)
    if 'pressure_pa' in nodes.columns and nodes['pressure_pa'].notna().any():
        p_bar = nodes['pressure_pa'].dropna().astype(float) / 1e5
        p_min, p_max = float(p_bar.min()), float(p_bar.max())
    else:
        p_min = p_max = 0.0

    # Very rough compressor power proxy (no flows known here). Report 0.0 safely.
    estimated_compressor_power_mw = 0.0

    summary_text = f"""
WASCAL Gas Network Analysis Summary
{'='*50}

Network Scale:
- Nodes: {nodes_count}
- Pipelines: {pipelines_count}
- Compressors: {compressors_count}

Network Properties:
- Total pipeline volume: {total_pipeline_volume_m3/1e6:.2f} million m³
- Estimated compressor power: {estimated_compressor_power_mw:.1f} MW
- Total supply: {total_supply:.1f} sm³/s
- Total demand: {total_demand:.1f} sm³/s
- Flow balance: {flow_balance:.1f} sm³/s
- Pressure range: {p_min:.1f} - {p_max:.1f} bar

Notes:
- Summary is derived directly from CSV inputs (no hydraulics).
- Use the simulation mode for full hydraulic results.
"""

    output_path = Path(folder_path) / output_file
    with open(output_path, 'w') as f:
        f.write(summary_text)

    print(f"\nNetwork summary exported to: {output_path}")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WASCAL Gas Network Analysis')
    parser.add_argument('csv_folder', nargs='?', default='./wascal', 
                       help='Path to folder with WASCAL CSV files (default: ./wascal)')
    parser.add_argument('--export', action='store_true', 
                       help='Export network summary to text file')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed node and pipeline information')
    parser.add_argument('--debug', action='store_true', help='Enable verbose debug during solve')
    parser.add_argument('--max-iter', type=int, default=200, help='Max iterations for solver')
    parser.add_argument('--tolerance', type=float, default=1e-2, help='Convergence tolerance')
    parser.add_argument('--debug-every', type=int, default=1, help='Record debug snapshot every N iters')
    parser.add_argument('--debug-top', type=int, default=5, help='Top-K residual nodes per snapshot')
    
    args = parser.parse_args()
    
    try:
        print("WASCAL Gas Network Analysis Tool")
        print("This tool provides network analysis for complex gas transmission systems.")
        
        # Check if the folder exists
        folder_path = Path(args.csv_folder)
        if not folder_path.exists():
            print(f"Error: Folder '{args.csv_folder}' not found.")
            print("Available folders:")
            parent_dir = Path('.')
            for item in parent_dir.iterdir():
                if item.is_dir():
                    print(f"  {item}")
            exit(1)
        
        # Run hydraulic simulation
        results = wascal_network_simulation(
            args.csv_folder,
            max_iter=args.max_iter,
            tolerance=args.tolerance,
            debug=args.debug,
            debug_every=args.debug_every,
            debug_top=args.debug_top,
        )
        
        # Print simulation results
        print_simulation_results(results)
        
        # Export pressure results to CSV
        if results:
            export_pressure_results(results)
        
        if args.detailed:
            # Show additional details
            network_data = analyze_wascal_network(args.csv_folder)
            
            print("\nDetailed Node Information (first 10):")
            for i, (_, node) in enumerate(network_data['nodes'].head(10).iterrows()):
                print(f"  Node {int(node['node_index'])}: "
                      f"Lat {node.get('latitude', 'N/A')}, "
                      f"Lon {node.get('longitude', 'N/A')}, "
                      f"Alt {node.get('altitude_m', 'N/A')}m")
                if i >= 9:
                    break
        
        if args.export:
            export_network_summary(args.csv_folder)
        
        if results:
            stats = results['network_stats']
            print(f"\nSimulation complete. Network: {stats['total_nodes']} nodes, "
                  f"{stats['total_pipelines']} pipelines, {stats['total_compressors']} compressors.")
            if args.debug and 'debug' in results:
                dbg = results['debug']
                print(f"  Residual history (len={len(dbg['residual_history'])}): first 5 = {dbg['residual_history'][:5]}")
                if dbg['iteration_samples']:
                    last = dbg['iteration_samples'][-1]
                    print(f"  Last residual sample (iter {last['iter']}): {last['top_residuals']}")
        else:
            print("\nSimulation failed.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
