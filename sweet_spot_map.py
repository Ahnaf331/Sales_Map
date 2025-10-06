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


def generate_visit_data(config, n_visits=2000, seed=42):
    """Generate synthetic salesperson visit data for different locations."""
    random.seed(seed)
    np.random.seed(seed)
    
    cities = config['cities']
    city_names = [c[0] for c in cities]
    city_lats = [c[1] for c in cities]
    city_lons = [c[2] for c in cities]
    city_weights = np.array([c[3] for c in cities], dtype=float)
    city_weights /= city_weights.sum()
    
    # Define regions
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
    
    salespersons = [
        'Karim Ahmed', 'Rahim Hossain', 'Fatima Begum', 'Ayesha Khan', 'Jamal Uddin',
        'Nasrin Akter', 'Habib Rahman', 'Sultana Parvin', 'Mizanur Rahman', 'Shakil Ahmed'
    ]
    
    visits = []
    
    for i in range(n_visits):
        # Select a city
        city_idx = np.random.choice(len(city_names), p=city_weights)
        city_name = city_names[city_idx]
        base_lat = city_lats[city_idx]
        base_lon = city_lons[city_idx]
        
        # Add clustering around city centers (tighter for sweet spots)
        lat_offset = np.random.normal(0, 0.03)
        lon_offset = np.random.normal(0, 0.03)
        
        lat = base_lat + lat_offset
        lon = base_lon + lon_offset
        
        # Determine region
        region = next((r for r, cities_list in regions.items() if city_name in cities_list), 'Central')
        
        # Select salesperson
        salesperson = random.choice(salespersons)
        
        # Generate visit date (last 90 days)
        days_ago = random.randint(0, 90)
        visit_date = date.today() - timedelta(days=days_ago)
        
        # Visit details
        outlets_visited = random.randint(1, 8)
        duration_hours = round(random.uniform(0.5, 4.0), 1)
        
        visits.append({
            'visit_id': f'V{i+1:04d}',
            'salesperson': salesperson,
            'city': city_name,
            'region': region,
            'latitude': lat,
            'longitude': lon,
            'visit_date': visit_date,
            'outlets_visited': outlets_visited,
            'duration_hours': duration_hours
        })
    
    return pd.DataFrame(visits)


def identify_sweet_spots(df, grid_size=0.04, min_visits=8):
    """
    Identify sweet spots (high-visit areas) using grid-based clustering.
    
    Args:
        df: DataFrame with visit data
        grid_size: Size of grid cells in degrees (smaller = more granular)
        min_visits: Minimum visits to be considered a sweet spot
    
    Returns:
        DataFrame with sweet spot locations and visit counts
    """
    # Create grid cells
    df['lat_grid'] = (df['latitude'] / grid_size).round() * grid_size
    df['lon_grid'] = (df['longitude'] / grid_size).round() * grid_size
    
    # Count visits per grid cell
    sweet_spots = df.groupby(['lat_grid', 'lon_grid']).agg({
        'visit_id': 'count',
        'outlets_visited': 'sum',
        'salesperson': lambda x: x.nunique(),
        'city': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
        'region': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
        'duration_hours': 'sum'
    }).reset_index()
    
    sweet_spots.columns = ['latitude', 'longitude', 'visit_count', 'total_outlets', 
                           'unique_salespersons', 'city', 'region', 'total_hours']
    
    # Filter by minimum visits
    sweet_spots = sweet_spots[sweet_spots['visit_count'] >= min_visits]
    
    # Calculate intensity score (normalized)
    max_visits = sweet_spots['visit_count'].max()
    sweet_spots['intensity'] = sweet_spots['visit_count'] / max_visits
    
    return sweet_spots.sort_values('visit_count', ascending=False)


