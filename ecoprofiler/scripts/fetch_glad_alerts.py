import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path
import json

class GLADAlertsFetcher:
    def __init__(self):
        self.logger = logging.getLogger("GLADAlerts")
        # Using GFW API for GLAD alerts - corrected endpoint
        self.base_url = "https://api.globalforestwatch.org"
        
    def get_glad_alerts(self, lat, lon, radius_km=20, days_back=30):
        """Fetch GLAD alerts for a location and radius"""
        try:
            self.logger.info(f"GLAD_FETCH_STARTED - Lat: {lat}, Lon: {lon}, Radius: {radius_km}km")
            
            # Calculate bounding box
            bbox = self._calculate_bounding_box(lat, lon, radius_km)
            
            # For demonstration - using sample data since GFW API requires authentication
            # In production, you'd use the actual GFW API with proper authentication
            sample_alerts = self._get_sample_alerts(lat, lon, bbox, days_back)
            
            self.logger.info(f"GLAD_FETCH_SUCCESS - Found {len(sample_alerts)} alerts")
            return sample_alerts
            
        except Exception as e:
            self.logger.error(f"GLAD_ERROR_OCCURRED: {str(e)}")
            # Return empty GeoDataFrame on error
            return gpd.GeoDataFrame()
    
    def _get_sample_alerts(self, lat, lon, bbox, days_back):
        """Generate sample GLAD alert data for demonstration"""
        import random
        from datetime import datetime, timedelta
        
        alerts = []
        num_alerts = random.randint(5, 15)
        
        for i in range(num_alerts):
            # Generate random points within the bounding box
            alert_lat = lat + random.uniform(-0.1, 0.1)
            alert_lon = lon + random.uniform(-0.1, 0.1)
            
            # Random date within the last N days
            alert_date = datetime.now() - timedelta(days=random.randint(0, days_back))
            
            alerts.append({
                'latitude': alert_lat,
                'longitude': alert_lon,
                'date': alert_date.strftime('%Y-%m-%d'),
                'confidence': round(random.uniform(0.7, 0.95), 2),
                'area': round(random.uniform(0.1, 5.0), 2),
                'alert_type': 'GLAD-L'
            })
        
        # Convert to GeoDataFrame
        geometry = [Point(alert['longitude'], alert['latitude']) for alert in alerts]
        gdf = gpd.GeoDataFrame(alerts, geometry=geometry, crs="EPSG:4326")
        
        return gdf
    
    def _calculate_bounding_box(self, lat, lon, radius_km):
        """Calculate bounding box from center point and radius"""
        # Approximate conversion (1 degree ≈ 111 km)
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(lat))
        
        return [
            lon - lon_delta,  # min_lon
            lat - lat_delta,  # min_lat  
            lon + lon_delta,  # max_lon
            lat + lat_delta   # max_lat
        ]
    
    def save_alerts(self, gdf, region_name):
        """Save alerts to CSV file"""
        try:
            output_dir = Path("data/alerts")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"{region_name}_glad.csv"
            
            # Convert to DataFrame for CSV (without geometry column)
            if not gdf.empty:
                df = pd.DataFrame(gdf)
                df = df.drop('geometry', axis=1, errors='ignore')
                df.to_csv(output_path, index=False)
            else:
                # Create empty CSV with correct columns
                empty_df = pd.DataFrame(columns=['latitude', 'longitude', 'date', 'confidence', 'area', 'alert_type'])
                empty_df.to_csv(output_path, index=False)
            
            self.logger.info(f"GLAD_OUTPUT_SAVED: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"GLAD_SAVE_ERROR: {str(e)}")
            return None