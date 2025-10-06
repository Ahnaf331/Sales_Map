import pandas as pd
import numpy as np
import folium
from folium.plugins import MiniMap
import random
import json
import os
from datetime import date, datetime, timedelta

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)


def generate_brand_data(config, n_locations=150, seed=42):
    """Generate synthetic brand coverage data for different locations."""
    random.seed(seed)
    np.random.seed(seed)
    
    cities = config['cities']
    city_names = [c[0] for c in cities]
    city_lats = [c[1] for c in cities]
    city_lons = [c[2] for c in cities]
    city_weights = np.array([c[3] for c in cities], dtype=float)
    city_weights /= city_weights.sum()
    
    # Define regions based on actual Bangladesh geography
    regions = {
        'North': ['Rangpur', 'Dinajpur', 'Nilphamari', 'Gaibandha', 'Thakurgaon', 'Panchagarh', 
                  'Kurigram', 'Lalmonirhat', 'Saidpur', 'Bogra', 'Pabna', 'Natore', 'Sirajganj'],
        'South': ['Barishal', 'Bhola', 'Patuakhali', 'Barguna', 'Pirojpur', 'Jhalokati'],
        'East': ['Sylhet', 'Moulvibazar', 'Habiganj', 'Sunamganj', 'Comilla', 'Brahmanbaria', 
                 'Feni', 'Khagrachhari', 'Bandarban', 'Rangamati', "Cox's Bazar"],
        'West': ['Khulna', 'Kushtia', 'Jessore', 'Satkhira', 'Chuadanga', 'Meherpur', 
                 'Magura', 'Narail', 'Jhenaidah', 'Rajshahi'],
        'Central': ['Dhaka', 'Narayanganj', 'Gazipur', 'Tangail', 'Kishoreganj', 'Manikganj', 
                    'Munshiganj', 'Madaripur', 'Shariatpur', 'Faridpur', 'Rajbari', 'Mymensingh',
                    'Jamalpur', 'Sherpur', 'Netrokona', 'Chandpur', 'Chattogram']
    }
    
    # Define brand names
    brands = [
        'Brand A', 'Brand B', 'Brand C', 'Brand D', 'Brand E',
        'Brand F', 'Brand G', 'Brand H', 'Brand I', 'Brand J'
    ]
    
    locations = []
    
    for city_name in city_names:
        city_idx = city_names.index(city_name)
        base_lat, base_lon = city_lats[city_idx], city_lons[city_idx]
        city_weight = city_weights[city_idx]
        
        # Determine region
        region = next((r for r, cities_list in regions.items() if city_name in cities_list), 'Central')
        
        # Number of brand locations in this city (more for bigger cities)
        num_locations = max(1, int(city_weight * 100))
        
        for i in range(num_locations):
            # Add some spatial variation
            lat = base_lat + np.random.normal(0, 0.05)
            lon = base_lon + np.random.normal(0, 0.08)
            
            # Random brand
            brand = random.choice(brands)
            
            # Coverage score (0-100) - higher for major cities
            if city_weight > 0.15:  # Major cities
                coverage_score = random.randint(60, 100)
            elif city_weight > 0.05:  # Medium cities
                coverage_score = random.randint(40, 80)
            else:  # Small cities
                coverage_score = random.randint(20, 60)
            
            # Number of outlets for this brand in this location
            num_outlets = max(1, int(coverage_score / 10) + random.randint(-2, 3))
            
            # Market share percentage
            market_share = round(random.uniform(5, 35), 1)
            
            locations.append({
                'city': city_name,
                'region': region,
                'latitude': lat,
                'longitude': lon,
                'brand': brand,
                'coverage_score': coverage_score,
                'num_outlets': num_outlets,
                'market_share': market_share
            })
    
    return pd.DataFrame(locations)