def create_sweet_spot_map(visits_df, sweet_spots_df, output_file='outputs/sweet_spot_map.html'):
    """Create an interactive map showing sweet spot locations."""
    
    # Initialize map centered on Bangladesh
    center_lat = 23.8103
    center_lon = 90.4125
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='CartoDB dark_matter',
        control_scale=True
    )
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; 
                left: 50%; 
                transform: translateX(-50%);
                width: 450px; 
                background-color: rgba(30, 30, 30, 0.95);
                border: 2px solid #FFD700;
                border-radius: 8px;
                z-index: 9999;
                padding: 12px 20px;
                color: white;
                font-family: Arial, sans-serif;
                box-shadow: 0 4px 6px rgba(0,0,0,0.5);">
        <h3 style="margin: 0; color: #FFD700; font-size: 22px; font-weight: 300; 
                   letter-spacing: 1px; text-align: center;">
            Sweet Spot Location Map
        </h3>
        <p style="margin: 5px 0 0 0; font-size: 13px; text-align: center; color: #ccc;">
            High-frequency salesperson visit areas
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add individual visit points with 5 different colors based on outlets visited
    for idx, visit in visits_df.iterrows():
        # Color based on outlets visited (1-8 range)
        outlets = visit['outlets_visited']
        if outlets >= 7:
            color = '#FF0000'  # Bright Red - Very High
        elif outlets >= 5:
            color = '#FF8C00'  # Orange - High
        elif outlets >= 4:
            color = '#FFFF00'  # Yellow - Medium
        elif outlets >= 2:
            color = '#00FF00'  # Green - Low
        else:
            color = '#8B00FF'  # Violet - Very Low
        
        folium.CircleMarker(
            location=[visit['latitude'], visit['longitude']],
            radius=3,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            opacity=0.8,
            weight=1,
            popup=f"<b>{visit['salesperson']}</b><br>City: {visit['city']}<br>Outlets: {outlets}<br>Duration: {visit['duration_hours']}h",
            tooltip=f"{visit['city']} - {outlets} outlets"
        ).add_to(m)
    
    # Add division labels
    divisions = {
        'DHAKA': [23.8103, 90.4125],
        'CHATTOGRAM': [22.3569, 91.7832],
        'SYLHET': [24.8949, 91.8687],
        'KHULNA': [22.8456, 89.5403],
        'RAJSHAHI': [24.3636, 88.6241],
        'RANGPUR': [25.7439, 89.2752],
        'BARISHAL': [22.7010, 90.3535],
        'MYMENSINGH': [24.7500, 90.3800]
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
                            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
                    {division}
                </div>
            ''')
        ).add_to(m)
    
    # Add legend with 5 colors for individual visits
    legend_html = '''
    <div style="position: fixed; 
                bottom: 40px; 
                left: 40px; 
                width: 240px; 
                background-color: rgba(30, 30, 30, 0.95);
                border: 2px solid #FFD700;
                border-radius: 8px;
                z-index: 9999;
                padding: 15px;
                color: white;
                font-family: Arial, sans-serif;
                font-size: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.5);">
        <h4 style="margin: 0 0 12px 0; color: #FFD700; font-size: 15px;">Visit Categories</h4>
        <p style="margin: 0 0 10px 0; font-size: 11px; color: #ccc;">Based on outlets visited per trip</p>
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <span style="display: inline-block; width: 12px; height: 12px; 
                         background-color: #FF0000; border-radius: 50%; 
                         margin-right: 8px; border: 1px solid #FF0000;"></span>
            <span><b>Very High</b> (7-8 outlets)</span>
        </div>
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <span style="display: inline-block; width: 12px; height: 12px; 
                         background-color: #FF8C00; border-radius: 50%; 
                         margin-right: 8px; border: 1px solid #FF8C00;"></span>
            <span><b>High</b> (5-6 outlets)</span>
        </div>
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <span style="display: inline-block; width: 12px; height: 12px; 
                         background-color: #FFFF00; border-radius: 50%; 
                         margin-right: 8px; border: 1px solid #FFFF00;"></span>
            <span><b>Medium</b> (4 outlets)</span>
        </div>
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <span style="display: inline-block; width: 12px; height: 12px; 
                         background-color: #00FF00; border-radius: 50%; 
                         margin-right: 8px; border: 1px solid #00FF00;"></span>
            <span><b>Low</b> (2-3 outlets)</span>
        </div>
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <span style="display: inline-block; width: 12px; height: 12px; 
                         background-color: #8B00FF; border-radius: 50%; 
                         margin-right: 8px; border: 1px solid #8B00FF;"></span>
            <span><b>Very Low</b> (1 outlet)</span>
        </div>
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #555; 
                    font-size: 10px; color: #999;">
            Each dot = 1 salesperson visit
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add statistics box with updated categories
    total_visits = len(visits_df)
    very_high = len(visits_df[visits_df['outlets_visited'] >= 7])
    high = len(visits_df[(visits_df['outlets_visited'] >= 5) & (visits_df['outlets_visited'] < 7)])
    medium = len(visits_df[visits_df['outlets_visited'] == 4])
    low = len(visits_df[(visits_df['outlets_visited'] >= 2) & (visits_df['outlets_visited'] < 4)])
    very_low = len(visits_df[visits_df['outlets_visited'] == 1])
    total_outlets = visits_df['outlets_visited'].sum()
    
    stats_html = f'''
    <div style="position: fixed; 
                bottom: 40px; 
                right: 40px; 
                width: 200px; 
                background-color: rgba(30, 30, 30, 0.95);
                border: 2px solid #FFD700;
                border-radius: 8px;
                z-index: 9999; 
                font-size: 12px;
                padding: 15px;
                color: white;
                font-family: Arial;
                box-shadow: 0 4px 6px rgba(0,0,0,0.5);">
        <h4 style="margin: 0 0 10px 0; color: #FFD700; font-size: 15px;">Quick Stats</h4>
        <p style="margin: 6px 0; color: #ddd;"><b>Total Visits:</b> {total_visits:,}</p>
        <p style="margin: 6px 0; color: #FF0000;"><b>Very High:</b> {very_high}</p>
        <p style="margin: 6px 0; color: #FF8C00;"><b>High:</b> {high}</p>
        <p style="margin: 6px 0; color: #FFFF00;"><b>Medium:</b> {medium}</p>
        <p style="margin: 6px 0; color: #00FF00;"><b>Low:</b> {low}</p>
        <p style="margin: 6px 0; color: #8B00FF;"><b>Very Low:</b> {very_low}</p>
        <p style="margin: 6px 0; color: #ddd;"><b>Total Outlets:</b> {total_outlets:,}</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(stats_html))
    
    # Add MiniMap for navigation
    minimap = MiniMap(toggle_display=True, tile_layer='CartoDB dark_matter')
    m.add_child(minimap)
    
    # Save map
    m.save(output_file)
    print(f"Sweet spot map saved to: {output_file}")
    
    return m


def export_to_excel(visits_df, sweet_spots_df, output_file='outputs/sweet_spot_analysis.xlsx'):
    """Export visit and sweet spot data to Excel with multiple sheets."""
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sweet spots summary (sorted by visit count)
        sweet_spots_export = sweet_spots_df.copy()
        sweet_spots_export = sweet_spots_export.sort_values('visit_count', ascending=False)
        sweet_spots_export.to_excel(writer, sheet_name='Sweet Spots', index=False)
        
        # All visits
        visits_export = visits_df.copy()
        visits_export['visit_date'] = visits_export['visit_date'].astype(str)
        visits_export = visits_export.sort_values('visit_date', ascending=False)
        visits_export.to_excel(writer, sheet_name='All Visits', index=False)
        
        # Visits by city
        city_summary = visits_df.groupby('city').agg({
            'visit_id': 'count',
            'outlets_visited': 'sum',
            'salesperson': lambda x: x.nunique(),
            'duration_hours': 'sum'
        }).reset_index()
        city_summary.columns = ['City', 'Total Visits', 'Total Outlets', 
                                'Unique Salespersons', 'Total Hours']
        city_summary = city_summary.sort_values('Total Visits', ascending=False)
        city_summary.to_excel(writer, sheet_name='By City', index=False)
        
        # Visits by salesperson
        sp_summary = visits_df.groupby('salesperson').agg({
            'visit_id': 'count',
            'outlets_visited': 'sum',
            'city': lambda x: x.nunique(),
            'duration_hours': 'sum'
        }).reset_index()
        sp_summary.columns = ['Salesperson', 'Total Visits', 'Total Outlets', 
                             'Cities Covered', 'Total Hours']
        sp_summary = sp_summary.sort_values('Total Visits', ascending=False)
        sp_summary.to_excel(writer, sheet_name='By Salesperson', index=False)
        
        # Visits by region
        region_summary = visits_df.groupby('region').agg({
            'visit_id': 'count',
            'outlets_visited': 'sum',
            'salesperson': lambda x: x.nunique(),
            'city': lambda x: x.nunique()
        }).reset_index()
        region_summary.columns = ['Region', 'Total Visits', 'Total Outlets', 
                                  'Unique Salespersons', 'Cities']
        region_summary = region_summary.sort_values('Total Visits', ascending=False)
        region_summary.to_excel(writer, sheet_name='By Region', index=False)
    
    print(f"Excel report exported to: {output_file}")


def print_summary_statistics(visits_df, sweet_spots_df):
    """Print summary statistics about sweet spots."""
    
    print("\n" + "="*70)
    print("SWEET SPOT ANALYSIS - SUMMARY STATISTICS")
    print("="*70)
    
    print(f"\nTotal Visits: {len(visits_df):,}")
    print(f"Total Outlets Visited: {visits_df['outlets_visited'].sum():,}")
    print(f"Total Visit Hours: {visits_df['duration_hours'].sum():,.1f}")
    
    print(f"\nVisit Distribution by Outlets Visited:")
    print(f"  Very High (7-8 outlets): {len(visits_df[visits_df['outlets_visited'] >= 7])}")
    print(f"  High (5-6 outlets): {len(visits_df[(visits_df['outlets_visited'] >= 5) & (visits_df['outlets_visited'] < 7)])}")
    print(f"  Medium (4 outlets): {len(visits_df[visits_df['outlets_visited'] == 4])}")
    print(f"  Low (2-3 outlets): {len(visits_df[(visits_df['outlets_visited'] >= 2) & (visits_df['outlets_visited'] < 4)])}")
    print(f"  Very Low (1 outlet): {len(visits_df[visits_df['outlets_visited'] == 1])}")
    
    print(f"\nCoverage:")
    print(f"  Cities Covered: {visits_df['city'].nunique()}")
    print(f"  Regions Covered: {visits_df['region'].nunique()}")
    print(f"  Active Salespersons: {visits_df['salesperson'].nunique()}")
    
    print(f"\nTop 5 Cities by Total Visits:")
    top_cities = visits_df.groupby('city')['visit_id'].count().sort_values(ascending=False).head()
    for city, count in top_cities.items():
        print(f"  {city}: {count} visits")
    
    print(f"\nTop 5 Salespersons by Visit Count:")
    top_sp = visits_df.groupby('salesperson')['visit_id'].count().sort_values(ascending=False).head()
    for sp, count in top_sp.items():
        outlets = visits_df[visits_df['salesperson'] == sp]['outlets_visited'].sum()
        print(f"  {sp}: {count} visits ({outlets} outlets)")
    
    print("\n" + "="*70)


def main():
    """Main function to generate sweet spot location map."""
    
    print("="*70)
    print("SWEET SPOT LOCATION MAP GENERATOR")
    print("="*70)
    
    # Generate visit data
    print("\nGenerating visit data...")
    visits_df = generate_visit_data(config, n_visits=2000)
    print(f"Generated {len(visits_df):,} visits")
    
    # Identify sweet spots
    print("\nIdentifying sweet spots...")
    sweet_spots_df = identify_sweet_spots(visits_df, grid_size=0.04, min_visits=8)
    print(f"Found {len(sweet_spots_df)} sweet spot locations")
    
    # Create map
    print("\nCreating interactive map...")
    create_sweet_spot_map(visits_df, sweet_spots_df, output_file='outputs/sweet_spot_map.html')
    
    # Export to Excel
    print("\nExporting data to Excel...")
    export_to_excel(visits_df, sweet_spots_df, output_file='outputs/sweet_spot_analysis.xlsx')
    
    # Print summary statistics
    print_summary_statistics(visits_df, sweet_spots_df)
    
    print("\nAnalysis complete!")
    print("  - Interactive Map: outputs/sweet_spot_map.html")
    print("  - Excel Report: outputs/sweet_spot_analysis.xlsx")


if __name__ == "__main__":
    main()