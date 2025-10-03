import pandas as pd
import numpy as np
import random
import json
import os
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

# Create necessary directories
os.makedirs('outputs', exist_ok=True)

print("Sales Analytics Dashboard - Starting")
print("="*70)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

def get_region(city_name):
    """Get region for a city."""
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
    for region, cities in regions.items():
        if city_name in cities:
            return region
    return 'Central'

def generate_central_csv():
    """Generate central CSV with all map data."""
    print("\nGenerating central CSV with all map data...")
    random.seed(42)
    np.random.seed(42)
    
    cities = config['cities']
    city_names = [c[0] for c in cities]
    city_weights = np.array([c[3] for c in cities], dtype=float)
    city_weights /= city_weights.sum()
    
    all_records = []
    
    # 1. Sales Data (1000 records)
    print("  - Generating sales data...")
    categories = config['categories']
    category_probs = config['category_probs']
    price_ranges = config['price_ranges']
    
    for i in range(1000):
        idx = np.random.choice(len(cities), p=city_weights)
        city = cities[idx]
        category = np.random.choice(list(categories.keys()), p=list(category_probs.values()))
        product = random.choice(categories[category])
        low, high = price_ranges[category]
        price = random.randint(int(low), int(high))
        units = random.randint(1, 100)
        
        all_records.append({
            'data_type': 'sales',
            'record_id': f'SALE{i+1:04d}',
            'city': city[0],
            'region': get_region(city[0]),
            'latitude': round(city[1] + np.random.normal(0, 0.05), 6),
            'longitude': round(city[2] + np.random.normal(0, 0.06), 6),
            'category': category,
            'product': product,
            'price_bdt': price,
            'units_sold': units,
            'sales_amount': price * units,
            'date': (date.today() - timedelta(days=random.randint(0, 365))).isoformat(),
            'store_size': random.choice(['Small', 'Medium', 'Large']),
            'customer_rating': round(random.uniform(3.0, 5.0), 1)
        })
    
    # 2. Visit Coverage Data (800 records)
    print("  - Generating visit coverage data...")
    salespersons = ['Karim Ahmed', 'Rahim Hossain', 'Fatima Begum', 'Ayesha Khan', 'Jamal Uddin']
    
    for i in range(800):
        idx = np.random.choice(len(cities), p=city_weights)
        city = cities[idx]
        
        all_records.append({
            'data_type': 'visit',
            'record_id': f'VISIT{i+1:04d}',
            'city': city[0],
            'region': get_region(city[0]),
            'latitude': round(city[1] + np.random.normal(0, 0.04), 6),
            'longitude': round(city[2] + np.random.normal(0, 0.05), 6),
            'salesperson': random.choice(salespersons),
            'coverage_value': random.randint(1, 6),
            'outlets_visited': random.randint(1, 8),
            'duration_hours': round(random.uniform(0.5, 4.0), 1),
            'date': (date.today() - timedelta(days=random.randint(0, 90))).isoformat()
        })
    
    # 3. Not Ordered Outlets (1500 records)
    print("  - Generating not ordered outlets...")
    outlet_types = ['Retail Shop', 'Grocery Store', 'Pharmacy', 'Department Store']
    reasons = ['Not contacted yet', 'Price concerns', 'Stock issues', 'Competitor preference']
    
    for i in range(1500):
        idx = np.random.choice(len(cities), p=city_weights)
        city = cities[idx]
        size = random.choice(['Small', 'Medium', 'Large'])
        
        if size == 'Large':
            potential = random.randint(50000, 150000)
        elif size == 'Medium':
            potential = random.randint(20000, 60000)
        else:
            potential = random.randint(5000, 25000)
        
        all_records.append({
            'data_type': 'not_ordered',
            'record_id': f'NOUT{i+1:04d}',
            'city': city[0],
            'region': get_region(city[0]),
            'latitude': round(city[1] + np.random.normal(0, 0.04), 6),
            'longitude': round(city[2] + np.random.normal(0, 0.05), 6),
            'outlet_type': random.choice(outlet_types),
            'outlet_size': size,
            'priority_score': random.randint(1, 10),
            'potential_monthly_value': potential,
            'days_since_contact': random.randint(0, 180),
            'no_order_reason': random.choice(reasons),
            'assigned_salesperson': random.choice(salespersons)
        })
    
    # 4. Brand Coverage (150 records)
    print("  - Generating brand coverage...")
    brands = ['Brand A', 'Brand B', 'Brand C', 'Brand D', 'Brand E']
    
    for i in range(150):
        idx = np.random.choice(len(cities), p=city_weights)
        city = cities[idx]
        
        all_records.append({
            'data_type': 'brand',
            'record_id': f'BRAND{i+1:04d}',
            'brand': random.choice(brands),
            'city': city[0],
            'region': get_region(city[0]),
            'latitude': round(city[1] + np.random.normal(0, 0.05), 6),
            'longitude': round(city[2] + np.random.normal(0, 0.06), 6),
            'coverage_score': random.randint(20, 100),
            'num_outlets': random.randint(1, 15),
            'market_share': round(random.uniform(5, 35), 1)
        })
    
    # 5. Sweet Spots (50 records)
    print("  - Generating sweet spots...")
    
    for i in range(50):
        idx = np.random.choice(len(cities), p=city_weights)
        city = cities[idx]
        visit_count = random.randint(8, 50)
        
        all_records.append({
            'data_type': 'sweet_spot',
            'record_id': f'SPOT{i+1:04d}',
            'city': city[0],
            'region': get_region(city[0]),
            'latitude': round(city[1] + np.random.normal(0, 0.03), 6),
            'longitude': round(city[2] + np.random.normal(0, 0.04), 6),
            'visit_count': visit_count,
            'total_outlets': random.randint(10, 80),
            'unique_salespersons': random.randint(2, 8),
            'intensity_score': round(visit_count / 50, 2),
            'category': 'Hot Spot' if visit_count >= 30 else ('High Activity' if visit_count >= 15 else 'Medium Activity')
        })
    
    # 6. Routes (approx 200 records)
    print("  - Generating route connections...")
    
    for i, city1 in enumerate(cities[:30]):  # Limit for performance
        for city2 in cities[i+1:30]:
            from math import radians, sin, cos, sqrt, atan2
            lat1, lon1 = radians(city1[1]), radians(city1[2])
            lat2, lon2 = radians(city2[1]), radians(city2[2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = 6371 * c
            
            if distance < 200:
                all_records.append({
                    'data_type': 'route',
                    'from_city': city1[0],
                    'to_city': city2[0],
                    'from_region': get_region(city1[0]),
                    'to_region': get_region(city2[0]),
                    'from_latitude': city1[1],
                    'from_longitude': city1[2],
                    'to_latitude': city2[1],
                    'to_longitude': city2[2],
                    'distance_km': round(distance, 2)
                })
    
    # Create DataFrame
    df = pd.DataFrame(all_records)
    df['generated_at'] = datetime.now().isoformat()
    
    # Save central CSV
    csv_path = 'outputs/central_sales_data.csv'
    df.to_csv(csv_path, index=False)
    
    print(f"\nCentral CSV created: {csv_path}")
    print(f"Total records: {len(df):,}")
    print(f"  Sales: {len(df[df['data_type']=='sales']):,}")
    print(f"  Visits: {len(df[df['data_type']=='visit']):,}")
    print(f"  Not Ordered: {len(df[df['data_type']=='not_ordered']):,}")
    print(f"  Brand: {len(df[df['data_type']=='brand']):,}")
    print(f"  Sweet Spots: {len(df[df['data_type']=='sweet_spot']):,}")
    print(f"  Routes: {len(df[df['data_type']=='route']):,}")
    
    return df

def create_dashboard_html(df):
    """Create the HTML dashboard matching the design."""
    print("\nCreating dashboard HTML...")
    
    total_records = len(df)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Analytics Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 300;
            letter-spacing: 4px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        
        .header p {{
            font-size: 1rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 50px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.95rem;
            font-weight: 500;
        }}
        
        .maps-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .map-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.25);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .map-card:hover {{
            transform: translateY(-10px);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
        }}
        
        .map-icon {{
            height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 5rem;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        }}
        
        .map-content {{
            padding: 25px;
        }}
        
        .map-title {{
            font-size: 1.4rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 12px;
        }}
        
        .map-description {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 20px;
            font-size: 0.95rem;
        }}
        
        .btn-view {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            font-size: 0.95rem;
        }}
        
        .btn-view:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .footer {{
            text-align: center;
            color: white;
            padding: 30px;
            margin-top: 40px;
        }}
        
        .footer a {{
            color: white;
            text-decoration: none;
            background: rgba(255, 255, 255, 0.2);
            padding: 10px 25px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 15px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .footer a:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8rem;
            }}
            .maps-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SALES ANALYTICS DASHBOARD</h1>
            <p>Bangladesh Sales Intelligence & Territory Management</p>
        </div>
        
        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-value">{total_records:,}+</div>
                <div class="stat-label">Total Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">6</div>
                <div class="stat-label">Interactive Maps</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">51</div>
                <div class="stat-label">Cities</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">5</div>
                <div class="stat-label">Regions</div>
            </div>
        </div>
        
        <div class="maps-grid">
            <div class="map-card" onclick="window.open('sales_map.html', '_blank')">
                <div class="map-icon">📊</div>
                <div class="map-content">
                    <div class="map-title">Sales Coverage Map</div>
                    <div class="map-description">
                        Visualization of 1,000 sales records across Bangladesh with category analysis.
                    </div>
                    <a href="sales_map.html" class="btn-view" onclick="event.stopPropagation()">View Map</a>
                </div>
            </div>
            
            <div class="map-card" onclick="window.open('visit_coverage_map.html', '_blank')">
                <div class="map-icon">📍</div>
                <div class="map-content">
                    <div class="map-title">Visit Coverage Map</div>
                    <div class="map-description">
                        800 salesperson visits with coverage intensity (1-6 scale) analysis.
                    </div>
                    <a href="visit_coverage_map.html" class="btn-view" onclick="event.stopPropagation()">View Map</a>
                </div>
            </div>
            
            <div class="map-card" onclick="window.open('not_ordered_outlets_map.html', '_blank')">
                <div class="map-icon">🏪</div>
                <div class="map-content">
                    <div class="map-title">Not Ordered Outlets</div>
                    <div class="map-description">
                        1,500 outlets without orders, prioritized by potential value.
                    </div>
                    <a href="not_ordered_outlets_map.html" class="btn-view" onclick="event.stopPropagation()">View Map</a>
                </div>
            </div>
            
            <div class="map-card" onclick="window.open('brand_coverage_map.html', '_blank')">
                <div class="map-icon">🏷️</div>
                <div class="map-content">
                    <div class="map-title">Brand Coverage Map</div>
                    <div class="map-description">
                        150 brand locations showing market penetration and coverage scores.
                    </div>
                    <a href="brand_coverage_map.html" class="btn-view" onclick="event.stopPropagation()">View Map</a>
                </div>
            </div>
            
            <div class="map-card" onclick="window.open('route_map_bangladesh.html', '_blank')">
                <div class="map-icon">🛣️</div>
                <div class="map-content">
                    <div class="map-title">Route Network Map</div>
                    <div class="map-description">
                        City connections within 200km with distance calculations and filtering.
                    </div>
                    <a href="route_map_bangladesh.html" class="btn-view" onclick="event.stopPropagation()">View Map</a>
                </div>
            </div>
            
            <div class="map-card" onclick="window.open('sweet_spot_map.html', '_blank')">
                <div class="map-icon">🎯</div>
                <div class="map-content">
                    <div class="map-title">Sweet Spot Map</div>
                    <div class="map-description">
                        High-activity zones for focused sales efforts (8+ visits).
                    </div>
                    <a href="sweet_spot_map.html" class="btn-view" onclick="event.stopPropagation()">View Map</a>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Sales Analytics Dashboard v1.0 | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <a href="central_sales_data.csv" download>📥 Download Central CSV Dataset</a>
        </div>
    </div>
</body>
</html>"""
    
    dashboard_path = 'outputs/dashboard.html'
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Dashboard created: {dashboard_path}")
    return dashboard_path

def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("SALES ANALYTICS DASHBOARD GENERATOR")
    print("="*70)
    
    # Generate central CSV
    df = generate_central_csv()
    
    # Create dashboard HTML
    dashboard_path = create_dashboard_html(df)
    
    print("\n" + "="*70)
    print("COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"\nGenerated Files:")
    print(f"  Dashboard: {os.path.abspath(dashboard_path)}")
    print(f"  Central CSV: {os.path.abspath('outputs/central_sales_data.csv')}")
    print(f"\nMake sure your map HTML files are in 'outputs/' folder:")
    print(f"  - sales_map.html")
    print(f"  - visit_coverage_map.html")
    print(f"  - not_ordered_outlets_map.html")
    print(f"  - brand_coverage_map.html")
    print(f"  - route_map_bangladesh.html")
    print(f"  - sweet_spot_map.html")
    
    # Open dashboard in browser
    print("\nOpening dashboard in browser...")
    webbrowser.open(f'file://{os.path.abspath(dashboard_path)}')

if __name__ == '__main__':
    main()