def create_brand_coverage_map(df, output_file='outputs/brand_coverage_map.html'):
    """Create an interactive brand coverage map with dark theme."""
    
    # Center on Bangladesh
    center_lat = 23.8103
    center_lon = 90.4125
    
    # Create base map with dark theme
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='CartoDB dark_matter',
        control_scale=True
    )
    
    # Define coverage colors (matching the screenshot)
    def get_coverage_color(score):
        """Return color based on coverage score."""
        if score >= 75:
            return '#FFD700'  # Gold/Yellow - High coverage
        elif score >= 50:
            return '#FFA500'  # Orange - Medium coverage
        else:
            return '#FF6B6B'  # Red/Pink - Low coverage
    
    # Calculate circle sizes based on coverage score
    max_coverage = df['coverage_score'].max()
    min_coverage = df['coverage_score'].min()
    
    # Add markers for each location
    for idx, row in df.iterrows():
        # Calculate radius based on coverage score (logarithmic scale for better visualization)
        normalized_score = (row['coverage_score'] - min_coverage) / (max_coverage - min_coverage)
        radius = 5 + (normalized_score ** 0.7) * 25  # Range from 5 to 30
        
        color = get_coverage_color(row['coverage_score'])
        
        # Create popup content
        popup_html = f"""
        <div style='font-family: Arial; font-size: 12px; min-width: 200px;'>
            <h4 style='margin: 0 0 10px 0; color: #333;'>{row['brand']}</h4>
            <table style='width: 100%; border-collapse: collapse;'>
                <tr>
                    <td style='padding: 3px 0;'><b>City:</b></td>
                    <td style='padding: 3px 0;'>{row['city']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Region:</b></td>
                    <td style='padding: 3px 0;'>{row['region']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Coverage Score:</b></td>
                    <td style='padding: 3px 0;'>{row['coverage_score']}/100</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Outlets:</b></td>
                    <td style='padding: 3px 0;'>{row['num_outlets']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Market Share:</b></td>
                    <td style='padding: 3px 0;'>{row['market_share']}%</td>
                </tr>
            </table>
        </div>
        """
        
        # Add circle marker
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['brand']} - {row['city']} (Coverage: {row['coverage_score']})",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2,
            opacity=0.8
        ).add_to(m)
    
    # Add city labels for major cities
    major_cities = df.groupby('city').agg({
        'coverage_score': 'mean',
        'latitude': 'first',
        'longitude': 'first'
    }).reset_index()
    
    # Filter for top cities by coverage
    major_cities = major_cities.nlargest(15, 'coverage_score')
    
    for idx, city in major_cities.iterrows():
        folium.Marker(
            location=[city['latitude'], city['longitude']],
            icon=folium.DivIcon(html=f'''
                <div style="font-size: 11px; 
                            color: white; 
                            font-weight: bold; 
                            text-shadow: 1px 1px 2px black, -1px -1px 2px black;
                            white-space: nowrap;
                            font-family: Arial;">
                    {city['city']}
                </div>
            ''')
        ).add_to(m)
    
    # Add division labels
    divisions = {
        'DHAKA': [23.8103, 90.4125],
        'CHATTOGRAM\nDIVISION': [22.3569, 91.7832],
        'SYLHET DIVISION': [24.8949, 91.8687],
        'KHULNA DIVISION': [22.8456, 89.5403],
        'RAJSHAHI\nDIVISION': [24.3636, 88.6241],
        'RANGPUR': [25.7439, 89.2752],
        'BARISHAL\nDIVISION': [22.7010, 90.3535],
        'MYMENSINGH\nDIVISION': [24.7500, 90.3800]
    }
    
    for division, coords in divisions.items():
        folium.Marker(
            location=coords,
            icon=folium.DivIcon(html=f'''
                <div style="font-size: 10px; 
                            color: #999; 
                            font-weight: normal; 
                            text-transform: uppercase;
                            letter-spacing: 1px;
                            white-space: pre;
                            font-family: Arial;
                            text-align: center;">
                    {division}
                </div>
            ''')
        ).add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; 
                left: 50%; 
                transform: translateX(-50%);
                width: 400px; 
                height: 60px; 
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 5px;
                z-index: 9999; 
                text-align: center;
                padding: 10px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0; 
                   font-family: Arial, sans-serif; 
                   font-size: 24px;
                   color: #333;
                   font-weight: 300;
                   letter-spacing: 1px;">
            Brand Coverage Map
        </h3>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 30px; 
                left: 30px; 
                width: 200px; 
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 5px;
                z-index: 9999; 
                font-size: 13px;
                padding: 15px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 10px 0; font-family: Arial;">Coverage Level</h4>
        <div style="margin: 8px 0;">
            <i style="background: #FFD700; 
                      width: 20px; 
                      height: 20px; 
                      float: left; 
                      margin-right: 10px;
                      border-radius: 50%;
                      border: 2px solid #FFD700;"></i>
            <span style="line-height: 20px;">High (75-100)</span>
        </div>
        <div style="margin: 8px 0; clear: both;">
            <i style="background: #FFA500; 
                      width: 20px; 
                      height: 20px; 
                      float: left; 
                      margin-right: 10px;
                      border-radius: 50%;
                      border: 2px solid #FFA500;"></i>
            <span style="line-height: 20px;">Medium (50-74)</span>
        </div>
        <div style="margin: 8px 0; clear: both;">
            <i style="background: #FF6B6B; 
                      width: 20px; 
                      height: 20px; 
                      float: left; 
                      margin-right: 10px;
                      border-radius: 50%;
                      border: 2px solid #FF6B6B;"></i>
            <span style="line-height: 20px;">Low (0-49)</span>
        </div>
        <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 11px; color: #666;">
            Circle size represents coverage intensity
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add MiniMap
    minimap = MiniMap(
        toggle_display=True,
        position='bottomright'
    )
    m.add_child(minimap)
    
    # Save map
    m.save(output_file)
    print(f"✅ Brand coverage map saved to: {output_file}")
    
    return m


