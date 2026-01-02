from pathlib import Path
import matplotlib.pyplot as plt
from scipy.constants import bar
import plotly.graph_objects as go

import GasNetSim as gns

if __name__ == "__main__":

    network = gns.create_network_from_files({
        "nodes":"7nodes_with_compressors_fixed.csv",
        "pipelines":"7pipelines_with_compressors_fixed.csv",
        "compressors": "7compressors_with_compressors_fixed.csv"
    }, initialization_strategy='compressor_aware')

    # Define groups
    exclude_node = 32
    group_a = {34, 35, 37, 39, 41, 70, 71, 72}

    total_prod_A_sm3_s = 0
    total_prod_B_sm3_s = 0

    for idx, n in network.nodes.items():
        if n.volumetric_flow and idx != exclude_node:
            if idx in group_a:
                total_prod_A_sm3_s += n.volumetric_flow
            else:
                total_prod_B_sm3_s += n.volumetric_flow

    print("Initial production Group A (Sm3/s):", total_prod_A_sm3_s)
    print("Initial production Group B (Sm3/s):", total_prod_B_sm3_s)

    # Convert Sm³/s → bcm/year just for scaling factor computation
    sm3s_to_bcm_y = lambda flow: flow * 60 * 60 * 24 * 365 / 1e9

    target_total_production = 30  # bcm/year for each group

    scaling_factor_A = sm3s_to_bcm_y(total_prod_A_sm3_s) / target_total_production if total_prod_A_sm3_s != 0 else 1
    scaling_factor_B = sm3s_to_bcm_y(total_prod_B_sm3_s) / target_total_production if total_prod_B_sm3_s != 0 else 1

    print("Scaling factor Group A:", scaling_factor_A)
    print("Scaling factor Group B:", scaling_factor_B)

    for p in network.pipelines.values():
        p.diameter = 1.23
        p.efficiency = 1

    for idx, n in network.nodes.items():
        if n.volumetric_flow and idx != exclude_node:
            if idx in group_a:
                n.volumetric_flow = -n.volumetric_flow / scaling_factor_A
            else:
                n.volumetric_flow = -n.volumetric_flow / scaling_factor_B

    total_prod_A_sm3_s = 0
    total_prod_B_sm3_s = 0

    for idx, n in network.nodes.items():
        if n.volumetric_flow and idx != exclude_node:
            if idx in group_a:
                total_prod_A_sm3_s += n.volumetric_flow
            else:
                total_prod_B_sm3_s += n.volumetric_flow

    cumulative_sm3_s = total_prod_A_sm3_s + total_prod_B_sm3_s

    print("Final production Group A (Sm3/s):", total_prod_A_sm3_s)
    print("Final production Group B (Sm3/s):", total_prod_B_sm3_s)
    print("Cumulative production (Sm3/s):", cumulative_sm3_s)

    network.simulation(max_iter=500, underrelaxation_factor=8, tol=1e-2)