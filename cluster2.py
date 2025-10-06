"""
Cluster Distribution Visualization using PCA
Creates 2D visualization of clusters using Principal Component Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("CLUSTER DISTRIBUTION - PCA VISUALIZATION")
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

# Remove any rows with missing values
features = features.dropna()
print(f"Features prepared: {len(features)} records")

# Standardize features
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Apply K-Means clustering with optimal number (6 clusters)
print("\nApplying K-Means clustering (k=6)...")
optimal_k = 6
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
clusters = kmeans.fit_predict(features_scaled)

print(f"Clustering complete. Distribution:")
for i in range(optimal_k):
    count = np.sum(clusters == i)
    print(f"  Cluster {i+1}: {count} records ({count/len(clusters)*100:.1f}%)")

# Apply PCA for 2D visualization
print("\nApplying PCA for dimensionality reduction...")
pca = PCA(n_components=2, random_state=42)
features_pca = pca.fit_transform(features_scaled)

print(f"Explained variance ratio:")
print(f"  PC1: {pca.explained_variance_ratio_[0]*100:.2f}%")
print(f"  PC2: {pca.explained_variance_ratio_[1]*100:.2f}%")
print(f"  Total: {sum(pca.explained_variance_ratio_)*100:.2f}%")

# Create DataFrame for plotting
pca_df = pd.DataFrame(
    features_pca,
    columns=['Principal Component 1', 'Principal Component 2']
)
pca_df['cluster'] = clusters + 1  # Add 1 to match cluster numbering 1-6

# Define colors for clusters (matching the screenshot)
cluster_colors = {
    1: '#FF6B6B',  # Red/Pink
    2: '#B8A131',  # Olive/Yellow
    3: '#4ECDC4',  # Teal
    4: '#45B7D1',  # Blue
    5: '#95A5A6',  # Gray
    6: '#E08DAC'   # Pink/Magenta
}

# Skip the basic PCA plot - will only create the full version with title

# Create full figure with title
print("\nCreating final visualization with main title...")
fig = plt.figure(figsize=(12, 8))
fig.patch.set_facecolor('#E8E8E8')

# Add main title at top
fig.text(0.5, 0.95, 'DISTRIBUTION OF CLUSTERS', 
         ha='center', fontsize=20, weight='normal', color='#4A4A4A')

# Create subplot for the PCA plot
ax = fig.add_subplot(111)
ax.set_facecolor('white')

# Plot each cluster
for cluster_id in range(1, optimal_k + 1):
    cluster_data = pca_df[pca_df['cluster'] == cluster_id]
    ax.scatter(
        cluster_data['Principal Component 1'],
        cluster_data['Principal Component 2'],
        c=cluster_colors[cluster_id],
        label=str(cluster_id),
        alpha=0.6,
        s=30,
        edgecolors='none'
    )

# Styling
ax.set_xlabel('Principal Component 1', fontsize=11)
ax.set_ylabel('Principal Component 2', fontsize=11)
ax.set_title('PCA - Kmeans Clustering', fontsize=12, pad=10)
ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
ax.spines['top'].set_visible(True)
ax.spines['right'].set_visible(True)
ax.spines['left'].set_visible(True)
ax.spines['bottom'].set_visible(True)

# Add legend
legend = ax.legend(title='cluster', loc='center left', bbox_to_anchor=(1, 0.5),
                   frameon=True, fancybox=False, shadow=False)
legend.get_frame().set_facecolor('white')
legend.get_frame().set_edgecolor('black')
legend.get_frame().set_linewidth(0.5)

plt.tight_layout(rect=[0, 0.02, 1, 0.93])
plt.savefig('outputs/cluster_distribution_full.png', dpi=300, 
            bbox_inches='tight', facecolor='#E8E8E8')
print("Saved: outputs/cluster_distribution_full.png")

plt.show()

# Export cluster assignments
print("\nExporting cluster assignments...")
sales_df_with_clusters = sales_df.loc[features.index].copy()
sales_df_with_clusters['cluster'] = clusters + 1
sales_df_with_clusters['pc1'] = features_pca[:, 0]
sales_df_with_clusters['pc2'] = features_pca[:, 1]

sales_df_with_clusters.to_csv('outputs/sales_with_clusters.csv', index=False)
print("Saved: outputs/sales_with_clusters.csv")

# Print cluster statistics
print("\n" + "="*70)
print("CLUSTER STATISTICS")
print("="*70)

for cluster_id in range(1, optimal_k + 1):
    cluster_mask = sales_df_with_clusters['cluster'] == cluster_id
    cluster_stats = sales_df_with_clusters[cluster_mask]
    
    print(f"\nCluster {cluster_id} ({len(cluster_stats)} records):")
    print(f"  Avg Sales Amount: ৳{cluster_stats['sales_amount'].mean():,.2f}")
    print(f"  Avg Units Sold: {cluster_stats['units_sold'].mean():.1f}")
    print(f"  Avg Price: ৳{cluster_stats['price_bdt'].mean():,.2f}")
    print(f"  Avg Rating: {cluster_stats['customer_rating'].mean():.2f}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print("\nFiles generated:")
print("  - outputs/cluster_distribution_full.png")
print("  - outputs/sales_with_clusters.csv")