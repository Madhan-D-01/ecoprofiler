#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import os

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from scripts.fetch_glad_alerts import GLADAlertsFetcher
from scripts.registry_search import CompanyRegistrySearch
from scripts.reddit_scraper import RedditScraper
from scripts.satellite_fetch import SatelliteImageryFetcher, SimpleSatelliteDownloader
from scripts.generate_pdf import generate_pdf_report
from config.settings import REDDIT_CONFIG, SENTINELHUB_CONFIG, validate_config

def main():
    parser = argparse.ArgumentParser(description='EcoProfiler - Environmental Crime OSINT Tool')
    
    # Input methods
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--place', type=str, help='Place name (e.g., "Sumatra")')
    input_group.add_argument('--coords', type=str, help='Coordinates "lat,lon" (e.g., "1.23,-56.77")')
    
    # Optional parameters
    parser.add_argument('--radius', type=int, default=20, help='Search radius in km (default: 20)')
    parser.add_argument('--days', type=int, default=30, help='Days to look back (default: 30)')
    parser.add_argument('--include-osm', action='store_true', help='Include OSM business search')
    parser.add_argument('--include-satellite', action='store_true', help='Include satellite imagery fetch')
    parser.add_argument('--report', action='store_true', help='Generate PDF report')
    
    args = parser.parse_args()
    
    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        print("Configuration errors found:")
        for error in config_errors:
            print(f"  - {error}")
        print("Please check your .env file and API credentials.")
        sys.exit(1)
    
    # Setup logging
    region_name = args.place if args.place else f"coords_{args.coords.replace(',', '_').replace('.', '')}"
    logger = setup_logger("EcoProfiler", region_name)
    
    logger.info(f"Starting EcoProfiler analysis for: {region_name}")
    
    try:
        # Parse coordinates
        if args.coords:
            lat, lon = map(float, args.coords.split(','))
        else:
            lat, lon = geocode_place(args.place)
        
        # Initialize modules
        glad_fetcher = GLADAlertsFetcher()
        company_search = CompanyRegistrySearch()
        reddit_scraper = RedditScraper(**REDDIT_CONFIG)
        
        # Data collection results
        data = {
            'glad_alerts': None,
            'companies': [],
            'osm_businesses': [],
            'reddit_posts': [],
            'satellite_images': []
        }
        
        # 1. Fetch GLAD alerts
        logger.info("Step 1: Fetching GLAD forest loss alerts")
        data['glad_alerts'] = glad_fetcher.get_glad_alerts(lat, lon, args.radius, args.days)
        if not data['glad_alerts'].empty:
            glad_fetcher.save_alerts(data['glad_alerts'], region_name)
        
        # 2. Company registry search
        logger.info("Step 2: Searching company registries")
        data['companies'], data['osm_businesses'] = company_search.search_companies_in_region(lat, lon, args.radius)
        company_search.save_companies(data['companies'], data['osm_businesses'], region_name)
        
        # 3. Reddit scraping
        logger.info("Step 3: Scraping Reddit for environmental discussions")
        place_name = args.place if args.place else f"coordinates {args.coords}"
        data['reddit_posts'] = reddit_scraper.search_region_posts(place_name, args.days)
        reddit_scraper.save_reddit_data(data['reddit_posts'], region_name)
        
        # 4. Satellite imagery (UPDATED FOR REAL IMAGERY)
        if args.include_satellite:
            logger.info("Step 4: Fetching satellite imagery")
            
            # Check if Sentinel Hub credentials are available
            if SENTINELHUB_CONFIG['client_id'] and SENTINELHUB_CONFIG['client_secret']:
                logger.info("Using real Sentinel Hub API for satellite imagery")
                try:
                    satellite_fetcher = SatelliteImageryFetcher(
                        client_id=SENTINELHUB_CONFIG['client_id'],
                        client_secret=SENTINELHUB_CONFIG['client_secret']
                    )
                    data['satellite_images'] = satellite_fetcher.fetch_region_imagery(
                        lat, lon, args.radius, region_name, args.days
                    )
                    logger.info(f"Real satellite imagery downloaded: {len(data['satellite_images'])} files")
                except Exception as e:
                    logger.error(f"Real satellite imagery failed: {str(e)}")
                    logger.info("Falling back to sample imagery")
                    sample_downloader = SimpleSatelliteDownloader()
                    data['satellite_images'] = sample_downloader.fetch_sample_imagery(region_name)
            else:
                logger.warning("Sentinel Hub credentials not found. Using sample imagery.")
                sample_downloader = SimpleSatelliteDownloader()
                data['satellite_images'] = sample_downloader.fetch_sample_imagery(region_name)
            
            logger.info(f"Satellite imagery: {len(data['satellite_images'])} files downloaded")
        
        # 5. Generate PDF report (if requested)
        if args.report:
            logger.info("Step 5: Generating PDF report")
            try:
                report_path = generate_pdf_report(data, region_name)
                logger.info(f"PDF report generated: {report_path}")
            except Exception as e:
                logger.error(f"PDF report generation failed: {str(e)}")
        
        logger.info(f"EcoProfiler analysis complete for {region_name}")
        print(f"✅ Analysis complete! Data saved in data/ directory.")
        print(f"📊 Run 'streamlit run dashboard/app.py' to view results.")
        
        return data
        
    except Exception as e:
        logger.error(f"ECO_PROFILER_ERROR: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def geocode_place(place_name):
    """Geocode place name to coordinates (simplified)"""
    # In real implementation, use geopy or similar
    geocoding_map = {
        'sumatra': (0.7893, 101.3431),
        'amazon': (-3.4653, -62.2159),
        'borneo': (0.9619, 114.5548),
        'congo': (-4.0383, 21.7587),
        'default': (0.0, 0.0)
    }
    
    place_lower = place_name.lower()
    for key, coords in geocoding_map.items():
        if key in place_lower:
            return coords
    
    return geocoding_map['default']

if __name__ == "__main__":
    main()