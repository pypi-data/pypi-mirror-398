#!/usr/bin/env python
"""Profile import time for GasNetSim to identify bottlenecks."""
import time
import sys

def time_import(module_name, description):
    """Time how long it takes to import a module."""
    start = time.time()
    __import__(module_name)
    end = time.time()
    elapsed = end - start
    print(f"{description:60s}: {elapsed:6.3f}s")
    return elapsed

print("=" * 80)
print("GasNetSim Import Time Profiling")
print("=" * 80)

# Profile main dependencies
print("\n1. Main dependencies:")
time_import("numpy", "numpy")
time_import("pandas", "pandas")
time_import("scipy", "scipy")
time_import("matplotlib", "matplotlib")

# Profile submodules
print("\n2. GasNetSim submodules (fresh imports):")
sys.path.insert(0, '/home/yil/shared/Projects/01_main/GasNetSim')

start_total = time.time()
time_import("GasNetSim.utils", "GasNetSim.utils")
time_import("GasNetSim.profile", "GasNetSim.profile")
time_import("GasNetSim.simulation", "GasNetSim.simulation")

# Gas mixture components
print("\n3. Gas mixture submodules:")
time_import("GasNetSim.components.gas_mixture.gas_mixture", "gas_mixture.gas_mixture")
time_import("GasNetSim.components.gas_mixture.viscosity", "gas_mixture.viscosity")
time_import("GasNetSim.components.gas_mixture.GERG2008.gerg2008_constants", "GERG2008.constants")
gerg_time = time_import("GasNetSim.components.gas_mixture.GERG2008.gerg2008_numba", "GERG2008.gerg2008_numba (Numba JIT)")
time_import("GasNetSim.components.gas_mixture.GERG2008.gerg2008", "GERG2008.gerg2008")

print("\n4. Core components:")
time_import("GasNetSim.components.node", "components.node")
time_import("GasNetSim.components.pipeline", "components.pipeline")
time_import("GasNetSim.components.network", "components.network")

print("\n5. Full package import:")
# Clear module cache for components
for key in list(sys.modules.keys()):
    if 'GasNetSim.components' in key and key in sys.modules:
        del sys.modules[key]

import_time = time_import("GasNetSim.components", "GasNetSim.components (full)")
end_total = time.time()

print("\n" + "=" * 80)
print(f"GERG2008 Numba module time: {gerg_time:.3f}s")
print(f"Full components import time: {import_time:.3f}s")
print(f"Total profiling time: {end_total - start_total:.3f}s")
print("=" * 80)