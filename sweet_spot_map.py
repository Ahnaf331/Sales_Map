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
    
    # Categorize sweet spots
    sweet_spots['category'] = pd.cut(
        sweet_spots['visit_count'],
        bins=[0, 15, 30, float('inf')],
        labels=['Medium Activity', 'High Activity', 'Hot Spot']
    )
    
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
    
    # Add sweet spot circles with varying sizes
    for idx, spot in sweet_spots_df.iterrows():
        # Calculate circle radius based on visit count (larger = more visits)
        base_radius = 2500  # Base radius in meters
        radius = base_radius * (0.5 + spot['intensity'] * 2.5)  # Scale from 0.5x to 3x
        
        # Determine color based on intensity
        if spot['visit_count'] >= 30:
            color = '#FFD700'  # Gold for hot spots
            fill_opacity = 0.7
            stroke_weight = 3
        elif spot['visit_count'] >= 15:
            color = '#FFA500'  # Orange for high activity
            fill_opacity = 0.6
            stroke_weight = 2
        else:
            color = '#FFDB58'  # Light yellow for medium activity
            fill_opacity = 0.5
            stroke_weight = 2
        
        # Create popup content
        popup_html = f"""
        <div style="font-family: Arial; width: 240px; color: #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0; 
                       padding-bottom: 8px; border-bottom: 2px solid #FFD700;">
                🎯 Sweet Spot
            </h4>
            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 4px;"><b>Location:</b></td>
                    <td style="padding: 4px;">{spot['city']}</td>
                </tr>
                <tr>
                    <td style="padding: 4px;"><b>Region:</b></td>
                    <td style="padding: 4px;">{spot['region']}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 4px;"><b>Total Visits:</b></td>
                    <td style="padding: 4px;"><b>{spot['visit_count']}</b></td>
                </tr>
                <tr>
                    <td style="padding: 4px;"><b>Outlets Visited:</b></td>
                    <td style="padding: 4px;">{spot['total_outlets']}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 4px;"><b>Salespersons:</b></td>
                    <td style="padding: 4px;">{spot['unique_salespersons']}</td>
                </tr>
                <tr>
                    <td style="padding: 4px;"><b>Total Hours:</b></td>
                    <td style="padding: 4px;">{spot['total_hours']:.1f}h</td>
                </tr>
                <tr style="background-color: #fff3cd;">
                    <td style="padding: 4px;"><b>Category:</b></td>
                    <td style="padding: 4px;"><b>{spot['category']}</b></td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 4px;"><b>Intensity:</b></td>
                    <td style="padding: 4px;">{spot['intensity']:.0%}</td>
                </tr>
            </table>
        </div>
        """
        
        # Add circle marker for sweet spot
        folium.Circle(
            location=[spot['latitude'], spot['longitude']],
            radius=radius,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=fill_opacity,
            opacity=0.9,
            weight=stroke_weight,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"<b>{spot['city']}</b><br>{spot['visit_count']} visits"
        ).add_to(m)
    
    # Add individual visit points (smaller, semi-transparent)
    for idx, visit in visits_df.iterrows():
        folium.CircleMarker(
            location=[visit['latitude'], visit['longitude']],
            radius=1.5,
            color='#FFD700',
            fill=True,
            fillColor='#FFD700',
            fillOpacity=0.25,
            opacity=0.25,
            weight=0.5
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
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 40px; 
                left: 40px; 
                width: 220px; 
                background-color: rgba(30, 30, 30, 0.95);
                border: 2px solid #FFD700;
                border-radius: 8px;
                z-index: 9999;
                padding: 15px;
                color: white;
                font-family: Arial, sans-serif;
                font-size: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.5);">
        <h4 style="margin: 0 0 12px 0; color: #FFD700; font-size: 15px;">Legend</h4>
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <span style="display: inline-block; width: 22px; height: 22px; 
                         background-color: #FFD700; border-radius: 50%; 
                         opacity: 0.7; margin-right: 8px; border: 2px solid #FFD700;"></span>
            <span><b>Hot Spot</b> (30+ visits)</span>
        </div>
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <span style="display: inline-block; width: 18px; height: 18px; 
                         background-color: #FFA500; border-radius: 50%; 
                         opacity: 0.6; margin-right: 10px; border: 2px solid #FFA500;"></span>
            <span><b>High Activity</b> (15-29)</span>
        </div>
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <span style="display: inline-block; width: 14px; height: 14px; 
                         background-color: #FFDB58; border-radius: 50%; 
                         opacity: 0.5; margin-right: 12px; border: 2px solid #FFDB58;"></span>
            <span><b>Medium</b> (8-14 visits)</span>
        </div>
        <div style="margin: 12px 0 8px 0; padding-top: 10px; border-top: 1px solid #555;">
            <span style="display: inline-block; width: 8px; height: 8px; 
                         background-color: #FFD700; border-radius: 50%; 
                         opacity: 0.25; margin-right: 8px;"></span>
            <span style="color: #ccc;">Individual Visits</span>
        </div>
        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #555; 
                    font-size: 10px; color: #999;">
            Circle size = Visit frequency
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add statistics box
    total_visits = len(visits_df)
    hot_spots = len(sweet_spots_df[sweet_spots_df['visit_count'] >= 30])
    high_activity = len(sweet_spots_df[(sweet_spots_df['visit_count'] >= 15) & (sweet_spots_df['visit_count'] < 30)])
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
        <p style="margin: 6px 0; color: #ddd;"><b>Sweet Spots:</b> {len(sweet_spots_df)}</p>
        <p style="margin: 6px 0; color: #FFD700;"><b>Hot Spots:</b> {hot_spots}</p>
        <p style="margin: 6px 0; color: #FFA500;"><b>High Activity:</b> {high_activity}</p>
        <p style="margin: 6px 0; color: #ddd;"><b>Outlets Visited:</b> {total_outlets:,}</p>
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
    
    print(f"\nSweet Spots Identified: {len(sweet_spots_df)}")
    print(f"  Hot Spots (30+ visits): {len(sweet_spots_df[sweet_spots_df['visit_count'] >= 30])}")
    print(f"  High Activity (15-29 visits): {len(sweet_spots_df[(sweet_spots_df['visit_count'] >= 15) & (sweet_spots_df['visit_count'] < 30)])}")
    print(f"  Medium Activity (8-14 visits): {len(sweet_spots_df[sweet_spots_df['visit_count'] < 15])}")
    
    print(f"\nCoverage:")
    print(f"  Cities Covered: {visits_df['city'].nunique()}")
    print(f"  Regions Covered: {visits_df['region'].nunique()}")
    print(f"  Active Salespersons: {visits_df['salesperson'].nunique()}")
    
    print(f"\nTop 10 Sweet Spots by Visit Count:")
    for idx, spot in sweet_spots_df.head(10).iterrows():
        print(f"  {spot['city']:18} | Visits: {spot['visit_count']:3} | "
              f"Outlets: {spot['total_outlets']:4} | Category: {spot['category']}")
    
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