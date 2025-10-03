import pandas as pd
import numpy as np
import folium
from folium.plugins import MiniMap, MarkerCluster
import random
import json
import os
from datetime import date, datetime, timedelta

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)


def generate_not_ordered_outlets(config, n_outlets=1500, seed=42):
    """Generate synthetic data for outlets that haven't placed orders."""
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
    
    # Outlet types
    outlet_types = ['Retail Shop', 'Grocery Store', 'Pharmacy', 'Department Store', 
                    'Supermarket', 'Convenience Store', 'Mini Market']
    
    # Reasons for not ordering
    no_order_reasons = [
        'Not contacted yet',
        'Price concerns',
        'Stock issues',
        'Competitor preference',
        'Credit terms disagreement',
        'Quality concerns',
        'Delivery issues',
        'New outlet - prospecting',
        'Seasonal business',
        'Low demand area'
    ]
    
    outlets = []
    
    for outlet_id in range(1, n_outlets + 1):
        # Select city
        city_idx = np.random.choice(len(city_names), p=city_weights)
        city_name = city_names[city_idx]
        base_lat = city_lats[city_idx]
        base_lon = city_lons[city_idx]
        
        # Add spatial variation (tighter clustering for more density)
        lat = base_lat + np.random.normal(0, 0.04)
        lon = base_lon + np.random.normal(0, 0.05)
        
        # Determine region
        region = next((r for r, cities_list in regions.items() if city_name in cities_list), 'Central')
        
        # Outlet details
        outlet_type = random.choice(outlet_types)
        outlet_size = random.choice(['Small', 'Medium', 'Large'])
        
        # Days since last contact (0-180 days)
        days_since_contact = random.randint(0, 180)
        last_contact_date = date.today() - timedelta(days=days_since_contact)
        
        # Priority score (1-10, higher = more urgent to follow up)
        # Larger outlets, recent contacts, and major cities get higher priority
        priority_score = 5  # base
        if outlet_size == 'Large':
            priority_score += 3
        elif outlet_size == 'Medium':
            priority_score += 1
        if city_weights[city_idx] > 0.15:  # Major city
            priority_score += 2
        if days_since_contact < 30:  # Recent contact
            priority_score += 2
        elif days_since_contact > 90:  # Old contact
            priority_score -= 2
        
        priority_score = max(1, min(10, priority_score + random.randint(-1, 1)))
        
        # Potential monthly value estimate
        if outlet_size == 'Large':
            potential_value = random.randint(50000, 150000)
        elif outlet_size == 'Medium':
            potential_value = random.randint(20000, 60000)
        else:
            potential_value = random.randint(5000, 25000)
        
        # Number of visits made
        visits_made = random.randint(0, 5)
        
        # Reason for not ordering
        reason = random.choice(no_order_reasons)
        
        # Contact person
        contact_person = f"Contact-{outlet_id}"
        
        # Assigned salesperson
        salesperson = random.choice([
            'Karim Ahmed', 'Rahim Hossain', 'Fatima Begum', 'Ayesha Khan', 'Jamal Uddin',
            'Nasrin Akter', 'Habib Rahman', 'Sultana Parvin', 'Mizanur Rahman', 'Shakil Ahmed'
        ])
        
        outlets.append({
            'outlet_id': f'NO{outlet_id:04d}',
            'outlet_name': f'{outlet_type} - {city_name} {outlet_id}',
            'outlet_type': outlet_type,
            'outlet_size': outlet_size,
            'city': city_name,
            'region': region,
            'latitude': lat,
            'longitude': lon,
            'priority_score': priority_score,
            'potential_monthly_value': potential_value,
            'last_contact_date': last_contact_date,
            'days_since_contact': days_since_contact,
            'visits_made': visits_made,
            'no_order_reason': reason,
            'contact_person': contact_person,
            'assigned_salesperson': salesperson
        })
    
    return pd.DataFrame(outlets)


