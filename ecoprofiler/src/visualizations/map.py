import folium
import folium.plugins as plugins
import geopandas as gpd
import pandas as pd
import logging
from pathlib import Path
import json
import numpy as np

logger = logging.getLogger("MapVisualization")

def create_alert_map(glad_alerts, osm_businesses, center_lat=None, center_lon=None):
    """Create interactive Folium map with GLAD alerts and OSM businesses"""
    try:
        # Calculate center if not provided
        if center_lat is None or center_lon is None:
            if not glad_alerts.empty and 'latitude' in glad_alerts.columns and 'longitude' in glad_alerts.columns:
                center_lat = glad_alerts['latitude'].mean()
                center_lon = glad_alerts['longitude'].mean()
            elif osm_businesses:
                valid_businesses = [b for b in osm_businesses if b.get('lat') and b.get('lon')]
                if valid_businesses:
                    center_lat = np.mean([b.get('lat', 0) for b in valid_businesses])
                    center_lon = np.mean([b.get('lon', 0) for b in valid_businesses])
                else:
                    center_lat, center_lon = 0, 0
            else:
                center_lat, center_lon = 0, 0
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Add GLAD alerts layer
        if not glad_alerts.empty:
            glad_layer = folium.FeatureGroup(name='🌳 Forest Loss Alerts')
            
            for idx, alert in glad_alerts.iterrows():
                # Determine color based on alert confidence or recency
                alert_color = 'red'  # High confidence/urgent
                
                folium.CircleMarker(
                    location=[alert.get('latitude', center_lat), alert.get('longitude', center_lon)],
                    radius=6,
                    popup=create_alert_popup(alert),
                    tooltip=f"Forest Alert: {alert.get('date', 'Unknown')}",
                    color=alert_color,
                    fillColor=alert_color,
                    fillOpacity=0.7,
                    weight=2
                ).add_to(glad_layer)
            
            glad_layer.add_to(m)
        
        # Add OSM businesses layer
        if osm_businesses:
            osm_layer = folium.FeatureGroup(name='🏢 Local Businesses')
            
            for business in osm_businesses:
                if business.get('lat') and business.get('lon'):
                    business_color = 'blue'
                    
                    folium.CircleMarker(
                        location=[business['lat'], business['lon']],
                        radius=4,
                        popup=create_business_popup(business),
                        tooltip=f"Business: {business.get('tags', {}).get('name', 'Unknown')}",
                        color=business_color,
                        fillColor=business_color,
                        fillOpacity=0.7,
                        weight=1
                    ).add_to(osm_layer)
            
            osm_layer.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add fullscreen control
        plugins.Fullscreen().add_to(m)
        
        logger.info("Map created successfully")
        return m
        
    except Exception as e:
        logger.error(f"Error creating map: {str(e)}")
        # Return basic map on error
        return folium.Map(location=[0, 0], zoom_start=2)

def create_alert_popup(alert):
    """Create popup content for GLAD alerts"""
    popup_html = f"""
    <div style="width: 250px;">
        <h4>🌳 Forest Loss Alert</h4>
        <b>Date:</b> {alert.get('date', 'Unknown')}<br>
        <b>Confidence:</b> {alert.get('confidence', 'N/A')}<br>
        <b>Area:</b> {alert.get('area', 'N/A')} ha<br>
        <b>Latitude:</b> {alert.get('latitude', 'N/A'):.4f}<br>
        <b>Longitude:</b> {alert.get('longitude', 'N/A'):.4f}<br>
    </div>
    """
    return folium.Popup(popup_html, max_width=300)

def create_business_popup(business):
    """Create popup content for OSM businesses"""
    tags = business.get('tags', {})
    name = tags.get('name', 'Unknown Business')
    business_type = tags.get('shop', tags.get('office', tags.get('industrial', 'Unknown')))
    
    popup_html = f"""
    <div style="width: 250px;">
        <h4>🏢 {name}</h4>
        <b>Type:</b> {business_type}<br>
        <b>Latitude:</b> {business.get('lat', 'N/A'):.4f}<br>
        <b>Longitude:</b> {business.get('lon', 'N/A'):.4f}<br>
    """
    
    # Add additional tags if available
    additional_tags = 0
    for key, value in list(tags.items())[:3]:  # Show first 3 tags
        if key not in ['name', 'shop', 'office', 'industrial']:
            popup_html += f"<b>{key}:</b> {value}<br>"
            additional_tags += 1
    
    popup_html += "</div>"
    return folium.Popup(popup_html, max_width=300)

def create_satellite_overlay(satellite_images, map_obj):
    """Add satellite imagery overlay to map"""
    try:
        # This would integrate with actual satellite image tiles
        # For now, we'll create a placeholder
        if satellite_images:
            satellite_layer = folium.FeatureGroup(name='🛰️ Satellite Imagery')
            
            # Add each satellite image as an overlay
            for img_path in satellite_images[:3]:  # Limit to 3 images
                # This is simplified - real implementation would use image bounds
                # Check if the file exists and is an image
                if str(img_path).endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
                    folium.raster_layers.ImageOverlay(
                        image=str(img_path),
                        bounds=[[-1, -1], [1, 1]],  # Placeholder bounds
                        opacity=0.6,
                        interactive=True,
                        cross_origin=False,
                        zindex=1
                    ).add_to(satellite_layer)
            
            satellite_layer.add_to(map_obj)
            logger.info("Satellite overlay added to map")
            
    except Exception as e:
        logger.warning(f"Could not add satellite overlay: {str(e)}")

def create_simple_map(center_lat, center_lon, zoom=10):
    """Create a simple folium map with basic settings"""
    try:
        return folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
    except Exception as e:
        logger.error(f"Error creating simple map: {str(e)}")
        # Fallback to world map
        return folium.Map(location=[0, 0], zoom_start=2)