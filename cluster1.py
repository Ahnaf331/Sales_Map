"""
Clean Cluster Elbow Analysis - Matches Screenshot Exactly
Generates the elbow plot with scientific notation and optimal cluster identification
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("CLUSTER ELBOW ANALYSIS - CLEAN VERSION")
print("="*70)

# Load the central sales data
print("\nLoading data...")
df = pd.read_csv('outputs/central_sales_data.csv')

# Filter for sales data only
sales_df = df[df['data_type'] == 'sales'].copy()
print(f"Loaded {len(sales_df)} sales records")

# Prepare features for clustering
print("\nPreparing features for clustering...")
features = sales_df[['sales_amount', 'units_sold', 'price_bdt', 'customer_rating']].copy()
features = features.dropna()
print(f"Features prepared: {len(features)} records")

# Standardize features
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Calculate WCSS for different numbers of clusters
print("\nCalculating WCSS for k=2 to k=15...")
wcss = []
K_range = range(2, 16)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(features_scaled)
    wcss.append(kmeans.inertia_)
    print(f"  K={k}: WCSS = {kmeans.inertia_:.2e}")

# Calculate optimal k using elbow method
differences = np.diff(wcss)
second_differences = np.diff(differences)
optimal_k = np.argmin(second_differences) + 2

print(f"\nOptimal number of clusters: {optimal_k}")

# Create the figure matching the screenshot
print("\nCreating visualization...")
fig = plt.figure(figsize=(12, 8))
fig.patch.set_facecolor('#E8E8E8')

# Add main title at top
fig.text(0.08, 0.95, 'NUMBER OF CLUSTERS IDENTIFICATION', 
         fontsize=22, weight='normal', color='#3A3A3A',
         family='sans-serif')

# Create the plot area
ax = fig.add_axes([0.15, 0.3, 0.75, 0.55])
ax.set_facecolor('white')

# Plot the elbow curve
ax.plot(K_range, wcss, 'o--', 
        linewidth=1.5, 
        markersize=7, 
        color='black', 
        markerfacecolor='white', 
        markeredgewidth=1.5,
        markeredgecolor='black')

# Set axis labels
ax.set_xlabel('Number of Clusters', fontsize=11, color='#3A3A3A')
ax.set_ylabel('Within groups sum of squares', fontsize=11, color='#3A3A3A', rotation=90)

# Set axis properties
ax.set_xticks(K_range)
ax.set_xlim(1.5, 15.5)

# Format y-axis with scientific notation
ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
ax.yaxis.major.formatter._useMathText = True

# Grid styling
ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
ax.set_axisbelow(True)

# Spine styling - keep all spines visible
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(0.8)
    spine.set_color('black')

# Tick styling
ax.tick_params(axis='both', which='major', labelsize=10, color='black', width=0.8)

# Add optimal cluster text at bottom
fig.text(0.5, 0.12, f'Optimal number of clusters based on the Elbow method plot: {optimal_k}', 
         ha='center', fontsize=14, weight='normal', color='#3A3A3A',
         family='sans-serif')

# Save the figure
output_file = 'outputs/cluster_elbow_final.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='#E8E8E8')
print(f"Saved: {output_file}")

plt.show()

print("\n" + "="*70)
print(f"ANALYSIS COMPLETE - OPTIMAL CLUSTERS: {optimal_k}")
print("="*70)
print("\nGenerated file:")
print(f"  - {output_file}")