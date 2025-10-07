import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import os
import logging
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.logger import setup_logger
from src.visualizations.map import create_alert_map, create_satellite_overlay
from src.visualizations.graph import create_entity_graph
from src.visualizations.reddit_plot import create_reddit_timeline, create_sentiment_chart

# Fix the PDF import - try multiple ways
try:
    from scripts.generate_pdf import generate_pdf_report
except ImportError:
    try:
        # Alternative import path
        from generate_pdf import generate_pdf_report
    except ImportError:
        # Create a fallback function
        def generate_pdf_report(data, region_name):
            st.error("PDF generation not available")
            return None

# Configure page
st.set_page_config(
    page_title="EcoProfiler - Environmental Crime Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EcoProfilerDashboard:
    def __init__(self):
        self.logger = setup_logger("dashboard")
        self.data_dir = project_root / "data"
        self.current_region = None
        
    def load_data(self, region_name):
        """Load all data for the specified region"""
        self.current_region = region_name
        data = {}
        
        try:
            # Load GLAD alerts
            glad_path = self.data_dir / "alerts" / f"{region_name}_glad.csv"
            if glad_path.exists():
                data['glad_alerts'] = pd.read_csv(glad_path)
                if 'date' in data['glad_alerts'].columns:
                    data['glad_alerts']['date'] = pd.to_datetime(data['glad_alerts']['date'], errors='coerce')
            else:
                data['glad_alerts'] = pd.DataFrame()
                
            # Load company data
            company_path = self.data_dir / "companies" / f"{region_name}_companies.json"
            if company_path.exists():
                with open(company_path, 'r', encoding='utf-8') as f:
                    data['companies'] = json.load(f)
            else:
                data['companies'] = []
                
            # Load OSM data
            osm_path = self.data_dir / "companies" / f"{region_name}_osm.json"
            if osm_path.exists():
                with open(osm_path, 'r', encoding='utf-8') as f:
                    data['osm_businesses'] = json.load(f)
            else:
                data['osm_businesses'] = []
                
            # Load Reddit data
            reddit_path = self.data_dir / "reddit" / f"{region_name}_praw_enriched.json"
            if reddit_path.exists():
                with open(reddit_path, 'r', encoding='utf-8') as f:
                    data['reddit_posts'] = json.load(f)
            else:
                data['reddit_posts'] = []
                
            # Load satellite metadata with case-insensitive globbing - IMPROVED VERSION
            sat_dir = self.data_dir / "satellite" / region_name
            data['satellite_images'] = []
            if sat_dir.exists():
                # More comprehensive image extensions including uppercase
                image_extensions = [
                    '*.png', '*.jpg', '*.jpeg', '*.tif', '*.tiff', '*.bmp', '*.gif',
                    '*.PNG', '*.JPG', '*.JPEG', '*.TIF', '*.TIFF', '*.BMP', '*.GIF'
                ]
                
                for ext in image_extensions:
                    try:
                        found_files = list(sat_dir.glob(ext))
                        data['satellite_images'].extend(found_files)
                    except Exception as e:
                        self.logger.warning(f"Error globbing {ext} in {sat_dir}: {e}")
                
                # Remove duplicates and sort
                data['satellite_images'] = sorted(set(data['satellite_images']))
                
                self.logger.info(f"Found {len(data['satellite_images'])} satellite image(s) in {sat_dir}")
                for img in data['satellite_images']:
                    self.logger.debug(f"Satellite image: {img}")
                    
                # Also look for subdirectories
                for subdir in sat_dir.iterdir():
                    if subdir.is_dir():
                        self.logger.info(f"Found satellite subdirectory: {subdir}")
                        for ext in image_extensions:
                            try:
                                found_files = list(subdir.glob(ext))
                                data['satellite_images'].extend(found_files)
                                self.logger.info(f"Found {len(found_files)} images in {subdir} with {ext}")
                            except Exception as e:
                                self.logger.warning(f"Error globbing {ext} in {subdir}: {e}")
                
            else:
                self.logger.warning(f"Satellite directory does not exist: {sat_dir}")
            
            self.logger.info(f"Successfully loaded data for region: {region_name}")
            
        except Exception as e:
            self.logger.error(f"Error loading data for {region_name}: {str(e)}")
            st.error(f"Error loading data: {str(e)}")
            
        return data

    def render_header(self):
        """Render the dashboard header"""
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("🌍 EcoProfiler")
            st.subheader("Global Environmental Crime Intelligence Platform")
        with col2:
            st.metric("Active Region", self.current_region if self.current_region else "None")
            st.metric("Data Sources", "6+ APIs")

    def render_sidebar(self, data):
        """Render the sidebar controls and summary"""
        st.sidebar.header("🔍 Analysis Controls")
        
        # Region selector
        available_regions = self.get_available_regions()
        selected_region = st.sidebar.selectbox(
            "Select Analysis Region",
            options=available_regions,
            index=0 if available_regions else None
        )
        
        if selected_region and selected_region != self.current_region:
            data = self.load_data(selected_region)
            
        # Data summary
        st.sidebar.header("📊 Data Summary")
        
        if data['glad_alerts'] is not None and not data['glad_alerts'].empty:
            st.sidebar.metric("Forest Loss Alerts", len(data['glad_alerts']))
        else:
            st.sidebar.metric("Forest Loss Alerts", 0)
            
        st.sidebar.metric("Companies Identified", len(data['companies']))
        st.sidebar.metric("Local Businesses", len(data['osm_businesses']))
        st.sidebar.metric("Social Media Posts", len(data['reddit_posts']))
        
        # Risk assessment
        risk_score = self.calculate_risk_score(data)
        st.sidebar.header("🚨 Risk Assessment")
        st.sidebar.progress(risk_score / 100)
        st.sidebar.write(f"Overall Risk: {risk_score:.1f}/100")
        
        # Debug toggle
        if st.sidebar.checkbox("🔧 Debug Mode", value=False):
            st.session_state.debug_mode = True
        else:
            st.session_state.debug_mode = False
        
        return data

    def get_available_regions(self):
        """Get list of available regions with data"""
        regions = set()
        
        # Check alerts directory
        alerts_dir = self.data_dir / "alerts"
        if alerts_dir.exists():
            for file in alerts_dir.glob("*_glad.csv"):
                regions.add(file.stem.replace("_glad", ""))
                
        # Check companies directory
        companies_dir = self.data_dir / "companies"
        if companies_dir.exists():
            for file in companies_dir.glob("*_companies.json"):
                regions.add(file.stem.replace("_companies", ""))
                
        return sorted(list(regions))

    def calculate_risk_score(self, data):
        """Calculate overall environmental risk score"""
        score = 0
        
        # GLAD alerts contribute 40%
        if data['glad_alerts'] is not None and not data['glad_alerts'].empty:
            alert_count = len(data['glad_alerts'])
            score += min(40, alert_count / 10)  # Normalize
            
        # Company sanctions contribute 30%
        sanctioned_companies = [c for c in data['companies'] if c.get('sanctioned', False)]
        score += min(30, len(sanctioned_companies) * 10)
        
        # Reddit sentiment contributes 20%
        if data['reddit_posts']:
            negative_posts = [p for p in data['reddit_posts'] if p.get('sentiment', 0) < -0.1]
            score += min(20, len(negative_posts) / len(data['reddit_posts']) * 20)
            
        # OSM industrial sites contribute 10%
        industrial_osm = [b for b in data['osm_businesses'] 
                         if any(tag in str(b.get('tags', {})).lower() 
                               for tag in ['industrial', 'mining', 'logging', 'quarry'])]
        score += min(10, len(industrial_osm) * 2)
        
        return min(100, score)

    def render_main_dashboard(self, data):
        """Render the main dashboard content"""
        try:
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🗺️ Interactive Map", 
                "🏢 Company Registry", 
                "📈 Social Intelligence",
                "🔗 Entity Network",
                "📄 Intelligence Report"
            ])
            
            with tab1:
                self.render_map_tab(data)
                
            with tab2:
                self.render_companies_tab(data)
                
            with tab3:
                self.render_social_tab(data)
                
            with tab4:
                self.render_network_tab(data)
                
            with tab5:
                self.render_report_tab(data)
        except Exception as e:
            st.error(f"Error rendering dashboard: {str(e)}")
            self.logger.error(f"Dashboard rendering error: {str(e)}")

    def render_map_tab(self, data):
        """Render the interactive map tab with improved layout and satellite display"""
        try:
            # Create main layout with better spacing
            st.subheader("🌍 Environmental Intelligence Map")
            
            # Use columns with better ratio
            map_col, data_col = st.columns([2, 1])
            
            with map_col:
                st.subheader("🗺️ Interactive Map")
                
                if data['glad_alerts'] is not None and not data['glad_alerts'].empty:
                    # Create Folium map
                    alert_map = create_alert_map(data['glad_alerts'], data.get('osm_businesses', []))
                    folium_static(alert_map, width=650, height=500)
                else:
                    st.warning("No alert data available for mapping")
                    # Show a placeholder map
                    placeholder_map = folium.Map(location=[0, 0], zoom_start=2)
                    folium_static(placeholder_map, width=650, height=400)
            
            with data_col:
                # Satellite Imagery Section - Improved layout
                st.subheader("🛰️ Satellite Analysis")
                
                if data['satellite_images']:
                    # Debug information in debug mode
                    if st.session_state.get('debug_mode', False):
                        st.write(f"🔍 Debug: Found {len(data['satellite_images'])} satellite files:")
                        for i, img_path in enumerate(data['satellite_images']):
                            st.code(f"{i+1}. {img_path}")
                        
                        # Add image diagnostics in debug mode
                        if data['satellite_images']:
                            st.subheader("🩺 Image Diagnostics")
                            test_img = data['satellite_images'][0]
                            self.check_image_format(test_img)
                    
                    # Filter for actual image files
                    image_files = [img for img in data['satellite_images'] 
                                  if str(img).lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif'))]
                    
                    if image_files:
                        st.success(f"✅ Found {len(image_files)} satellite images")
                        
                        # Group images by type with more flexible pattern matching
                        true_color_images = [img for img in image_files 
                                           if any(term in str(img).lower() 
                                                 for term in ['truecolor', 'true_color', 'natural', 'rgb'])]
                        ndvi_images = [img for img in image_files 
                                     if any(term in str(img).lower() 
                                           for term in ['ndvi', 'vegetation', 'health'])]
                        false_color_images = [img for img in image_files 
                                            if any(term in str(img).lower() 
                                                  for term in ['falsecolor', 'false_color', 'nir'])]
                        
                        # Display True Color images
                        if true_color_images:
                            with st.expander("🎨 True Color Imagery", expanded=True):
                                st.info(f"Found {len(true_color_images)} true color images")
                                for img_path in true_color_images[:3]:  # Show max 3
                                    self._display_satellite_image(img_path, "True Color")
                        
                        # Display NDVI images  
                        if ndvi_images:
                            with st.expander("🌿 Vegetation Analysis (NDVI)", expanded=True):
                                st.info(f"Found {len(ndvi_images)} vegetation analysis images")
                                for img_path in ndvi_images[:3]:  # Show max 3
                                    self._display_satellite_image(img_path, "NDVI")
                        
                        # Display False Color images
                        if false_color_images:
                            with st.expander("🌈 False Color Imagery", expanded=False):
                                st.info(f"Found {len(false_color_images)} false color images")
                                for img_path in false_color_images[:2]:
                                    self._display_satellite_image(img_path, "False Color")
                        
                        # Show remaining images if any
                        other_images = [img for img in image_files 
                                      if img not in true_color_images + ndvi_images + false_color_images]
                        if other_images:
                            with st.expander("📡 Other Satellite Data", expanded=False):
                                st.info(f"Found {len(other_images)} other satellite images")
                                for img_path in other_images[:3]:
                                    self._display_satellite_image(img_path, "Satellite")
                    
                    else:
                        # Check for text files if no images
                        text_files = [img for img in data['satellite_images'] 
                                     if str(img).endswith('.txt')]
                        if text_files:
                            st.info("📄 Sample satellite data available")
                            for img_path in text_files[:2]:
                                try:
                                    with open(img_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    with st.expander(f"📄 {img_path.name}"):
                                        st.text(content)
                                except Exception as e:
                                    st.info(f"Sample data: {img_path.name}")
                        else:
                            st.info("🛰️ No satellite imagery files found")
                else:
                    st.info("🛰️ No satellite imagery available")
                
                # Add spacing
                st.markdown("---")
                
                # Alert Statistics Section - Improved layout
                st.subheader("📊 Forest Alert Statistics")
                
                if data['glad_alerts'] is not None and not data['glad_alerts'].empty:
                    try:
                        # Calculate recent alerts
                        recent_alerts = data['glad_alerts'][
                            pd.to_datetime(data['glad_alerts']['date']) > 
                            (datetime.now() - timedelta(days=30))
                        ]
                        
                        # Key metrics in a compact layout
                        metric_col1, metric_col2 = st.columns(2)
                        with metric_col1:
                            st.metric(
                                "Last 30 Days", 
                                len(recent_alerts),
                                delta=f"{len(recent_alerts) - len(data['glad_alerts']) + len(recent_alerts)} total"
                            )
                        with metric_col2:
                            st.metric("Total Alerts", len(data['glad_alerts']))
                        
                        # Additional stats
                        with st.expander("📈 Detailed Statistics", expanded=False):
                            # Alert timeline
                            try:
                                daily_alerts = data['glad_alerts'].groupby(
                                    data['glad_alerts']['date'].dt.date
                                ).size().reset_index(name='count')
                                
                                if len(daily_alerts) > 1:
                                    fig = px.line(daily_alerts, x='date', y='count', 
                                                 title="Daily Forest Loss Alerts",
                                                 height=200)
                                    fig.update_layout(
                                        margin=dict(l=20, r=20, t=30, b=20),
                                        xaxis_title="",
                                        yaxis_title="Alerts"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("📅 Single day of alerts")
                                    
                                # Alert summary
                                if 'confidence' in data['glad_alerts'].columns:
                                    avg_confidence = data['glad_alerts']['confidence'].mean()
                                    st.metric("Average Confidence", f"{avg_confidence:.2f}")
                                    
                            except Exception as e:
                                st.warning("⚠️ Could not generate detailed statistics")
                                
                    except Exception as e:
                        st.error(f"❌ Error processing alert statistics: {str(e)}")
                else:
                    st.info("📊 No alert data available")
                
                # Quick Reference Guide
                with st.expander("📖 Interpretation Guide", expanded=False):
                    st.subheader("True Color Imagery")
                    st.write("""
                    - **Green**: Vegetation and forests
                    - **Blue**: Water bodies  
                    - **Gray/Brown**: Urban areas, bare soil
                    - **White**: Clouds
                    """)
                    
                    st.subheader("NDVI Vegetation Index")
                    st.write("""
                    - **Dark Blue**: Water
                    - **Brown**: Bare soil/urban (0.0-0.1)
                    - **Yellow**: Sparse vegetation (0.1-0.3)
                    - **Light Green**: Moderate vegetation (0.3-0.5)
                    - **Green**: Healthy vegetation (0.5-0.7)
                    - **Dark Green**: Dense vegetation (>0.7)
                    """)
                    
        except Exception as e:
            st.error(f"❌ Error rendering map tab: {str(e)}")
            self.logger.error(f"Map tab error: {str(e)}")

    def _display_satellite_image(self, img_path, image_type):
        """Helper method to display satellite images with proper error handling"""
        try:
            self.logger.info(f"Attempting to display image: {img_path}")

            if not img_path.exists():
                st.warning(f"❌ Image file not found: {img_path}")
                self.logger.warning(f"Missing image file: {img_path}")
                return

            file_size = img_path.stat().st_size
            if file_size == 0:
                st.warning(f"⚠️ Empty image file: {img_path.name}")
                self.logger.warning(f"Empty image: {img_path}")
                return
                
            if file_size < 1000:  # Less than 1KB likely problematic
                st.warning(f"⚠️ Very small image file: {img_path.name} ({file_size} bytes)")

            # Try multiple methods to display the image
            try:
                # Method 1: Direct file path (should work for most images)
                st.image(str(img_path), caption=f"{image_type}: {img_path.name}", use_column_width=True)
                
            except Exception as e:
                self.logger.warning(f"Direct image display failed, trying PIL: {e}")
                try:
                    # Method 2: Use PIL to open and display
                    from PIL import Image
                    image = Image.open(img_path)
                    st.image(image, caption=f"{image_type}: {img_path.name}", use_column_width=True)
                except Exception as pil_error:
                    self.logger.warning(f"PIL display failed, trying matplotlib: {pil_error}")
                    try:
                        # Method 3: Use matplotlib for problematic images
                        import matplotlib.pyplot as plt
                        import matplotlib.image as mpimg
                        
                        img = mpimg.imread(img_path)
                        fig, ax = plt.subplots(figsize=(10, 8))
                        ax.imshow(img)
                        ax.axis('off')
                        st.pyplot(fig)
                        plt.close(fig)
                    except Exception as plt_error:
                        st.error(f"❌ All display methods failed for {img_path.name}")
                        self.logger.error(f"All image display methods failed: {plt_error}")
                        
                        # Show file info as fallback
                        st.info(f"📄 File: {img_path.name}")
                        st.info(f"📏 Size: {file_size} bytes")
                        st.info(f"📁 Path: {img_path}")

            # Show image info
            file_size_kb = file_size / 1024
            file_size_mb = file_size_kb / 1024
            
            if file_size_mb > 1:
                size_display = f"{file_size_mb:.1f} MB"
            else:
                size_display = f"{file_size_kb:.1f} KB"
                
            st.caption(f"📁 {img_path.name} | Size: {size_display}")

            # Add type-specific information
            if image_type == "True Color":
                st.caption("🎨 Natural color representation - shows landscape as human eyes see it")
            elif image_type == "NDVI":
                st.caption("🌿 Vegetation health analysis - red/brown indicates stressed vegetation")
            elif image_type == "False Color":
                st.caption("🌈 Infrared-enhanced - healthy vegetation appears bright red")
            else:
                st.caption("🛰️ Satellite imagery data")

        except Exception as e:
            st.error(f"❌ Cannot display {img_path.name}: {str(e)}")
            self.logger.error(f"Failed to display image {img_path}: {str(e)}")

    def check_image_format(self, img_path):
        """Diagnostic method to check image format and properties"""
        try:
            from PIL import Image
            import io
            
            st.subheader("🔍 Image Diagnostics")
            
            # Check file properties
            st.write(f"**File Info:**")
            st.write(f"- Path: `{img_path}`")
            st.write(f"- Exists: `{img_path.exists()}`")
            st.write(f"- Size: `{img_path.stat().st_size} bytes`")
            
            # Try to open with PIL
            try:
                with Image.open(img_path) as img:
                    st.write(f"**PIL Image Info:**")
                    st.write(f"- Format: `{img.format}`")
                    st.write(f"- Mode: `{img.mode}`")
                    st.write(f"- Size: `{img.size}`")
                    
                    # Check if it's a valid image by trying to convert to bytes
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    st.write(f"- Can convert to bytes: `{len(buf.getvalue()) > 0}`")
                    
                    return True
            except Exception as pil_error:
                st.error(f"PIL cannot open image: {pil_error}")
                return False
                
        except Exception as e:
            st.error(f"Diagnostic failed: {e}")
            return False

    def render_companies_tab(self, data):
        """Render the company registry tab"""
        try:
            st.subheader("🏢 Corporate Entity Registry")
            
            if not data['companies']:
                st.info("No company data available")
                return
                
            # Create company dataframe for display
            company_df = pd.DataFrame(data['companies'])
            
            # Display company cards
            for idx, company in enumerate(data['companies']):
                with st.expander(f"🏭 {company.get('name', 'Unknown')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Basic Info**")
                        st.write(f"Name: {company.get('name', 'N/A')}")
                        st.write(f"LEI: {company.get('lei', 'N/A')}")
                        st.write(f"Founded: {company.get('founded', 'N/A')}")
                        
                    with col2:
                        st.write("**Location & Status**")
                        st.write(f"Country: {company.get('country', 'N/A')}")
                        st.write(f"Status: {company.get('status', 'N/A')}")
                        if company.get('sanctioned'):
                            st.error("🚨 SANCTIONED ENTITY")
                        if company.get('shell_company'):
                            st.warning("⚠️ SHELL COMPANY RISK")
                            
                    with col3:
                        st.write("**Environmental Risk**")
                        # Calculate risk factors
                        risk_factors = []
                        if company.get('sanctioned'):
                            risk_factors.append("Sanctions")
                        if company.get('shell_company'):
                            risk_factors.append("Shell Company")
                        if company.get('industry') in ['mining', 'logging', 'oil']:
                            risk_factors.append("High-Risk Industry")
                            
                        st.write(f"Risk Factors: {', '.join(risk_factors) if risk_factors else 'None'}")
            
            # OSM Businesses section
            st.subheader("📍 Local Business Mapping")
            if data['osm_businesses']:
                osm_df = pd.DataFrame([
                    {
                        'Name': biz.get('tags', {}).get('name', 'Unknown'),
                        'Type': biz.get('tags', {}).get('shop', biz.get('tags', {}).get('office', 'Unknown')),
                        'Lat': biz.get('lat'),
                        'Lon': biz.get('lon')
                    }
                    for biz in data['osm_businesses']
                    if biz.get('lat') and biz.get('lon')
                ])
                st.dataframe(osm_df, use_container_width=True)
            else:
                st.info("No local business data from OSM")
        except Exception as e:
            st.error(f"Error rendering companies tab: {str(e)}")
            self.logger.error(f"Companies tab error: {str(e)}")

    def render_social_tab(self, data):
        """Render the social intelligence tab"""
        try:
            st.subheader("📈 Social Media Intelligence")
            
            if not data['reddit_posts']:
                st.info("No Reddit data available")
                return
                
            # Create posts dataframe
            posts_df = pd.DataFrame(data['reddit_posts'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Timeline chart
                timeline_fig = create_reddit_timeline(posts_df)
                st.plotly_chart(timeline_fig, use_container_width=True)
                
            with col2:
                # Sentiment chart
                sentiment_fig = create_sentiment_chart(posts_df)
                st.plotly_chart(sentiment_fig, use_container_width=True)
                
            # Top posts
            st.subheader("🔥 Top Social Media Posts")
            posts_df_sorted = posts_df.sort_values('score', ascending=False)
            
            for idx, post in posts_df_sorted.head(5).iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{post.get('title', 'No Title')}**")
                        st.write(post.get('selftext', '')[:200] + "...")
                    with col2:
                        st.write(f"Score: {post.get('score', 0)}")
                        st.write(f"Comments: {post.get('num_comments', 0)}")
                        sentiment = post.get('sentiment', 0)
                        sentiment_color = "red" if sentiment < -0.1 else "green" if sentiment > 0.1 else "gray"
                        st.write(f"Sentiment: :{sentiment_color}[{sentiment:.2f}]")
                    st.divider()
        except Exception as e:
            st.error(f"Error rendering social tab: {str(e)}")
            self.logger.error(f"Social tab error: {str(e)}")

    def render_network_tab(self, data):
        """Render the entity network tab"""
        try:
            st.subheader("🔗 Corporate Entity Network")
            
            if not data['companies']:
                st.info("No company data available for network analysis")
                return
                
            # Create network graph
            network_fig = create_entity_graph(data['companies'])
            st.plotly_chart(network_fig, use_container_width=True)
            
            # Network statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_companies = len(data['companies'])
                st.metric("Total Entities", total_companies)
                
            with col2:
                parent_companies = len([c for c in data['companies'] if c.get('parent')])
                st.metric("Parent Companies", parent_companies)
                
            with col3:
                subsidiaries = len([c for c in data['companies'] if c.get('subsidiaries')])
                st.metric("Subsidiaries", subsidiaries)
        except Exception as e:
            st.error(f"Error rendering network tab: {str(e)}")
            self.logger.error(f"Network tab error: {str(e)}")

    def render_report_tab(self, data):
        """Render the intelligence report tab"""
        try:
            st.subheader("📄 Environmental Crime Intelligence Report")
            
            # Report summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Alerts", 
                         len(data['glad_alerts']) if not data['glad_alerts'].empty else 0)
            with col2:
                st.metric("High-Risk Companies", 
                         len([c for c in data['companies'] if c.get('sanctioned') or c.get('shell_company')]))
            with col3:
                st.metric("Social Volume", 
                         len(data['reddit_posts']))
            
            # Generate report sections
            st.subheader("Executive Summary")
            self.generate_executive_summary(data)
            
            st.subheader("Key Findings")
            self.generate_key_findings(data)
            
            st.subheader("Recommendations")
            self.generate_recommendations(data)
            
            # PDF export button
            if st.button("📥 Generate PDF Report"):
                self.generate_pdf_report(data)
        except Exception as e:
            st.error(f"Error rendering report tab: {str(e)}")
            self.logger.error(f"Report tab error: {str(e)}")

    def generate_executive_summary(self, data):
        """Generate executive summary section"""
        risk_score = self.calculate_risk_score(data)
        
        if risk_score > 70:
            risk_level = "🚨 CRITICAL"
            color = "red"
        elif risk_score > 40:
            risk_level = "⚠️ HIGH"
            color = "orange"
        elif risk_score > 20:
            risk_level = "🔶 MEDIUM"
            color = "yellow"
        else:
            risk_level = "✅ LOW"
            color = "green"
            
        st.write(f"""
        **Risk Level**: :{color}[**{risk_level}**] ({risk_score:.1f}/100)
        
        This region shows **{len(data['glad_alerts']) if not data['glad_alerts'].empty else 0}** forest loss alerts 
        with **{len(data['companies'])}** corporate entities identified. 
        Social media analysis reveals **{len(data['reddit_posts'])}** relevant discussions.
        """)

    def generate_key_findings(self, data):
        """Generate key findings section"""
        
        # GLAD findings
        if not data['glad_alerts'].empty:
            recent_alerts = data['glad_alerts'][data['glad_alerts']['date'] > 
                                              (datetime.now() - timedelta(days=30))]
            st.write("**🌳 Forest Monitoring**")
            st.write(f"- {len(recent_alerts)} new alerts in past 30 days")
            st.write(f"- Total alert area: {data['glad_alerts']['area'].sum() if 'area' in data['glad_alerts'].columns else 'N/A'} hectares")
        
        # Company findings
        if data['companies']:
            sanctioned = [c for c in data['companies'] if c.get('sanctioned')]
            shells = [c for c in data['companies'] if c.get('shell_company')]
            
            st.write("**🏢 Corporate Risk**")
            st.write(f"- {len(sanctioned)} sanctioned entities identified")
            st.write(f"- {len(shells)} potential shell companies")
            
        # Social findings
        if data['reddit_posts']:
            negative_posts = [p for p in data['reddit_posts'] if p.get('sentiment', 0) < -0.1]
            st.write("**📱 Social Intelligence**")
            st.write(f"- {len(negative_posts)} posts with negative sentiment")
            st.write(f"- Peak discussion volume: {max([p.get('score', 0) for p in data['reddit_posts']])} upvotes")

    def generate_recommendations(self, data):
        """Generate recommendations section"""
        risk_score = self.calculate_risk_score(data)
        
        if risk_score > 70:
            st.write("""
            **🚨 IMMEDIATE ACTION REQUIRED**
            - Launch formal investigation into identified entities
            - Coordinate with local environmental agencies
            - Deploy satellite monitoring for real-time alerts
            - Engage with social media platforms for content monitoring
            """)
        elif risk_score > 40:
            st.write("""
            **⚠️ ENHANCED MONITORING RECOMMENDED**
            - Increase satellite monitoring frequency
            - Conduct deeper corporate due diligence
            - Monitor social channels for escalation
            - Prepare contingency investigation plans
            """)
        else:
            st.write("""
            **✅ STANDARD MONITORING SUFFICIENT**
            - Maintain regular satellite monitoring
            - Periodic corporate registry checks
            - Continue social media listening
            - Document baseline for future comparison
            """)

    def generate_pdf_report(self, data):
        """Generate PDF report using the PDF generator module"""
        try:
            report_path = generate_pdf_report(data, self.current_region)
            st.success(f"📄 Report generated: {report_path}")
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")

def main():
    """Main dashboard application"""
    try:
        dashboard = EcoProfilerDashboard()
        
        # Render header
        dashboard.render_header()
        
        # Initial data load
        initial_data = {
            'glad_alerts': pd.DataFrame(),
            'companies': [],
            'osm_businesses': [],
            'reddit_posts': [],
            'satellite_images': []
        }
        
        # Render sidebar and get updated data
        data = dashboard.render_sidebar(initial_data)
        
        # Render main dashboard
        dashboard.render_main_dashboard(data)
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.write("**EcoProfiler v1.0**")
        st.sidebar.write("Global Environmental Crime Intelligence")
        st.sidebar.write("🌍 Using Open Data Only")
        
    except Exception as e:
        st.error(f"Fatal error in dashboard: {str(e)}")
        logging.error(f"Dashboard fatal error: {str(e)}")

if __name__ == "__main__":
    main()