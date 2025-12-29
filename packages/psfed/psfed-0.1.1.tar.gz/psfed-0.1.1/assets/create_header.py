"""
Create a header image for psfed README: Binary Mask Grid visualization.
Shows a neural network weight matrix with partial sharing mask overlay.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Set up the figure with a wide aspect ratio for GitHub header
fig, ax = plt.subplots(figsize=(12, 4), facecolor='#0d1117')  # GitHub dark theme
ax.set_facecolor('#0d1117')

# Parameters
np.random.seed(42)
grid_rows, grid_cols = 8, 32
cell_size = 0.9
gap = 0.1
share_fraction = 0.5

# Generate random "weights" and mask
weights = np.random.randn(grid_rows, grid_cols)
mask = np.random.random((grid_rows, grid_cols)) < share_fraction

# Color schemes
shared_cmap = plt.cm.plasma  # Vibrant for shared
local_color = '#2d333b'  # Muted gray for local

# Draw the grid
for i in range(grid_rows):
    for j in range(grid_cols):
        x = j * (cell_size + gap)
        y = (grid_rows - 1 - i) * (cell_size + gap)
        
        if mask[i, j]:
            # Shared parameter - vibrant color based on weight value
            normalized_weight = (weights[i, j] - weights.min()) / (weights.max() - weights.min())
            color = shared_cmap(normalized_weight)
            alpha = 0.95
            edgecolor = '#ffffff'
            linewidth = 0.5
        else:
            # Local parameter - muted
            color = local_color
            alpha = 0.4
            edgecolor = '#444c56'
            linewidth = 0.3
        
        rect = patches.FancyBboxPatch(
            (x, y), cell_size, cell_size,
            boxstyle="round,pad=0.02,rounding_size=0.15",
            facecolor=color,
            edgecolor=edgecolor,
            linewidth=linewidth,
            alpha=alpha
        )
        ax.add_patch(rect)

# Add title text
ax.text(
    grid_cols * (cell_size + gap) / 2, 
    grid_rows * (cell_size + gap) + 1.2,
    "PSFed",
    fontsize=42,
    fontweight='bold',
    color='#ffffff',
    ha='center',
    va='bottom',
    fontfamily='sans-serif'
)

ax.text(
    grid_cols * (cell_size + gap) / 2,
    grid_rows * (cell_size + gap) + 0.3,
    "Partial Model Sharing for Federated Learning",
    fontsize=16,
    color='#8b949e',
    ha='center',
    va='bottom',
    fontfamily='sans-serif'
)

# Add legend indicators
legend_y = -1.5
legend_x_start = grid_cols * (cell_size + gap) / 2 - 8

# Shared indicator
shared_rect = patches.FancyBboxPatch(
    (legend_x_start, legend_y), 0.8, 0.8,
    boxstyle="round,pad=0.02,rounding_size=0.1",
    facecolor=shared_cmap(0.7),
    edgecolor='#ffffff',
    linewidth=0.5,
    alpha=0.95
)
ax.add_patch(shared_rect)
ax.text(legend_x_start + 1.2, legend_y + 0.4, "Shared Parameters", 
        fontsize=11, color='#c9d1d9', va='center', fontfamily='sans-serif')

# Local indicator
local_rect = patches.FancyBboxPatch(
    (legend_x_start + 9, legend_y), 0.8, 0.8,
    boxstyle="round,pad=0.02,rounding_size=0.1",
    facecolor=local_color,
    edgecolor='#444c56',
    linewidth=0.3,
    alpha=0.4
)
ax.add_patch(local_rect)
ax.text(legend_x_start + 10.2, legend_y + 0.4, "Local Parameters", 
        fontsize=11, color='#8b949e', va='center', fontfamily='sans-serif')

# Set axis limits and remove axes
ax.set_xlim(-1, grid_cols * (cell_size + gap) + 1)
ax.set_ylim(-3, grid_rows * (cell_size + gap) + 4)
ax.set_aspect('equal')
ax.axis('off')

# Save
plt.tight_layout()
plt.savefig('header.png', dpi=150, bbox_inches='tight', 
            facecolor='#0d1117', edgecolor='none', pad_inches=0.3)
plt.savefig('header.svg', bbox_inches='tight', 
            facecolor='#0d1117', edgecolor='none', pad_inches=0.3)

print("Header images saved: header.png and header.svg")
plt.show()
