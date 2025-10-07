import logging
from pathlib import Path
import requests
import json
from datetime import datetime, timedelta
import os
from sentinelhub import (
    SHConfig,
    BBox,
    CRS,
    DataCollection,
    MimeType,
    MosaickingOrder,
    SentinelHubRequest,
    bbox_to_dimensions
)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger("SatelliteFetcher")

class SatelliteImageryFetcher:
    def __init__(self, client_id=None, client_secret=None):
        self.logger = logging.getLogger("SatelliteFetcher")
        
        # Configure Sentinel Hub
        self.config = SHConfig()
        
        if client_id and client_secret:
            self.config.sh_client_id = client_id
            self.config.sh_client_secret = client_secret
        else:
            # Try to get from environment
            self.config.sh_client_id = os.getenv('SENTINELHUB_CLIENT_ID')
            self.config.sh_client_secret = os.getenv('SENTINELHUB_CLIENT_SECRET')
        
        self.output_dir = Path("data/satellite")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify credentials
        if not self.config.sh_client_id or not self.config.sh_client_secret:
            self.logger.warning("Sentinel Hub credentials not configured")
        else:
            self.logger.info("Sentinel Hub credentials loaded successfully")
    
    def fetch_region_imagery(self, lat, lon, radius_km=20, region_name="unknown", days_back=30):
        """Fetch real satellite imagery for a region using Sentinel Hub"""
        try:
            self.logger.info(f"SENTINEL_FETCH_STARTED - Region: {region_name}")
            
            if not self.config.sh_client_id or not self.config.sh_client_secret:
                self.logger.error("SENTINEL_FAILURE: Missing Sentinel Hub credentials")
                return []
            
            # Calculate bounding box
            bbox = self._calculate_bbox(lat, lon, radius_km)
            resolution = 50  # meters per pixel
            
            # Create output directory for region
            region_dir = self.output_dir / region_name
            region_dir.mkdir(exist_ok=True)
            
            downloaded_images = []
            
            # Fetch True Color imagery using standard L2A true color
            true_color_images = self._fetch_true_color_standard(bbox, resolution, region_dir, region_name, days_back)
            downloaded_images.extend(true_color_images)
            
            # Fetch NDVI using standard approach
            ndvi_images = self._fetch_ndvi_standard(bbox, resolution, region_dir, region_name, days_back)
            downloaded_images.extend(ndvi_images)
            
            self.logger.info(f"SENTINEL_FETCH_SUCCESS - Downloaded {len(downloaded_images)} real satellite images")
            return downloaded_images
            
        except Exception as e:
            self.logger.error(f"SENTINEL_FAILURE: {str(e)}")
            return []
    
    def _calculate_bbox(self, lat, lon, radius_km):
        """Calculate bounding box from center and radius"""
        # Approximate conversion (1 degree ≈ 111 km)
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(lat))
        
        min_lon = lon - lon_delta
        max_lon = lon + lon_delta
        min_lat = lat - lat_delta
        max_lat = lat + lat_delta
        
        return BBox(bbox=[min_lon, min_lat, max_lon, max_lat], crs=CRS.WGS84)
    
    def _fetch_true_color_standard(self, bbox, resolution, output_dir, region_name, days_back):
        """Fetch true color imagery using standard Sentinel-2 L2A true color"""
        try:
            # Calculate image size
            size = bbox_to_dimensions(bbox, resolution=resolution)
            self.logger.info(f"True color image size: {size}")
            
            # Standard true color evalscript from Sentinel Hub documentation
            evalscript_true_color = """
            //VERSION=3
            function setup() {
                return {
                    input: [{
                        bands: ["B02", "B03", "B04"],
                        units: "REFLECTANCE"
                    }],
                    output: {
                        bands: 3
                    }
                };
            }

            function evaluatePixel(sample) {
                // Simple true color rendering
                // B04 = Red, B03 = Green, B02 = Blue
                return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
            }
            """
            
            # Calculate time interval (last N days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            self.logger.info(f"Fetching true color imagery from {start_date.date()} to {end_date.date()}")
            
            # Create request with L2A data
            request = SentinelHubRequest(
                evalscript=evalscript_true_color,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                        mosaicking_order=MosaickingOrder.MOST_RECENT
                    )
                ],
                responses=[
                    SentinelHubRequest.output_response('default', MimeType.PNG)
                ],
                bbox=bbox,
                size=size,
                config=self.config
            )
            
            # Download image
            self.logger.info("Downloading true color image...")
            image_data = request.get_data()
            
            if not image_data or len(image_data) == 0:
                self.logger.warning("No image data received for true color")
                return []
                
            image_array = image_data[0]
            
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"{region_name}_truecolor_{timestamp}.png"
            
            # Convert to PIL Image and save
            self._save_image_with_legend(image_array, output_path, "True Color", self._get_true_color_legend())
            
            self.logger.info(f"True color image saved: {output_path}")
            return [output_path]
            
        except Exception as e:
            self.logger.warning(f"True color fetch failed: {str(e)}")
            return []
    
    def _fetch_ndvi_standard(self, bbox, resolution, output_dir, region_name, days_back):
        """Fetch NDVI using standard Sentinel Hub approach"""
        try:
            # Calculate image size
            size = bbox_to_dimensions(bbox, resolution=resolution)
            self.logger.info(f"NDVI image size: {size}")
            
            # Standard NDVI evalscript from Sentinel Hub documentation
            evalscript_ndvi = """
            //VERSION=3
            function setup() {
                return {
                    input: [{
                        bands: ["B04", "B08"],
                        units: "REFLECTANCE"
                    }],
                    output: {
                        bands: 3,
                        sampleType: "AUTO"
                    }
                };
            }

            function evaluatePixel(sample) {
                // Calculate NDVI
                let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
                
                // Color map based on standard NDVI interpretation
                if (ndvi < -0.2) return [0, 0, 0.3];       // Water - Dark Blue
                if (ndvi < 0.0) return [0.5, 0.4, 0.3];    // Bare Soil/Urban - Brown
                if (ndvi < 0.1) return [0.8, 0.8, 0.4];    // Sparse Vegetation - Yellow
                if (ndvi < 0.3) return [0.5, 0.7, 0.3];    // Moderate Vegetation - Light Green
                if (ndvi < 0.5) return [0.3, 0.6, 0.2];    // Healthy Vegetation - Green
                if (ndvi < 0.7) return [0.1, 0.5, 0.1];    // Dense Vegetation - Dark Green
                return [0.0, 0.4, 0.0];                    // Very Dense Vegetation - Very Dark Green
            }
            """
            
            # Calculate time interval
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            self.logger.info(f"Fetching NDVI imagery from {start_date.date()} to {end_date.date()}")
            
            # Create request with L2A data
            request = SentinelHubRequest(
                evalscript=evalscript_ndvi,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                        mosaicking_order=MosaickingOrder.MOST_RECENT
                    )
                ],
                responses=[
                    SentinelHubRequest.output_response('default', MimeType.PNG)
                ],
                bbox=bbox,
                size=size,
                config=self.config
            )
            
            # Download image
            self.logger.info("Downloading NDVI image...")
            image_data = request.get_data()
            
            if not image_data or len(image_data) == 0:
                self.logger.warning("No image data received for NDVI")
                return []
                
            image_array = image_data[0]
            
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"{region_name}_ndvi_{timestamp}.png"
            
            # Convert to PIL Image and save with NDVI legend
            self._save_image_with_legend(image_array, output_path, "NDVI Vegetation Index", self._get_ndvi_legend())
            
            self.logger.info(f"NDVI image saved: {output_path}")
            return [output_path]
            
        except Exception as e:
            self.logger.warning(f"NDVI fetch failed: {str(e)}")
            return []
    
    def _get_true_color_legend(self):
        """Create legend for true color image"""
        return {
            "title": "True Color Satellite Imagery",
            "description": "Natural color representation using Red (B04), Green (B03), Blue (B02) bands",
            "items": [
                {"color": (0, 100, 0), "label": "Vegetation - Green"},
                {"color": (100, 100, 100), "label": "Urban Areas - Gray"}, 
                {"color": (0, 0, 150), "label": "Water Bodies - Blue"},
                {"color": (150, 150, 100), "label": "Bare Soil - Brown"}
            ]
        }
    
    def _get_ndvi_legend(self):
        """Create legend for NDVI image"""
        return {
            "title": "NDVI Vegetation Index",
            "description": "Normalized Difference Vegetation Index: -1.0 to +1.0",
            "items": [
                {"color": (0, 0, 100), "label": "Water (< -0.2)"},
                {"color": (150, 120, 100), "label": "Bare Soil/Urban (0.0 to 0.1)"},
                {"color": (200, 200, 100), "label": "Sparse Vegetation (0.1 to 0.3)"},
                {"color": (100, 180, 100), "label": "Moderate Vegetation (0.3 to 0.5)"},
                {"color": (0, 150, 0), "label": "Dense Vegetation (0.5 to 0.7)"},
                {"color": (0, 100, 0), "label": "Very Dense Vegetation (> 0.7)"}
            ]
        }
    
    def _save_image_with_legend(self, image_array, output_path, image_type, legend_info):
        """Save image with embedded legend"""
        try:
            # Convert to uint8 appropriately
            if np.issubdtype(image_array.dtype, np.floating):
                image_data_uint8 = (np.clip(image_array, 0, 1) * 255).astype(np.uint8)
            else:
                image_data_uint8 = image_array.astype(np.uint8)
            
            # Create PIL image
            main_image = Image.fromarray(image_data_uint8)
            
            # Create legend image
            legend_image = self._create_legend_image(legend_info, main_image.width)
            
            # Combine main image and legend
            combined_height = main_image.height + legend_image.height
            combined_image = Image.new('RGB', (main_image.width, combined_height), 'white')
            
            # Paste main image
            combined_image.paste(main_image, (0, 0))
            
            # Paste legend
            combined_image.paste(legend_image, (0, main_image.height))
            
            # Save combined image
            combined_image.save(output_path, 'PNG', optimize=True, quality=95)
            
            self.logger.info(f"{image_type} image with legend saved: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving {image_type} image with legend: {str(e)}")
            # Fallback: save without legend
            image_data_uint8 = image_array.astype(np.uint8) if not np.issubdtype(image_array.dtype, np.floating) else (np.clip(image_array, 0, 1) * 255).astype(np.uint8)
            Image.fromarray(image_data_uint8).save(output_path, 'PNG')
    
    def _create_legend_image(self, legend_info, width):
        """Create a legend image"""
        height = 180  # Fixed height for legend
        legend_img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(legend_img)
        
        try:
            # Try to use a font
            try:
                font_large = ImageFont.truetype("arial.ttf", 16)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                # Fallback to default font
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw title
            title = legend_info["title"]
            draw.text((10, 10), title, fill='black', font=font_large)
            
            # Draw description
            description = legend_info["description"]
            draw.text((10, 35), description, fill='darkgray', font=font_small)
            
            # Draw legend items
            y_offset = 60
            for i, item in enumerate(legend_info["items"]):
                # Draw color box
                box_x = 10
                box_y = y_offset
                box_size = 20
                draw.rectangle([box_x, box_y, box_x + box_size, box_y + box_size], 
                              fill=tuple(item["color"]), outline='black', width=1)
                
                # Draw label
                label_x = box_x + box_size + 10
                label_y = box_y + 6
                draw.text((label_x, label_y), item["label"], fill='black', font=font_small)
                
                y_offset += 30
            
            # Add border
            draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
            
        except Exception as e:
            self.logger.warning(f"Could not create detailed legend: {str(e)}")
            # Simple fallback legend
            draw.text((10, 10), legend_info["title"], fill='black')
            draw.text((10, 30), legend_info["description"], fill='gray')
        
        return legend_img

