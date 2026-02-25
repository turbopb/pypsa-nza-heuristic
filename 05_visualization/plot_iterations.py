"""
Plot load shedding vs capacity additions with exponential fit.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# Data from our iterations
capacity_added = np.array([0, 1251, 1450, 1750, 2025, 2325, 2525, 2950])  # MW
load_shedding = np.array([5.96, 2.02, 1.07, 0.44, 0.20, 0.04, 0.02, 0.00])  # %

# Define exponential decay model
def exp_decay(x, a, b, c):
    """Exponential decay: y = a * exp(-b*x) + c"""
    return a * np.exp(-b * x) + c

# Fit the model
popt, _ = curve_fit(exp_decay, capacity_added, load_shedding, 
                    p0=[6, 0.001, 0], maxfev=10000)

print("Exponential fit parameters:")
print(f"  y = {popt[0]:.2f} * exp(-{popt[1]:.6f} * x) + {popt[2]:.4f}")

# Generate smooth curve
capacity_smooth = np.linspace(0, 3500, 500)
shedding_smooth = exp_decay(capacity_smooth, *popt)

# Find capacity for different targets
capacity_for_zero = capacity_smooth[np.argmin(np.abs(shedding_smooth - 0.01))]
capacity_for_half = capacity_smooth[np.argmin(np.abs(shedding_smooth - 0.5))]

# Estimate 10% reserve margin point
peak_demand = 7827  # MW
print(f"\nPeak demand: {peak_demand} MW")
print(f"Capacity for ~0% shedding: {capacity_for_zero:.0f} MW")
print(f"Capacity for 0.5% shedding: {capacity_for_half:.0f} MW")

# Create the plot
fig, ax = plt.subplots(figsize=(14, 8))

# Plot fitted curve
ax.plot(capacity_smooth, shedding_smooth, 'b-', linewidth=3, 
        label='Exponential Fit', alpha=0.8)

# Plot actual data points
ax.scatter(capacity_added, load_shedding, color='red', s=150, 
          zorder=5, label='Actual Iterations', edgecolors='darkred', linewidth=2)

# Mark key thresholds
ax.axhline(y=0, color='green', linestyle='--', linewidth=2, 
          label='Zero Shedding Target', alpha=0.7)
ax.axhline(y=0.5, color='orange', linestyle='--', linewidth=1.5, 
          label='0.5% Shedding (~Adequate)', alpha=0.7)

# Vertical lines for key capacities
ax.axvline(x=capacity_for_zero, color='green', linestyle=':', 
          linewidth=2, alpha=0.5)
ax.axvline(x=capacity_for_half, color='orange', linestyle=':', 
          linewidth=1.5, alpha=0.5)

# Annotations
ax.annotate(f'Zero shedding\n~{capacity_for_zero:.0f} MW',
           xy=(capacity_for_zero, 0.05), 
           xytext=(capacity_for_zero + 400, 1.2),
           arrowprops=dict(arrowstyle='->', color='green', lw=2),
           fontsize=11, fontweight='bold', color='green',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

ax.annotate(f'Baseline\n5.96% shedding\n0 MW added',
           xy=(0, 5.96), xytext=(600, 5.2),
           arrowprops=dict(arrowstyle='->', color='darkred', lw=2),
           fontsize=10, fontweight='bold')

ax.annotate(f'Final Design\n2,950 MW\n0% shedding\n19.1% reserve',
           xy=(2950, exp_decay(2950, *popt)), 
           xytext=(2200, 3.5),
           arrowprops=dict(arrowstyle='->', color='blue', lw=2),
           fontsize=11, fontweight='bold', color='blue',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

ax.annotate(f'Adequate system\n~{capacity_for_half:.0f} MW\n0.5% shedding',
           xy=(capacity_for_half, 0.5), 
           xytext=(capacity_for_half - 600, 2),
           arrowprops=dict(arrowstyle='->', color='orange', lw=1.5),
           fontsize=10, fontweight='bold', color='orange')

# Formatting
ax.set_xlabel('Capacity Added (MW)', fontsize=14, fontweight='bold')
ax.set_ylabel('Load Shedding (%)', fontsize=14, fontweight='bold')
ax.set_title('2030 Heuristic Capacity Planning: Exponential Adequacy Response', 
            fontsize=16, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
ax.set_xlim(-100, 3500)
ax.set_ylim(-0.3, 6.5)

plt.tight_layout()
plt.savefig('2030_capacity_iterations.png', dpi=300, bbox_inches='tight')
print(f"\n? Plot saved to: 2030_capacity_iterations.png")

plt.show()

# Summary table
print("\n" + "="*60)
print("CAPACITY REQUIREMENTS SUMMARY")
print("="*60)
print(f"\nBaseline (2024 infrastructure):")
print(f"  Capacity added: 0 MW")
print(f"  Load shedding: 5.96%")
print(f"  Status: CRITICAL")

print(f"\nAdequate system (~0.5% shedding acceptable):")
print(f"  Capacity needed: ~{capacity_for_half:.0f} MW")
print(f"  Load shedding: ~0.5%")
print(f"  Status: MARGINAL")

print(f"\nZero shedding (no reserve margin):")
print(f"  Capacity needed: ~{capacity_for_zero:.0f} MW")
print(f"  Load shedding: ~0%")
print(f"  Status: ADEQUATE")

print(f"\nFinal design (with reserve margin):")
print(f"  Capacity added: 2,950 MW")
print(f"  Load shedding: 0%")
print(f"  Effective reserve: 19.1%")
print(f"  Status: HEALTHY")

print(f"\nMargin of safety: {2950 - capacity_for_zero:.0f} MW above zero shedding")