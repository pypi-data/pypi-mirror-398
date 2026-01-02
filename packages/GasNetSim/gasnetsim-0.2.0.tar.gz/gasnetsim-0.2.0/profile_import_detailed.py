#!/usr/bin/env python
"""Detailed import profiling with python -X importtime equivalent."""
import time
import sys

def profile_import(module_path):
    """Profile a single import and show time."""
    # Clear any cached version
    if module_path in sys.modules:
        del sys.modules[module_path]

    start = time.time()
    try:
        mod = __import__(module_path, fromlist=[''])
        elapsed = time.time() - start
        print(f"  {module_path:70s}: {elapsed:6.3f}s")
        return elapsed, True
    except Exception as e:
        elapsed = time.time() - start
        print(f"  {module_path:70s}: {elapsed:6.3f}s (ERROR: {e})")
        return elapsed, False

print("Profiling imports step by step...")
print("=" * 80)

# Clear GasNetSim from cache
for key in list(sys.modules.keys()):
    if 'GasNetSim' in key or 'cantera' in key or 'numba' in key:
        del sys.modules[key]

sys.path.insert(0, '/home/yil/shared/Projects/01_main/GasNetSim')

print("\nStep 1: Import base dependencies")
profile_import("numpy")
profile_import("pandas")

print("\nStep 2: Import Numba (JIT compiler)")
profile_import("numba")

print("\nStep 3: Import Cantera (chemistry library)")
profile_import("cantera")

print("\nStep 4: Import gas_mixture components individually")
profile_import("GasNetSim.components.gas_mixture.GERG2008.gerg2008_constants")
profile_import("GasNetSim.components.gas_mixture.GERG2008.gerg2008")
profile_import("GasNetSim.components.gas_mixture.GERG2008.gerg2008_numba")
profile_import("GasNetSim.components.gas_mixture.GERG2008")

print("\nStep 5: Import other gas mixture modules")
profile_import("GasNetSim.components.gas_mixture.gas_mixture")
profile_import("GasNetSim.components.gas_mixture.viscosity")
profile_import("GasNetSim.components.gas_mixture")

print("\nStep 6: Import pipeline functions")
profile_import("GasNetSim.components.utils.pipeline_function")

print("\nStep 7: Import create_network utilities")
profile_import("GasNetSim.components.utils.create_network")

print("\nStep 8: Import core components")
profile_import("GasNetSim.components.node")
profile_import("GasNetSim.components.pipeline")
profile_import("GasNetSim.components.network")

print("\nStep 9: Import full components module")
start = time.time()
import GasNetSim.components
elapsed = time.time() - start
print(f"  GasNetSim.components (aggregated): {elapsed:6.3f}s")

print("\nStep 10: Import full GasNetSim package")
start = time.time()
import GasNetSim
elapsed = time.time() - start
print(f"  GasNetSim (top-level): {elapsed:6.3f}s")

print("=" * 80)