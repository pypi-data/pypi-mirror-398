'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-04-30 02:54:18 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-04-30 03:02:14 +0200
FilePath     : test_functions.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Assuming the modified matrixHelper.py is in the correct path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from matrixHelper import plot_correlation_heatmap

# Generate synthetic correlated data
np.random.seed(42)
n_samples = 500
n_features = 10

# Create base features
base1 = np.random.normal(0, 1, n_samples)
base2 = np.random.normal(0, 1, n_samples)
base3 = np.random.normal(0, 1, n_samples)

# Create a dataframe with correlated features
data = {
    'A': base1 + 0.1 * np.random.normal(0, 1, n_samples),
    'B': base1 + 0.2 * np.random.normal(0, 1, n_samples),
    'C': np.random.normal(0, 1, n_samples),  # Independent
    'D': base1 + 0.3 * np.random.normal(0, 1, n_samples),
    'E': base2 + 0.2 * np.random.normal(0, 1, n_samples),
    'F': base3 + 0.1 * np.random.normal(0, 1, n_samples),
    'G': base3 + 0.2 * np.random.normal(0, 1, n_samples),
    'H': np.random.normal(0, 1, n_samples),  # Independent
    'J': np.random.normal(0, 1, n_samples),  # Independent
    'K': base2 + 0.1 * np.random.normal(0, 1, n_samples),
}

df = pd.DataFrame(data)

# Create output directory
output_dir = Path('output')
output_dir.mkdir(exist_ok=True)

# Generate standard heatmap
plot_correlation_heatmap(df=df, output_plot_name='output/standard_heatmap.png', title='Standard Correlation Heatmap', cluster=False)

# Generate clustered heatmap
plot_correlation_heatmap(df=df, output_plot_name='output/clustered_heatmap.png', title='Clustered Correlation Heatmap', cluster=True)


# Save the plot
plt.savefig('standard_heatmap.png')
plt.close()

print("Validation complete. Check output directory for heatmaps.")
