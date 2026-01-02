from pathlib import Path
import matplotlib.pyplot as plt
from scipy.constants import bar
import plotly.graph_objects as go

import GasNetSim as gns

if __name__ == "__main__":

    network = gns.create_network_from_files({
        "nodes":"7nodes_with_compressors.csv",
        "pipelines":"7pipelines_with_compressors.csv",
        "compressors": "7compressors_with_compressors.csv"
    })

    network.simulation(tracking_method=None, max_iter=5)