def export_brand_data_to_excel(df, filename='outputs/brand_coverage_analysis.xlsx'):
    """Export brand coverage data to Excel with summary sheets."""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Main data sheet
        df.to_excel(writer, sheet_name='Brand Coverage Data', index=False)
        
        # Summary by brand
        brand_summary = df.groupby('brand').agg({
            'coverage_score': 'mean',
            'num_outlets': 'sum',
            'market_share': 'mean',
            'city': 'count'
        }).round(2)
        brand_summary.columns = ['Avg Coverage Score', 'Total Outlets', 'Avg Market Share %', 'Locations']
        brand_summary = brand_summary.sort_values('Avg Coverage Score', ascending=False)
        brand_summary.to_excel(writer, sheet_name='Summary by Brand')
        
        # Summary by city
        city_summary = df.groupby('city').agg({
            'coverage_score': 'mean',
            'num_outlets': 'sum',
            'brand': 'nunique',
            'market_share': 'mean'
        }).round(2)
        city_summary.columns = ['Avg Coverage Score', 'Total Outlets', 'Number of Brands', 'Avg Market Share %']
        city_summary = city_summary.sort_values('Avg Coverage Score', ascending=False)
        city_summary.to_excel(writer, sheet_name='Summary by City')
        
        # Summary by region
        region_summary = df.groupby('region').agg({
            'coverage_score': 'mean',
            'num_outlets': 'sum',
            'brand': 'nunique',
            'city': 'nunique'
        }).round(2)
        region_summary.columns = ['Avg Coverage Score', 'Total Outlets', 'Number of Brands', 'Number of Cities']
        region_summary = region_summary.sort_values('Avg Coverage Score', ascending=False)
        region_summary.to_excel(writer, sheet_name='Summary by Region')
        
        # Top performing locations
        top_locations = df.nlargest(50, 'coverage_score')[
            ['brand', 'city', 'region', 'coverage_score', 'num_outlets', 'market_share']
        ]
        top_locations.to_excel(writer, sheet_name='Top 50 Locations', index=False)
    
    print(f"✅ Brand coverage data exported to: {filename}")


def print_summary_statistics(df):
    """Print summary statistics about brand coverage."""
    print("\n" + "="*60)
    print("BRAND COVERAGE SUMMARY STATISTICS")
    print("="*60)
    
    print(f"\nTotal Locations: {len(df)}")
    print(f"Number of Brands: {df['brand'].nunique()}")
    print(f"Number of Cities: {df['city'].nunique()}")
    print(f"Number of Regions: {df['region'].nunique()}")
    
    print(f"\nCoverage Score Statistics:")
    print(f"  Average: {df['coverage_score'].mean():.2f}")
    print(f"  Median: {df['coverage_score'].median():.2f}")
    print(f"  Min: {df['coverage_score'].min():.2f}")
    print(f"  Max: {df['coverage_score'].max():.2f}")
    
    print(f"\nTotal Outlets: {df['num_outlets'].sum()}")
    print(f"Average Outlets per Location: {df['num_outlets'].mean():.2f}")
    
    print(f"\nAverage Market Share: {df['market_share'].mean():.2f}%")
    
    print("\nTop 5 Brands by Average Coverage:")
    top_brands = df.groupby('brand')['coverage_score'].mean().sort_values(ascending=False).head(5)
    for brand, score in top_brands.items():
        print(f"  {brand}: {score:.2f}")
    
    print("\nTop 5 Cities by Average Coverage:")
    top_cities = df.groupby('city')['coverage_score'].mean().sort_values(ascending=False).head(5)
    for city, score in top_cities.items():
        print(f"  {city}: {score:.2f}")
    
    print("\nCoverage Distribution by Region:")
    region_coverage = df.groupby('region')['coverage_score'].mean().sort_values(ascending=False)
    for region, score in region_coverage.items():
        print(f"  {region}: {score:.2f}")
    
    print("\n" + "="*60)


def main():
    """Main function to generate brand coverage map and analysis."""
    print("🚀 Starting Brand Coverage Map Generation...")
    
    # Generate brand coverage data
    print("\n📊 Generating brand coverage data...")
    df = generate_brand_data(config, n_locations=150, seed=42)
    
    # Print summary statistics
    print_summary_statistics(df)
    
    # Create brand coverage map
    print("\n🗺️  Creating brand coverage map...")
    create_brand_coverage_map(df, output_file='outputs/brand_coverage_map.html')
    
    # Export to Excel
    print("\n📁 Exporting data to Excel...")
    export_brand_data_to_excel(df, filename='outputs/brand_coverage_analysis.xlsx')
    
    print("\n✅ Brand coverage analysis complete!")
    print("\nGenerated files:")
    print("  - outputs/brand_coverage_map.html")
    print("  - outputs/brand_coverage_analysis.xlsx")
    print("\nOpen the HTML file in your browser to view the interactive map.")


if __name__ == '__main__':
    main()
