#!/usr/bin/env python
"""Test script to verify contextily backend fix."""

import sys
import importlib
from pathlib import Path

# Force reload of modules to get latest changes
if 'GasNetSim.components.utils.plot_functions' in sys.modules:
    importlib.reload(sys.modules['GasNetSim.components.utils.plot_functions'])

import GasNetSim as gns
from GasNetSim.components.utils.plot_functions import plot_network_pipeline_flow_results

def test_contextily_backend():
    """Test the fixed contextily backend."""
    
    # Load Irish13 network
    irish13_path = Path("examples/Irish13")
    if not irish13_path.exists():
        print("Irish13 example not found")
        return
    
    # Create and simulate network

    print("Loading and simulating Irish13 network...")
    network = gns.create_network_from_folder(irish13_path)
    network.simulation(use_cuda=False, tol=1e-4)
    print("Simulation complete!")
    
    # Test contextily backend specifically
    print("\nTesting fixed contextily backend...")
    try:
        fig, ax = plot_network_pipeline_flow_results(
            network, 
            backend="contextily",
            pipeline_color="#FF6B6B",
            figsize=(10, 8)
        )
        print("✓ Contextily backend test successful!")
        
        # Save the plot
        import matplotlib.pyplot as plt
        plt.savefig("contextily_test.png", dpi=150, bbox_inches='tight')
        print("✓ Plot saved as contextily_test.png")
        plt.close()
        
    except Exception as e:
        print(f"✗ Contextily backend test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_contextily_backend()