def create_not_ordered_map(df, output_file='outputs/not_ordered_outlets_map.html'):
    """Create an interactive map showing outlets that haven't ordered."""
    
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
    
    # Priority-based colors (matching your screenshot's yellow/orange scheme)
    def get_priority_color(priority):
        if priority >= 8:
            return '#FFD700'  # Gold - High priority
        elif priority >= 5:
            return '#FFA500'  # Orange - Medium priority
        else:
            return '#FF8C00'  # Dark orange - Low priority
    
    # Size based on potential value
    max_value = df['potential_monthly_value'].max()
    min_value = df['potential_monthly_value'].min()
    
    # Add markers with clustering for better performance
    marker_cluster = MarkerCluster(name='Not Ordered Outlets').add_to(m)
    
    for idx, row in df.iterrows():
        # Calculate marker size based on potential value
        normalized_value = (row['potential_monthly_value'] - min_value) / (max_value - min_value)
        radius = 5 + (normalized_value ** 0.5) * 15  # Range from 5 to 20
        
        color = get_priority_color(row['priority_score'])
        
        # Create detailed popup
        popup_html = f"""
        <div style='font-family: Arial; font-size: 12px; min-width: 280px;'>
            <h4 style='margin: 0 0 10px 0; color: #333; border-bottom: 2px solid {color};
                       padding-bottom: 5px;'>{row['outlet_name']}</h4>
            <table style='width: 100%; border-collapse: collapse;'>
                <tr>
                    <td style='padding: 3px 0;'><b>Outlet ID:</b></td>
                    <td style='padding: 3px 0;'>{row['outlet_id']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Type:</b></td>
                    <td style='padding: 3px 0;'>{row['outlet_type']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Size:</b></td>
                    <td style='padding: 3px 0;'>{row['outlet_size']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>City:</b></td>
                    <td style='padding: 3px 0;'>{row['city']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Region:</b></td>
                    <td style='padding: 3px 0;'>{row['region']}</td>
                </tr>
                <tr style='background-color: #fff3cd;'>
                    <td style='padding: 3px 0;'><b>Priority:</b></td>
                    <td style='padding: 3px 0;'><b>{row['priority_score']}/10</b></td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Potential Value:</b></td>
                    <td style='padding: 3px 0;'>৳{row['potential_monthly_value']:,}/month</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Last Contact:</b></td>
                    <td style='padding: 3px 0;'>{row['last_contact_date']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Days Since:</b></td>
                    <td style='padding: 3px 0;'>{row['days_since_contact']} days</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Visits Made:</b></td>
                    <td style='padding: 3px 0;'>{row['visits_made']}</td>
                </tr>
                <tr style='background-color: #f8d7da;'>
                    <td style='padding: 3px 0;'><b>Reason:</b></td>
                    <td style='padding: 3px 0;'>{row['no_order_reason']}</td>
                </tr>
                <tr>
                    <td style='padding: 3px 0;'><b>Salesperson:</b></td>
                    <td style='padding: 3px 0;'>{row['assigned_salesperson']}</td>
                </tr>
            </table>
        </div>
        """
        
        # Add circle marker to cluster
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{row['outlet_name']} (Priority: {row['priority_score']})",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2,
            opacity=0.9
        ).add_to(marker_cluster)
    
    # Add division labels
    divisions = {
        'DHAKA': [23.8103, 90.4125],
        'CHATTOGRAM\nDIVISION': [22.3569, 91.7832],
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
                width: 450px; 
                height: 65px; 
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 5px;
                z-index: 9999; 
                text-align: center;
                padding: 10px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0 0 5px 0; 
                   font-family: Arial, sans-serif; 
                   font-size: 24px;
                   color: #333;
                   font-weight: 300;
                   letter-spacing: 1px;">
            Not Ordered Outlet Coverage Map
        </h3>
        <p style="margin: 0; font-size: 13px; color: #666;">
            Outlets that haven't placed orders yet
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 30px; 
                left: 30px; 
                width: 240px; 
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 5px;
                z-index: 9999; 
                font-size: 13px;
                padding: 15px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 12px 0; font-family: Arial;">Priority Level</h4>
        <div style="margin: 8px 0;">
            <i style="background: #FFD700; 
                      width: 20px; 
                      height: 20px; 
                      float: left; 
                      margin-right: 10px;
                      border-radius: 50%;
                      border: 2px solid #FFD700;"></i>
            <span style="line-height: 20px;"><b>High Priority</b> (8-10)</span>
        </div>
        <div style="margin: 8px 0; clear: both;">
            <i style="background: #FFA500; 
                      width: 20px; 
                      height: 20px; 
                      float: left; 
                      margin-right: 10px;
                      border-radius: 50%;
                      border: 2px solid #FFA500;"></i>
            <span style="line-height: 20px;"><b>Medium Priority</b> (5-7)</span>
        </div>
        <div style="margin: 8px 0; clear: both;">
            <i style="background: #FF8C00; 
                      width: 20px; 
                      height: 20px; 
                      float: left; 
                      margin-right: 10px;
                      border-radius: 50%;
                      border: 2px solid #FF8C00;"></i>
            <span style="line-height: 20px;"><b>Low Priority</b> (1-4)</span>
        </div>
        <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd; 
                    font-size: 11px; color: #666;">
            Circle size = Potential monthly value
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add statistics box
    total_outlets = len(df)
    high_priority = len(df[df['priority_score'] >= 8])
    total_potential = df['potential_monthly_value'].sum()
    
    stats_html = f'''
    <div style="position: fixed; 
                bottom: 30px; 
                right: 30px; 
                width: 220px; 
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 5px;
                z-index: 9999; 
                font-size: 12px;
                padding: 15px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 10px 0; font-family: Arial;">Quick Stats</h4>
        <p style="margin: 5px 0;"><b>Total Outlets:</b> {total_outlets}</p>
        <p style="margin: 5px 0;"><b>High Priority:</b> {high_priority}</p>
        <p style="margin: 5px 0;"><b>Total Potential:</b><br>৳{total_potential:,.0f}/month</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(stats_html))
    
    # Add MiniMap
    minimap = MiniMap(
        toggle_display=True,
        position='bottomright'
    )
    m.add_child(minimap)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    m.save(output_file)
    print(f"Not ordered outlets map saved to: {output_file}")
    
    return m


def export_to_excel(df, filename='outputs/not_ordered_outlets_analysis.xlsx'):
    """Export not ordered outlets data to Excel with analysis sheets."""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Main data sheet
        df_export = df.copy()
        df_export['last_contact_date'] = df_export['last_contact_date'].astype(str)
        df_export = df_export.sort_values(['priority_score', 'potential_monthly_value'], 
                                          ascending=[False, False])
        df_export.to_excel(writer, sheet_name='All Outlets', index=False)
        
        # High priority outlets
        high_priority = df[df['priority_score'] >= 8].sort_values('potential_monthly_value', ascending=False)
        high_priority_export = high_priority.copy()
        high_priority_export['last_contact_date'] = high_priority_export['last_contact_date'].astype(str)
        high_priority_export.to_excel(writer, sheet_name='High Priority', index=False)
        
        # Summary by region
        region_summary = df.groupby('region').agg({
            'outlet_id': 'count',
            'priority_score': 'mean',
            'potential_monthly_value': 'sum',
            'days_since_contact': 'mean',
            'visits_made': 'sum'
        }).round(2)
        region_summary.columns = ['Total Outlets', 'Avg Priority', 'Total Potential (BDT)', 
                                  'Avg Days Since Contact', 'Total Visits']
        region_summary = region_summary.sort_values('Total Potential (BDT)', ascending=False)
        region_summary.to_excel(writer, sheet_name='By Region')
        
        # Summary by city
        city_summary = df.groupby('city').agg({
            'outlet_id': 'count',
            'priority_score': 'mean',
            'potential_monthly_value': 'sum'
        }).round(2)
        city_summary.columns = ['Total Outlets', 'Avg Priority', 'Total Potential (BDT)']
        city_summary = city_summary.sort_values('Total Outlets', ascending=False).head(20)
        city_summary.to_excel(writer, sheet_name='Top 20 Cities')
        
        # Summary by reason
        reason_summary = df.groupby('no_order_reason').agg({
            'outlet_id': 'count',
            'potential_monthly_value': 'sum',
            'priority_score': 'mean'
        }).round(2)
        reason_summary.columns = ['Outlet Count', 'Total Potential (BDT)', 'Avg Priority']
        reason_summary = reason_summary.sort_values('Outlet Count', ascending=False)
        reason_summary.to_excel(writer, sheet_name='By Reason')
        
        # Summary by salesperson
        salesperson_summary = df.groupby('assigned_salesperson').agg({
            'outlet_id': 'count',
            'potential_monthly_value': 'sum',
            'priority_score': 'mean',
            'visits_made': 'sum'
        }).round(2)
        salesperson_summary.columns = ['Assigned Outlets', 'Total Potential (BDT)', 
                                       'Avg Priority', 'Total Visits Made']
        salesperson_summary = salesperson_summary.sort_values('Assigned Outlets', ascending=False)
        salesperson_summary.to_excel(writer, sheet_name='By Salesperson')
        
        # Urgency analysis (old contacts)
        urgent = df[df['days_since_contact'] > 60].sort_values('days_since_contact', ascending=False)
        urgent_export = urgent[['outlet_id', 'outlet_name', 'city', 'region', 'priority_score',
                               'potential_monthly_value', 'days_since_contact', 'no_order_reason',
                               'assigned_salesperson']].copy()
        urgent_export['last_contact_date'] = urgent['last_contact_date'].astype(str)
        urgent_export.to_excel(writer, sheet_name='Urgent Follow-up', index=False)
    
    print(f"Excel analysis exported to: {filename}")


def print_summary_statistics(df):
    """Print summary statistics about not ordered outlets."""
    
    print("\n" + "="*70)
    print("NOT ORDERED OUTLETS - SUMMARY STATISTICS")
    print("="*70)
    
    print(f"\nTotal Outlets Not Ordered: {len(df)}")
    print(f"Cities Covered: {df['city'].nunique()}")
    print(f"Regions Covered: {df['region'].nunique()}")
    
    print(f"\nPotential Monthly Revenue: ৳{df['potential_monthly_value'].sum():,.0f}")
    print(f"Average Potential per Outlet: ৳{df['potential_monthly_value'].mean():,.0f}")
    
    print(f"\nPriority Distribution:")
    print(f"  High Priority (8-10): {len(df[df['priority_score'] >= 8])} outlets")
    print(f"  Medium Priority (5-7): {len(df[(df['priority_score'] >= 5) & (df['priority_score'] < 8)])} outlets")
    print(f"  Low Priority (1-4): {len(df[df['priority_score'] < 5])} outlets")
    
    print(f"\nContact Analysis:")
    print(f"  Not contacted yet: {len(df[df['days_since_contact'] == 0])} outlets")
    print(f"  Contacted within 30 days: {len(df[df['days_since_contact'] <= 30])} outlets")
    print(f"  Contacted 31-60 days ago: {len(df[(df['days_since_contact'] > 30) & (df['days_since_contact'] <= 60)])} outlets")
    print(f"  Contacted 61-90 days ago: {len(df[(df['days_since_contact'] > 60) & (df['days_since_contact'] <= 90)])} outlets")
    print(f"  Contacted >90 days ago: {len(df[df['days_since_contact'] > 90])} outlets")
    
    print(f"\nTop 5 Regions by Outlet Count:")
    top_regions = df['region'].value_counts().head()
    for region, count in top_regions.items():
        potential = df[df['region'] == region]['potential_monthly_value'].sum()
        print(f"  {region}: {count} outlets (Potential: ৳{potential:,.0f})")
    
    print(f"\nTop 5 Cities by Outlet Count:")
    top_cities = df['city'].value_counts().head()
    for city, count in top_cities.items():
        potential = df[df['city'] == city]['potential_monthly_value'].sum()
        print(f"  {city}: {count} outlets (Potential: ৳{potential:,.0f})")
    
    print(f"\nTop 5 Reasons for Not Ordering:")
    top_reasons = df['no_order_reason'].value_counts().head()
    for reason, count in top_reasons.items():
        pct = (count / len(df)) * 100
        print(f"  {reason}: {count} outlets ({pct:.1f}%)")
    
    print(f"\nOutlet Size Distribution:")
    for size in ['Large', 'Medium', 'Small']:
        count = len(df[df['outlet_size'] == size])
        potential = df[df['outlet_size'] == size]['potential_monthly_value'].sum()
        print(f"  {size}: {count} outlets (Potential: ৳{potential:,.0f})")
    
    print("\n" + "="*70)


def main():
    """Main function to generate not ordered outlets map and analysis."""
    
    print("Generating not ordered outlets data...")
    df = generate_not_ordered_outlets(config, n_outlets=1500, seed=42)
    
    print("Creating not ordered outlets map...")
    create_not_ordered_map(df, output_file='outputs/not_ordered_outlets_map.html')
    
    print("Exporting data to Excel...")
    export_to_excel(df, filename='outputs/not_ordered_outlets_analysis.xlsx')
    
    print_summary_statistics(df)
    
    print("\nAnalysis complete!")
    print(f"  - Interactive Map: outputs/not_ordered_outlets_map.html")
    print(f"  - Excel Report: outputs/not_ordered_outlets_analysis.xlsx")


if __name__ == '__main__':
    main()