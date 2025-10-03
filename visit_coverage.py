import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, MiniMap
import random
import json
import os
from datetime import date, datetime, timedelta

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)


def generate_visit_data(config, n_visits=800, seed=42):
    """Generate synthetic salesperson visit data for different locations."""
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
    
    # Define salesperson names
    salespersons = [
        'Karim Ahmed', 'Rahim Hossain', 'Fatima Begum', 'Ayesha Khan', 'Jamal Uddin',
        'Nasrin Akter', 'Habib Rahman', 'Sultana Parvin', 'Mizanur Rahman', 'Sharmin Akter',
        'Rafiq Islam', 'Roksana Begum', 'Shakil Ahmed', 'Taslima Khatun', 'Masud Rana'
    ]
    
    visits = []
    
    for i in range(n_visits):
        # Select a city based on weights
        city_idx = np.random.choice(len(city_names), p=city_weights)
        city_name = city_names[city_idx]
        base_lat = city_lats[city_idx]
        base_lon = city_lons[city_idx]
        
        # Add some random offset to create spread around the city
        lat_offset = np.random.normal(0, 0.05)
        lon_offset = np.random.normal(0, 0.05)
        
        lat = base_lat + lat_offset
        lon = base_lon + lon_offset
        
        # Determine region
        region = 'Central'  # default
        for reg, cities_in_reg in regions.items():
            if city_name in cities_in_reg:
                region = reg
                break
        
        # Assign salesperson (some cities have preferred salespersons)
        salesperson = random.choice(salespersons)
        
        # Generate visit coverage value (1-6)
        # Higher values for major cities, lower for smaller areas
        if city_weights[city_idx] > 0.15:
            coverage_value = random.choices([4, 5, 6], weights=[0.3, 0.4, 0.3])[0]
        elif city_weights[city_idx] > 0.08:
            coverage_value = random.choices([3, 4, 5], weights=[0.3, 0.4, 0.3])[0]
        else:
            coverage_value = random.choices([1, 2, 3, 4], weights=[0.2, 0.3, 0.3, 0.2])[0]
        
        # Generate visit date (last 90 days)
        days_ago = random.randint(0, 90)
        visit_date = date.today() - timedelta(days=days_ago)
        
        # Generate visit details
        outlets_visited = random.randint(1, 8)
        duration_hours = round(random.uniform(0.5, 6.0), 1)
        orders_taken = random.randint(0, outlets_visited)
        
        visits.append({
            'visit_id': f'V{i+1:04d}',
            'salesperson': salesperson,
            'city': city_name,
            'region': region,
            'latitude': lat,
            'longitude': lon,
            'coverage_value': coverage_value,
            'visit_date': visit_date,
            'outlets_visited': outlets_visited,
            'duration_hours': duration_hours,
            'orders_taken': orders_taken
        })
    
    df = pd.DataFrame(visits)
    return df


