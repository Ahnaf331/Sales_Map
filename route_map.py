import pandas as pd
import numpy as np
import folium
from folium.plugins import MiniMap
import random
import math
from datetime import date, datetime, timedelta
import json
import os

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return c * r

def generate_synthetic_sales(config, n_records=1000, seed=42):
    """Generate synthetic sales data with detailed product and location information."""
    random.seed(seed)
    np.random.seed(seed)
    
    sales = []
    current_date = date.today()
    
    categories = config['categories']
    price_ranges = config['price_ranges']
    cities = config['cities']
    category_probs = config['category_probs']
    mean_units = config['mean_units']
    
    city_weights = np.array([c[3] for c in cities], dtype=float)
    city_weights /= city_weights.sum()
    
    city_names = [c[0] for c in cities]
    city_lats = [c[1] for c in cities]
    city_lons = [c[2] for c in cities]
    
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
    
    beat_cities = {}
    for region, city_list in regions.items():
        region_cities = [c for c in cities if c[0] in city_list]
        num_beats = max(1, len(region_cities) // 3)
        
        for i in range(num_beats):
            beat_cities[f"{region[0]}{i+1}"] = [c[0] for c in region_cities[i::num_beats]]
    
    for beat_id, beat_city_names in beat_cities.items():
        for city_name in beat_city_names:
            if city_name not in city_names:
                continue
                
            city_idx = city_names.index(city_name)
            lat, lon = city_lats[city_idx], city_lons[city_idx]
            
            num_stores = random.randint(5, 15)
            stores = [{
                'store_id': f"{beat_id}-{i:03d}",
                'size': random.choice(['Small', 'Medium', 'Large']),
                'rating': round(random.uniform(3.5, 5.0), 1),
                'lat': lat + random.uniform(-0.05, 0.05),
                'lon': lon + random.uniform(-0.05, 0.05),
                'beat_id': beat_id,
                'region': next(r for r, cities in regions.items() if city_name in cities)
            } for i in range(1, num_stores + 1)]
            
            for store in stores:
                sales_per_store = n_records // len(stores) // len(beat_cities)
                if store['size'] == 'Small':
                    sales_per_store = int(sales_per_store * 0.7)
                elif store['size'] == 'Large':
                    sales_per_store = int(sales_per_store * 1.5)
                
                for _ in range(max(1, sales_per_store)):
                    days_ago = random.randint(0, 364)
                    sale_date = current_date - timedelta(days=days_ago)
                    
                    category = np.random.choice(
                        list(category_probs.keys()),
                        p=list(category_probs.values())
                    )
                    product = random.choice(categories[category])
                    
                    low, high = price_ranges[category]
                    price = random.uniform(low, high)
                    
                    base_units = mean_units[category]
                    units_sold = max(1, int(random.normalvariate(base_units, base_units * 0.3)))
                    
                    amount = round(price * units_sold, 2)
                    
                    store_lat = store['lat'] + random.uniform(-0.005, 0.005)
                    store_lon = store['lon'] + random.uniform(-0.005, 0.005)
                    
                    sales.append({
                        'store_id': store['store_id'],
                        'store_size': store['size'],
                        'store_rating': store['rating'],
                        'beat_id': store['beat_id'],
                        'region': store['region'],
                        'city': city_name,
                        'lat': store_lat,
                        'lon': store_lon,
                        'sale_date': sale_date,
                        'category': category,
                        'product': product,
                        'price': price,
                        'units_sold': units_sold,
                        'amount': amount,
                        'customer_rating': round(random.uniform(3.0, 5.0), 1)
                    })
    
    return pd.DataFrame(sales)

def create_route_map(df, center_lat=23.8103, center_lon=90.4125, zoom_start=7):
    """Create a route map with regional colors, sized circles, distance labels, and location filter."""
    
    # Create base map with dark theme
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles='CartoDB dark_matter',
        attr='CartoDB',
        control_scale=True
    )
    
    # Regional colors matching screenshot
    region_colors = {
        'North': '#FF6B6B',      # Red
        'South': '#45B7D1',      # Blue
        'East': '#E08DAC',       # Pink/Purple
        'West': '#52B788',       # Green
        'Central': '#4ECDC4'     # Teal
    }
    
    # Get city-level aggregated data
    city_data = df.groupby(['city', 'region']).agg({
        'lat': 'first',
        'lon': 'first',
        'amount': 'sum',
        'store_id': 'nunique'
    }).reset_index()
    
    # Major cities (top 25% by sales)
    city_data['is_major'] = city_data['amount'] > city_data['amount'].quantile(0.75)
    
    # Create route connections
    location_pairs = []
    for i in range(len(city_data)):
        for j in range(i + 1, len(city_data)):
            loc1 = city_data.iloc[i]
            loc2 = city_data.iloc[j]
            distance = haversine(loc1['lat'], loc1['lon'], loc2['lat'], loc2['lon'])
            
            if distance < 200:  # Connect cities within 200km
                location_pairs.append((loc1, loc2, distance))
    
    # Sort by distance for better visualization
    location_pairs.sort(key=lambda x: x[2])
    
    # Draw routes with distance labels and unique IDs
    for idx, (loc1, loc2, distance) in enumerate(location_pairs):
        color = region_colors.get(loc1['region'], '#95A5A6')
        
        mid_lat = (loc1['lat'] + loc2['lat']) / 2
        mid_lon = (loc1['lon'] + loc2['lon']) / 2
        
        # Add route line with custom class for filtering
        folium.PolyLine(
            locations=[[loc1['lat'], loc1['lon']], [loc2['lat'], loc2['lon']]],
            color=color,
            weight=2,
            opacity=0.6,
            className=f"route-{loc1['city'].replace(' ', '-')}-{loc2['city'].replace(' ', '-')}"
        ).add_to(m)
        
        # Distance label
        folium.Marker(
            location=[mid_lat, mid_lon],
            icon=folium.DivIcon(html=f'''
                <div class="distance-label distance-{loc1['city'].replace(' ', '-')}-{loc2['city'].replace(' ', '-')}" 
                     style="font-size: 9px; color: {color}; font-weight: bold; 
                            text-shadow: 1px 1px 2px rgba(0,0,0,0.8), -1px -1px 2px rgba(0,0,0,0.8);">
                    {int(distance)}km
                </div>
            ''')
        ).add_to(m)
    
    # Add city markers
    for idx, city in city_data.iterrows():
        color = region_colors.get(city['region'], '#95A5A6')
        
        if city['is_major']:
            radius = 25
            opacity = 0.8
        else:
            radius = 15
            opacity = 0.7
        
        # Circle marker with custom class
        folium.CircleMarker(
            location=[city['lat'], city['lon']],
            radius=radius,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=opacity,
            weight=2,
            className=f"city-marker city-{city['city'].replace(' ', '-')}",
            popup=f"""
                <b>{city['city']}</b><br>
                Region: {city['region']}<br>
                Total Sales: ৳{city['amount']:,.2f}<br>
                Stores: {city['store_id']}
            """,
            tooltip=city['city']
        ).add_to(m)
        
        # City label
        folium.Marker(
            location=[city['lat'], city['lon']],
            icon=folium.DivIcon(html=f'''
                <div class="city-label city-{city['city'].replace(' ', '-')}" 
                     style="font-size: 11px; color: {color}; font-weight: bold; 
                            text-shadow: 1px 1px 3px rgba(0,0,0,0.9), -1px -1px 3px rgba(0,0,0,0.9);
                            margin-left: 30px; margin-top: -5px; white-space: nowrap;">
                    {city['city']}
                </div>
            ''')
        ).add_to(m)
    
    # Create city list for JavaScript
    city_list = [{'name': city['city'], 'region': city['region'], 
                  'lat': city['lat'], 'lon': city['lon']} 
                 for _, city in city_data.iterrows()]
    
    # Add legend with dark theme
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; 
                width: 200px; 
                background-color: rgba(40, 40, 40, 0.95); 
                border: 2px solid #555; 
                z-index: 1000; 
                font-size: 14px;
                color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.5);">
        <p style="margin: 0 0 12px 0; font-weight: bold; font-size: 16px;">Regions</p>
    '''
    
    for region, color in region_colors.items():
        legend_html += f'''
        <p style="margin: 8px 0;">
            <span style="background-color: {color}; 
                        width: 20px; 
                        height: 20px; 
                        display: inline-block; 
                        border-radius: 50%;
                        margin-right: 10px;
                        border: 1px solid rgba(255,255,255,0.3);"></span>
            {region}
        </p>
        '''
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add title and search interface with dark theme
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50%; 
                transform: translateX(-50%);
                z-index: 1000; 
                background: rgba(40, 40, 40, 0.95); 
                color: white;
                padding: 10px 25px; 
                border-radius: 8px; 
                box-shadow: 0 0 15px rgba(0,0,0,0.5);
                border: 2px solid #555;
                font-size: 18px;
                font-weight: bold;">
        Bangladesh Sales Route Network
    </div>
    
    <div style="position: fixed; 
                top: 60px; left: 50%; 
                transform: translateX(-50%);
                z-index: 1000; 
                background: rgba(40, 40, 40, 0.95); 
                padding: 10px 20px; 
                border-radius: 8px; 
                border: 2px solid #555;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);">
        <input type="text" 
               id="cityFilter" 
               placeholder="Search location (e.g., Dhaka, Sylhet)..."
               list="cityOptions"
               style="width: 300px; 
                      padding: 8px; 
                      border: 1px solid #555; 
                      background-color: rgba(60, 60, 60, 0.9);
                      color: white;
                      border-radius: 4px;
                      font-size: 14px;">
        <datalist id="cityOptions">
    '''
    
    # Add all cities to datalist for autocomplete
    for city in city_list:
        title_html += f'<option value="{city["name"]}">'
    
    title_html += '''
        </datalist>
        <button onclick="filterMap()" 
                style="padding: 8px 15px; 
                       margin-left: 10px;
                       background: #4ECDC4; 
                       color: white; 
                       border: none; 
                       border-radius: 4px;
                       cursor: pointer;
                       font-size: 14px;
                       font-weight: bold;">
            Filter
        </button>
        <button onclick="resetMap()" 
                style="padding: 8px 15px; 
                       margin-left: 5px;
                       background: #95A5A6; 
                       color: white; 
                       border: none; 
                       border-radius: 4px;
                       cursor: pointer;
                       font-size: 14px;
                       font-weight: bold;">
            Reset
        </button>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add JavaScript for filtering
    filter_js = f'''
    <script>
    const cityData = {json.dumps(city_list)};
    let currentFilter = null;
    
    function filterMap() {{
        const searchTerm = document.getElementById('cityFilter').value.trim();
        
        if (!searchTerm) {{
            alert('Please enter a location name');
            return;
        }}
        
        // Find matching city
        const matchingCity = cityData.find(city => 
            city.name.toLowerCase() === searchTerm.toLowerCase() ||
            city.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            searchTerm.toLowerCase().includes(city.name.toLowerCase())
        );
        
        if (!matchingCity) {{
            const cityNames = cityData.map(c => c.name).join(', ');
            alert('Location not found. Available cities: ' + cityNames);
            return;
        }}
        
        currentFilter = matchingCity.name;
        const safeCityName = matchingCity.name.replace(/[^a-zA-Z0-9]/g, '-');
        
        // Hide all elements first
        document.querySelectorAll('.leaflet-interactive').forEach(el => {{
            el.style.display = 'none';
        }});
        document.querySelectorAll('.leaflet-marker-icon').forEach(el => {{
            el.style.display = 'none';
        }});
        
        // Show selected city and its connections
        document.querySelectorAll(`.city-${{safeCityName}}`).forEach(el => {{
            el.style.display = 'block';
        }});
        
        // Find and show connected cities and routes
        cityData.forEach(otherCity => {{
            if (otherCity.name === matchingCity.name) return;
            
            const dist = haversineJS(
                matchingCity.lat, matchingCity.lon,
                otherCity.lat, otherCity.lon
            );
            
            if (dist < 200) {{
                const safeOtherName = otherCity.name.replace(/[^a-zA-Z0-9]/g, '-');
                
                // Show connected city
                document.querySelectorAll(`.city-${{safeOtherName}}`).forEach(el => {{
                    el.style.display = 'block';
                }});
                
                // Show routes (both directions)
                document.querySelectorAll(`.route-${{safeCityName}}-${{safeOtherName}}`).forEach(el => {{
                    el.style.display = 'block';
                }});
                document.querySelectorAll(`.route-${{safeOtherName}}-${{safeCityName}}`).forEach(el => {{
                    el.style.display = 'block';
                }});
                
                // Show distance labels
                document.querySelectorAll(`.distance-${{safeCityName}}-${{safeOtherName}}`).forEach(el => {{
                    el.style.display = 'block';
                }});
                document.querySelectorAll(`.distance-${{safeOtherName}}-${{safeCityName}}`).forEach(el => {{
                    el.style.display = 'block';
                }});
            }}
        }});
        
        // Center map on selected city
        map.setView([matchingCity.lat, matchingCity.lon], 9);
    }}
    
    function resetMap() {{
        document.getElementById('cityFilter').value = '';
        currentFilter = null;
        
        // Show all elements
        document.querySelectorAll('.leaflet-interactive').forEach(el => {{
            el.style.display = 'block';
        }});
        document.querySelectorAll('.leaflet-marker-icon').forEach(el => {{
            el.style.display = 'block';
        }});
        
        // Reset view
        map.setView([{center_lat}, {center_lon}], {zoom_start});
    }}
    
    function haversineJS(lat1, lon1, lat2, lon2) {{
        const toRad = x => x * Math.PI / 180;
        const R = 6371;
        const dLat = toRad(lat2 - lat1);
        const dLon = toRad(lon2 - lon1);
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }}
    
    // Store map reference
    let map;
    setTimeout(() => {{
        map = document.querySelector('.folium-map').__leaflet__;
    }}, 100);
    
    // Enter key support
    document.getElementById('cityFilter').addEventListener('keypress', function(e) {{
        if (e.key === 'Enter') {{
            filterMap();
        }}
    }});
    </script>
    '''
    m.get_root().html.add_child(folium.Element(filter_js))
    
    return m

def export_to_excel(df, filename='outputs/sales_analysis.xlsx'):
    """Export sales data to Excel with multiple analytical sheets."""
    print("🔹 Generating Excel report...")
    
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    
    if not pd.api.types.is_datetime64_any_dtype(df['sale_date']):
        df['sale_date'] = pd.to_datetime(df['sale_date'])
    
    df['month_year'] = df['sale_date'].dt.to_period('M').astype(str)
    df['year'] = df['sale_date'].dt.year
    
    # Summary sheet
    summary = df.groupby(['region', 'beat_id', 'city', 'category']).agg({
        'amount': 'sum',
        'units_sold': 'sum',
        'store_id': 'nunique',
        'customer_rating': 'mean'
    }).reset_index()
    summary.columns = ['Region', 'Beat', 'City', 'Category', 'Total Sales', 'Units Sold', 'Unique Stores', 'Avg Rating']
    summary.to_excel(writer, sheet_name='Summary', index=False)
    
    # Monthly trend
    monthly = df.groupby(['month_year', 'region', 'category'])['amount'].sum().unstack().reset_index()
    monthly.to_excel(writer, sheet_name='Monthly Trend', index=False)
    
    # Store performance
    store_perf = df.groupby(['store_id', 'city', 'beat_id', 'store_size']).agg({
        'amount': 'sum',
        'units_sold': 'sum',
        'customer_rating': 'mean',
        'sale_date': 'count'
    }).reset_index()
    store_perf.columns = ['Store ID', 'City', 'Beat', 'Size', 'Total Sales', 'Units Sold', 'Avg Rating', 'Transactions']
    store_perf = store_perf.sort_values('Total Sales', ascending=False)
    store_perf.to_excel(writer, sheet_name='Store Performance', index=False)
    
    # Category analysis
    category_analysis = df.groupby('category').agg({
        'amount': 'sum',
        'units_sold': 'sum',
        'customer_rating': 'mean'
    }).reset_index()
    category_analysis.columns = ['Category', 'Total Sales', 'Units Sold', 'Avg Rating']
    category_analysis = category_analysis.sort_values('Total Sales', ascending=False)
    category_analysis.to_excel(writer, sheet_name='Category Analysis', index=False)
    
    # Regional analysis
    regional = df.groupby('region').agg({
        'amount': 'sum',
        'units_sold': 'sum',
        'city': 'nunique',
        'store_id': 'nunique'
    }).reset_index()
    regional.columns = ['Region', 'Total Sales', 'Units Sold', 'Cities', 'Stores']
    regional.to_excel(writer, sheet_name='Regional Analysis', index=False)
    
    writer.close()
    print(f"✅ Excel report saved to {filename}")

def main():
    try:
        print("🔹 Loading configuration...")
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("✅ Configuration loaded successfully")
        
        print("\n🔹 Generating synthetic sales data...")
        sales_df = generate_synthetic_sales(config, n_records=5000)
        print(f"✅ Generated {len(sales_df)} sales records")
        
        print("\n🔹 Creating interactive route map with location filter...")
        route_map = create_route_map(sales_df)
        print("✅ Route map created successfully")
        
        os.makedirs('outputs', exist_ok=True)
        
        output_file = 'outputs/route_map_bangladesh.html'
        route_map.save(output_file)
        print(f"✅ Interactive route map saved to {output_file}")
        
        csv_file = 'outputs/sales_data_detailed.csv'
        sales_df.to_csv(csv_file, index=False)
        print(f"✅ Detailed sales data saved to {csv_file}")
        
        print("\n🔹 Exporting to Excel...")
        excel_file = 'outputs/sales_analysis.xlsx'
        export_to_excel(sales_df, filename=excel_file)
        
        print("\n🎉 Data generation and export complete!")
        print(f"   - Interactive Map: {os.path.abspath(output_file)}")
        print(f"   - Detailed Data: {os.path.abspath(csv_file)}")
        print(f"   - Excel Report: {os.path.abspath(excel_file)}")
        
        print("\n🔹 Opening map in default browser...")
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(output_file)}')
        
    except Exception as e:
        print("\n❌ An error occurred:")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()