# Simple downloader for testing
class SimpleSatelliteDownloader:
    """Simple satellite image downloader for testing without Sentinel Hub"""
    
    def __init__(self):
        self.logger = logging.getLogger("SimpleSatelliteDownloader")
        self.output_dir = Path("data/satellite")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_sample_imagery(self, region_name):
        """Create realistic sample satellite images with legends"""
        try:
            self.logger.info(f"Creating realistic sample imagery for: {region_name}")
            
            region_dir = self.output_dir / region_name
            region_dir.mkdir(exist_ok=True)
            
            # Create realistic sample images
            sample_files = []
            
            # Create a realistic true color image
            true_color_path = region_dir / f"{region_name}_truecolor_sample.png"
            self._create_realistic_image_with_legend(true_color_path, (600, 400), "truecolor", region_name)
            sample_files.append(true_color_path)
            
            # Create a realistic NDVI image
            ndvi_path = region_dir / f"{region_name}_ndvi_sample.png"
            self._create_realistic_image_with_legend(ndvi_path, (600, 400), "ndvi", region_name)
            sample_files.append(ndvi_path)
            
            self.logger.info(f"SAMPLE_IMAGERY_CREATED - {len(sample_files)} realistic sample images with legends")
            return sample_files
            
        except Exception as e:
            self.logger.error(f"SAMPLE_IMAGERY_ERROR: {str(e)}")
            return []
    
    def _create_realistic_image_with_legend(self, filepath, size, image_type, region_name):
        """Create realistic sample satellite image with legend"""
        from PIL import Image, ImageDraw
        
        # Create main image
        if image_type == "truecolor":
            main_img = self._create_realistic_true_color(size, region_name)
            legend_info = {
                "title": "True Color Satellite Imagery",
                "description": "Natural color representation (Sample Data)",
                "items": [
                    {"color": (0, 100, 0), "label": "Vegetation - Green"},
                    {"color": (100, 100, 100), "label": "Urban Areas - Gray"}, 
                    {"color": (0, 0, 150), "label": "Water Bodies - Blue"},
                    {"color": (150, 150, 100), "label": "Bare Soil - Brown"}
                ]
            }
        else:
            main_img = self._create_realistic_ndvi(size, region_name)
            legend_info = {
                "title": "NDVI Vegetation Index (Sample Data)",
                "description": "Normalized Difference Vegetation Index",
                "items": [
                    {"color": (0, 0, 100), "label": "Water (< -0.2)"},
                    {"color": (150, 120, 100), "label": "Bare Soil/Urban (0.0 to 0.1)"},
                    {"color": (200, 200, 100), "label": "Sparse Vegetation (0.1 to 0.3)"},
                    {"color": (100, 180, 100), "label": "Moderate Vegetation (0.3 to 0.5)"},
                    {"color": (0, 150, 0), "label": "Dense Vegetation (0.5 to 0.7)"},
                    {"color": (0, 100, 0), "label": "Very Dense Vegetation (> 0.7)"}
                ]
            }
        
        # Create legend
        legend_img = self._create_legend_image(legend_info, size[0])
        
        # Combine images
        combined_height = main_img.height + legend_img.height
        combined_image = Image.new('RGB', (size[0], combined_height), 'white')
        combined_image.paste(main_img, (0, 0))
        combined_image.paste(legend_img, (0, main_img.height))
        
        combined_image.save(filepath, 'PNG', quality=95)
    
    def _create_realistic_true_color(self, size, region_name):
        """Create realistic true color image"""
        from PIL import Image, ImageDraw
        import random
        
        img = Image.new('RGB', size, color=(100, 150, 200))  # Sky blue background
        draw = ImageDraw.Draw(img)
        
        # Draw realistic terrain
        # Mountains
        for i in range(3):
            base_y = random.randint(size[1]//2, size[1]-50)
            peak_x = random.randint(100, size[0]-100)
            peak_y = base_y - random.randint(80, 120)
            
            points = [
                (peak_x-100, base_y),
                (peak_x, peak_y), 
                (peak_x+100, base_y)
            ]
            draw.polygon(points, fill=(80, 100, 60))
        
        # Forests
        for i in range(15):
            x, y = random.randint(0, size[0]-1), random.randint(size[1]//3, size[1]-30)
            radius = random.randint(15, 35)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=(30, 80, 40))
        
        # Water
        for i in range(2):
            x, y = random.randint(0, size[0]//2), random.randint(size[1]//2, size[1]-80)
            width, height = random.randint(80, 180), random.randint(40, 100)
            draw.ellipse([x, y, x+width, y+height], fill=(50, 80, 180))
        
        # Urban areas
        for i in range(4):
            x, y = random.randint(size[0]//2, size[0]-50), random.randint(size[1]//2, size[1]-50)
            width, height = random.randint(40, 80), random.randint(30, 60)
            draw.rectangle([x, y, x+width, y+height], fill=(120, 120, 120))
        
        return img
    
    def _create_realistic_ndvi(self, size, region_name):
        """Create realistic NDVI image"""
        from PIL import Image, ImageDraw
        import random
        
        img = Image.new('RGB', size, color=(0, 0, 100))  # Water background
        draw = ImageDraw.Draw(img)
        
        # Water bodies
        for i in range(2):
            x, y = random.randint(0, size[0]//3), random.randint(size[1]//2, size[1]-100)
            width, height = random.randint(100, 200), random.randint(60, 120)
            draw.ellipse([x, y, x+width, y+height], fill=(0, 0, 150))
        
        # Vegetation gradients (circular patterns)
        center_x, center_y = size[0]//2, size[1]//2
        
        # Very dense vegetation (center)
        draw.ellipse([center_x-80, center_y-80, center_x+80, center_y+80], fill=(0, 100, 0))
        
        # Dense vegetation ring
        draw.ellipse([center_x-150, center_y-150, center_x+150, center_y+150], outline=(0, 150, 0), width=40)
        
        # Moderate vegetation ring  
        draw.ellipse([center_x-220, center_y-220, center_x+220, center_y+220], outline=(100, 180, 100), width=40)
        
        # Sparse vegetation ring
        draw.ellipse([center_x-290, center_y-290, center_x+290, center_y+290], outline=(200, 200, 100), width=40)
        
        # Bare soil areas
        for i in range(3):
            x, y = random.randint(size[0]-200, size[0]-50), random.randint(50, size[1]//2)
            width, height = random.randint(60, 120), random.randint(40, 80)
            draw.rectangle([x, y, x+width, y+height], fill=(150, 120, 100))
        
        return img
    
    def _create_legend_image(self, legend_info, width):
        """Create a legend image for sample data"""
        height = 150
        legend_img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(legend_img)
        
        # Draw title
        draw.text((10, 10), legend_info["title"], fill='black')
        
        # Draw description
        draw.text((10, 30), legend_info["description"], fill='darkgray')
        
        # Draw legend items
        y_offset = 55
        for i, item in enumerate(legend_info["items"]):
            # Color box
            box_x = 10
            box_y = y_offset
            box_size = 15
            draw.rectangle([box_x, box_y, box_x + box_size, box_y + box_size], 
                          fill=tuple(item["color"]), outline='black', width=1)
            
            # Label
            label_x = box_x + box_size + 5
            label_y = box_y + 2
            draw.text((label_x, label_y), item["label"], fill='black')
            
            y_offset += 20
        
        # Border
        draw.rectangle([0, 0, width-1, height-1], outline='black', width=1)
        
        return legend_img