def create_visit_coverage_map(df, output_file='outputs/visit_coverage_map.html'):
    """Create an interactive visit coverage heat map with dark theme."""
    
    # Calculate center of Bangladesh
    center_lat = 23.685
    center_lon = 90.3563
    
    # Create base map with dark theme
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='CartoDB dark_matter',
        attr='CartoDB'
    )
    
    # Prepare heat map data
    heat_data = []
    for idx, row in df.iterrows():
        # Weight by coverage value for heat intensity
        heat_data.append([row['latitude'], row['longitude'], row['coverage_value'] / 6.0])
    
    # Add heat map layer
    HeatMap(
        heat_data,
        min_opacity=0.2,
        max_opacity=0.8,
        radius=15,
        blur=20,
        gradient={
            0.0: '#440154',  # Dark purple
            0.2: '#3b528b',  # Blue
            0.4: '#21918c',  # Teal
            0.6: '#5ec962',  # Green
            0.8: '#fde725'   # Yellow
        }
    ).add_to(m)
    
    # Define colors for coverage values
    def get_color(coverage_value):
        if coverage_value <= 2:
            return '#ff4444'  # Red - Low coverage
        elif coverage_value <= 4:
            return '#ff9944'  # Orange - Medium coverage
        else:
            return '#ffdd44'  # Yellow - High coverage
    
    # Add individual visit markers
    for idx, row in df.iterrows():
        color = get_color(row['coverage_value'])
        
        # Create popup content
        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Visit Details</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr>
                    <td style="padding: 3px;"><b>Visit ID:</b></td>
                    <td style="padding: 3px;">{row['visit_id']}</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Salesperson:</b></td>
                    <td style="padding: 3px;">{row['salesperson']}</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>City:</b></td>
                    <td style="padding: 3px;">{row['city']}</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Region:</b></td>
                    <td style="padding: 3px;">{row['region']}</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Coverage Value:</b></td>
                    <td style="padding: 3px;">{row['coverage_value']}/6</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Visit Date:</b></td>
                    <td style="padding: 3px;">{row['visit_date']}</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Outlets Visited:</b></td>
                    <td style="padding: 3px;">{row['outlets_visited']}</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Duration:</b></td>
                    <td style="padding: 3px;">{row['duration_hours']} hours</td>
                </tr>
                <tr>
                    <td style="padding: 3px;"><b>Orders Taken:</b></td>
                    <td style="padding: 3px;">{row['orders_taken']}</td>
                </tr>
            </table>
        </div>
        """
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=4,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=1
        ).add_to(m)
    
    # Add division labels
    divisions = [
        ('Dhaka', 23.8103, 90.4125),
        ('Chattogram', 22.3569, 91.7832),
        ('Sylhet', 24.8949, 91.8687),
        ('Khulna', 22.8456, 89.5403),
        ('Rajshahi', 24.3636, 88.6241),
        ('Rangpur', 25.7439, 89.2752),
        ('Barishal', 22.7010, 90.3535),
        ('Mymensingh', 24.7500, 90.3800)
    ]
    
    for div_name, div_lat, div_lon in divisions:
        folium.Marker(
            location=[div_lat, div_lon],
            icon=folium.DivIcon(
                html=f'''
                <div style="
                    font-size: 11px;
                    color: white;
                    font-weight: bold;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
                    white-space: nowrap;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                ">{div_name} DIVISION</div>
                '''
            )
        ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="
        position: fixed;
        top: 10px;
        right: 10px;
        width: 280px;
        background-color: rgba(255, 255, 255, 0.95);
        border: 2px solid #333;
        border-radius: 8px;
        padding: 15px;
        font-family: Arial, sans-serif;
        z-index: 9999;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    ">
        <h3 style="margin: 0 0 12px 0; color: #2c3e50; font-size: 16px; text-align: center;">
            Visit Coverage Heat Map<br>
            <span style="font-size: 13px; font-weight: normal;">Value range (1 to 6)</span>
        </h3>
        <div style="margin-bottom: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 20px; height: 20px; background-color: #ff4444; 
                    border-radius: 50%; margin-right: 10px; border: 1px solid #333;"></div>
                <span style="font-size: 13px; color: #333;"><b>Low Coverage</b> (1-2)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 20px; height: 20px; background-color: #ff9944; 
                    border-radius: 50%; margin-right: 10px; border: 1px solid #333;"></div>
                <span style="font-size: 13px; color: #333;"><b>Medium Coverage</b> (3-4)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 20px; height: 20px; background-color: #ffdd44; 
                    border-radius: 50%; margin-right: 10px; border: 1px solid #333;"></div>
                <span style="font-size: 13px; color: #333;"><b>High Coverage</b> (5-6)</span>
            </div>
        </div>
        <hr style="margin: 10px 0; border: none; border-top: 1px solid #ccc;">
        <div style="font-size: 11px; color: #666; text-align: center;">
            Heat intensity shows visit density
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add MiniMap for navigation
    minimap = MiniMap(
        tile_layer='CartoDB dark_matter',
        toggle_display=True,
        position='bottomleft',
        width=150,
        height=150,
        zoom_level_offset=-5
    )
    m.add_child(minimap)
    
    # Save map
    m.save(output_file)
    print(f"Visit coverage map saved to: {output_file}")
    
    return m


def export_visit_data_to_excel(df, filename='outputs/visit_coverage_analysis.xlsx'):
    """Export visit data to Excel with summary sheets."""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Main visit data
        df_export = df.copy()
        df_export['visit_date'] = df_export['visit_date'].astype(str)
        df_export.to_excel(writer, sheet_name='All Visits', index=False)
        
        # Summary by salesperson
        salesperson_summary = df.groupby('salesperson').agg({
            'visit_id': 'count',
            'coverage_value': 'mean',
            'outlets_visited': 'sum',
            'duration_hours': 'sum',
            'orders_taken': 'sum'
        }).round(2)
        salesperson_summary.columns = ['Total Visits', 'Avg Coverage', 'Total Outlets', 'Total Hours', 'Total Orders']
        salesperson_summary = salesperson_summary.sort_values('Total Visits', ascending=False)
        salesperson_summary.to_excel(writer, sheet_name='By Salesperson')
        
        # Summary by city
        city_summary = df.groupby('city').agg({
            'visit_id': 'count',
            'coverage_value': 'mean',
            'outlets_visited': 'sum',
            'salesperson': lambda x: x.nunique()
        }).round(2)
        city_summary.columns = ['Total Visits', 'Avg Coverage', 'Total Outlets', 'Unique Salespersons']
        city_summary = city_summary.sort_values('Total Visits', ascending=False)
        city_summary.to_excel(writer, sheet_name='By City')
        
        # Summary by region
        region_summary = df.groupby('region').agg({
            'visit_id': 'count',
            'coverage_value': 'mean',
            'outlets_visited': 'sum',
            'duration_hours': 'sum',
            'salesperson': lambda x: x.nunique()
        }).round(2)
        region_summary.columns = ['Total Visits', 'Avg Coverage', 'Total Outlets', 'Total Hours', 'Unique Salespersons']
        region_summary = region_summary.sort_values('Total Visits', ascending=False)
        region_summary.to_excel(writer, sheet_name='By Region')
        
        # Coverage value distribution
        coverage_dist = df['coverage_value'].value_counts().sort_index()
        coverage_dist.name = 'Visit Count'
        coverage_dist.index.name = 'Coverage Value'
        coverage_dist.to_excel(writer, sheet_name='Coverage Distribution')
        
    print(f"Visit data exported to: {filename}")


def print_summary_statistics(df):
    """Print summary statistics about visit coverage."""
    
    print("\n" + "="*60)
    print("VISIT COVERAGE SUMMARY STATISTICS")
    print("="*60)
    
    print(f"\nTotal Visits: {len(df)}")
    print(f"Date Range: {df['visit_date'].min()} to {df['visit_date'].max()}")
    print(f"Total Salespersons: {df['salesperson'].nunique()}")
    print(f"Cities Covered: {df['city'].nunique()}")
    print(f"Regions Covered: {df['region'].nunique()}")
    
    print(f"\nAverage Coverage Value: {df['coverage_value'].mean():.2f}/6")
    print(f"Total Outlets Visited: {df['outlets_visited'].sum()}")
    print(f"Total Visit Hours: {df['duration_hours'].sum():.1f}")
    print(f"Total Orders Taken: {df['orders_taken'].sum()}")
    
    print("\nCoverage Value Distribution:")
    for val in sorted(df['coverage_value'].unique()):
        count = len(df[df['coverage_value'] == val])
        pct = (count / len(df)) * 100
        print(f"  Value {val}: {count} visits ({pct:.1f}%)")
    
    print("\nTop 5 Cities by Visit Count:")
    top_cities = df['city'].value_counts().head()
    for city, count in top_cities.items():
        avg_coverage = df[df['city'] == city]['coverage_value'].mean()
        print(f"  {city}: {count} visits (Avg Coverage: {avg_coverage:.2f})")
    
    print("\nTop 5 Salespersons by Visit Count:")
    top_sales = df['salesperson'].value_counts().head()
    for person, count in top_sales.items():
        avg_coverage = df[df['salesperson'] == person]['coverage_value'].mean()
        total_orders = df[df['salesperson'] == person]['orders_taken'].sum()
        print(f"  {person}: {count} visits (Avg Coverage: {avg_coverage:.2f}, Orders: {total_orders})")
    
    print("\nRegional Distribution:")
    region_stats = df.groupby('region').agg({
        'visit_id': 'count',
        'coverage_value': 'mean'
    }).round(2)
    for region, row in region_stats.iterrows():
        print(f"  {region}: {int(row['visit_id'])} visits (Avg Coverage: {row['coverage_value']:.2f})")
    
    print("\n" + "="*60)


def main():
    """Main function to generate visit coverage map and analysis."""
    
    print("Generating salesperson visit coverage data...")
    df = generate_visit_data(config, n_visits=800, seed=42)
    
    print("Creating visit coverage heat map...")
    create_visit_coverage_map(df, output_file='outputs/visit_coverage_map.html')
    
    print("Exporting visit data to Excel...")
    export_visit_data_to_excel(df, filename='outputs/visit_coverage_analysis.xlsx')
    
    print_summary_statistics(df)
    
    print("\n✓ Visit coverage analysis complete!")
    print(f"  - Map: outputs/visit_coverage_map.html")
    print(f"  - Data: outputs/visit_coverage_analysis.xlsx")


if __name__ == '__main__':
    main()
