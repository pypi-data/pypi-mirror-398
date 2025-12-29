"""
Create a header image for psfed README: Masked Parameter Flow visualization.
Shows a central server connected to clients with partial parameter streams.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from matplotlib.collections import PathCollection

# Set up the figure
fig, ax = plt.subplots(figsize=(12, 4), facecolor='#0d1117')
ax.set_facecolor('#0d1117')

np.random.seed(42)

# Colors
server_color = '#58a6ff'
client_colors = ['#f78166', '#a371f7', '#3fb950', '#d29922', '#f778ba']
shared_color = '#58a6ff'
local_color = '#2d333b'
text_color = '#c9d1d9'
muted_text = '#8b949e'

# Server position (center)
server_x, server_y = 6, 2

# Client positions (arc around server)
num_clients = 5
client_positions = []
for i in range(num_clients):
    angle = np.pi * 0.15 + (np.pi * 0.7) * i / (num_clients - 1)
    cx = server_x + 4.5 * np.cos(angle)
    cy = server_y + 3.0 * np.sin(angle) - 0.5
    client_positions.append((cx, cy))

# Draw parameter streams (particles flowing between server and clients)
share_fraction = 0.5
for idx, (cx, cy) in enumerate(client_positions):
    # Calculate direction
    dx = cx - server_x
    dy = cy - server_y
    dist = np.sqrt(dx**2 + dy**2)
    
    # Draw particles along the path
    num_particles = 25
    for i in range(num_particles):
        t = i / num_particles
        # Add some spread perpendicular to the path
        spread = np.random.uniform(-0.15, 0.15)
        px = server_x + t * dx + spread * (-dy/dist)
        py = server_y + t * dy + spread * (dx/dist)
        
        # Randomly decide if shared or not
        is_shared = np.random.random() < share_fraction
        
        if is_shared:
            color = client_colors[idx]
            alpha = 0.8 - 0.3 * t  # Fade as they go out
            size = 30 - 15 * t
        else:
            color = local_color
            alpha = 0.3
            size = 20 - 10 * t
        
        ax.scatter(px, py, c=[color], s=size, alpha=alpha, edgecolors='none', zorder=2)

# Draw server (central node)
server_circle = Circle((server_x, server_y), 0.6, 
                        facecolor=server_color, edgecolor='#ffffff',
                        linewidth=2, zorder=5, alpha=0.95)
ax.add_patch(server_circle)

# Server icon (simple representation)
ax.text(server_x, server_y, '⬢', fontsize=20, ha='center', va='center', 
        color='#ffffff', zorder=6)

# Draw clients
for idx, (cx, cy) in enumerate(client_positions):
    # Client device shape
    client_rect = FancyBboxPatch(
        (cx - 0.4, cy - 0.35), 0.8, 0.7,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        facecolor=client_colors[idx],
        edgecolor='#ffffff',
        linewidth=1.5,
        alpha=0.9,
        zorder=5
    )
    ax.add_patch(client_rect)
    
    # Client icon
    ax.text(cx, cy, '▢', fontsize=14, ha='center', va='center',
            color='#ffffff', zorder=6)

# Add title
ax.text(6, 4.8, "PSFed", fontsize=42, fontweight='bold', color='#ffffff',
        ha='center', va='bottom', fontfamily='sans-serif')

ax.text(6, 4.2, "Partial Model Sharing for Federated Learning",
        fontsize=16, color=muted_text, ha='center', va='bottom', fontfamily='sans-serif')

# Add labels
ax.text(server_x, server_y - 1.0, "Server", fontsize=10, color=text_color,
        ha='center', va='top', fontfamily='sans-serif')

# Legend
legend_y = -0.8
ax.scatter([2.5], [legend_y], c=[shared_color], s=50, alpha=0.8, edgecolors='none')
ax.text(3.0, legend_y, "Shared Parameters", fontsize=10, color=text_color,
        va='center', fontfamily='sans-serif')

ax.scatter([7.5], [legend_y], c=[local_color], s=50, alpha=0.5, edgecolors='none')
ax.text(8.0, legend_y, "Local Only", fontsize=10, color=muted_text,
        va='center', fontfamily='sans-serif')

# Set limits and remove axes
ax.set_xlim(0, 12)
ax.set_ylim(-1.5, 5.8)
ax.set_aspect('equal')
ax.axis('off')

# Save
plt.tight_layout()
plt.savefig('header_flow.png', dpi=150, bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none', pad_inches=0.3)
plt.savefig('header_flow.svg', bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none', pad_inches=0.3)

print("Header images saved: header_flow.png and header_flow.svg")
plt.show()
