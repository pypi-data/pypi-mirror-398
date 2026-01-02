# CSV-Based Gas Network Simulation

This folder contains Python implementations for gas network simulation using CSV input files, adapted from the original hardcoded simulation function.

## Files Description

### 1. `csv_gas_network_simulation.py`
The first implementation that closely follows the original `solve_gas_network()` function structure:
- Specifically designed for 4-node, 3-pipeline, 1-compressor networks
- Reads CSV files from the minimal_example folder
- Maintains the same Newton-Raphson solver logic as the original

### 2. `simple_csv_simulation.py` ⭐ **RECOMMENDED**
A robust, simplified version that:
- Automatically finds CSV files in the specified folder
- Provides detailed output including network configuration
- Supports command-line arguments
- Works reliably with the minimal example network

### 3. `general_csv_gas_simulation.py`
A more ambitious attempt at a general-purpose simulator:
- Intended to work with networks of any size
- Includes object-oriented design
- Currently needs refinement for complex networks

## CSV File Format

The simulation expects three CSV files with semicolon separators:

### Nodes CSV (`*nodes*.csv`)
```csv
node_index;longitude;latitude;altitude_m;temperature_k;node_type;flow_sm3_per_s;pressure_pa;flow_MW;flow_type;gas_composition
1;0;0;0;300;reference;0;5000000;;volumetric;NATURAL_GAS_gri30
2;1;0;0;288.15;demand;30;4500000;;volumetric;NATURAL_GAS_gri30
3;2;0;0;288.15;demand;30;4950000;;volumetric;NATURAL_GAS_gri30
4;3;0;0;288.15;demand;14.28571;4000000;;volumetric;NATURAL_GAS_gri30
```

### Pipelines CSV (`*pipelines*.csv`)
```csv
pipeline_index;inlet_index;outlet_index;diameter_m;length_m;roughness;efficiency
1;1;2;0.5;200000;0.000015;0.85
2;3;4;0.5;400000;0.000015;0.85
3;1;4;0.5;100000;0.000015;0.85
```

### Compressors CSV (`*compressors*.csv`)
```csv
compressor_index;inlet;outlet;compression_ratio;efficiency;thermodynamic_process
1;2;3;1.2;0.85;isentropic
```

## Usage Examples

### Basic Usage (Recommended)
```bash
python simple_csv_simulation.py ./minimal_example
```

### With Gas Turbine Compressor
```bash
python simple_csv_simulation.py ./minimal_example --gas-turbine
```

### Custom Power Demand
```bash
python simple_csv_simulation.py ./minimal_example --power-mw -500 --gas-turbine
```

### Original Direct Function Call
```python
from csv_gas_network_simulation import solve_gas_network_from_csv

results = solve_gas_network_from_csv(
    "./minimal_example", 
    P2_power_mw=-300, 
    use_gas_turbine_compressor=False
)
print_results(results)
```

## Sample Output

```
============================================================
GAS NETWORK SIMULATION RESULTS (from CSV)
============================================================

NETWORK CONFIGURATION:
  Node 1: P=50.0 bar, T=300.0 K, H=0.0 m, D=0.0 sm³/s
  Node 2: P=45.0 bar, T=288.1 K, H=0.0 m, D=30.0 sm³/s
  Node 3: P=49.5 bar, T=288.1 K, H=0.0 m, D=30.0 sm³/s
  Node 4: P=40.0 bar, T=288.1 K, H=0.0 m, D=14.3 sm³/s

Compressor: 1.2 ratio, 0.85 efficiency

SOLUTION:
Pressures (bar):
  p1: 50.00
  p2: 47.07
  p3: 56.48
  p4: 51.38

Flow Rates (sm³/s):
  Pipe 1-2: 9539.251
  Compressor 2-3: 9509.251
  Pipe 3-4: 9479.251
  Pipe 1-4: -9462.109

Compressor Power: 232.72 MW
Gas Consumption: 0.000 sm³/s

Convergence: 11 iterations, error = 1.59e-09
============================================================
```

## Key Features

1. **CSV Integration**: Reads network topology and parameters from CSV files
2. **Flexible Input**: Automatically detects CSV files in the specified folder
3. **Dual Compressor Models**: Supports both electric and gas turbine compressors
4. **Newton-Raphson Solver**: Same convergence algorithm as original code
5. **Detailed Output**: Shows network configuration and solution results
6. **Command Line Interface**: Easy to use with different parameters

## Network Topology

The current implementation handles the following network structure:
- Node 1: Reference node (50 bar)
- Node 2: Compressor inlet, demand node
- Node 3: Compressor outlet, demand node  
- Node 4: Gas turbine node
- Pipelines: 1→2, 3→4, 1→4
- Compressor: 2→3 with configurable compression ratio

## Dependencies

- `numpy`: Numerical computations
- `pandas`: CSV file reading
- `scipy`: Physical constants
- `pathlib`: File path handling
- `argparse`: Command line interface

## Notes

- Negative flow rates indicate reverse flow direction
- The solver uses the same physics as the original implementation
- Convergence typically occurs within 10-15 iterations
- Gas turbine compressor consumption is calculated based on actual power requirements