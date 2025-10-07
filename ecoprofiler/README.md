README.md

Markdown

# 🌍 EcoProfiler - Global Environmental Crime OSINT Platform

> **Fully Modular OSINT Tool for Environmental Crime Profiling Using Open Data Only**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎯 Overview

EcoProfiler is a comprehensive open-source intelligence platform designed to detect and analyze environmental crimes using exclusively open data sources. The system integrates satellite imagery, corporate registries, social media analysis, and environmental alerts to provide actionable intelligence.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Reddit Developer Account (for social media analysis)
- Sentinel Hub Account (optional, for satellite imagery)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ecoprofiler.git
   cd ecoprofiler
Install dependencies

Bash

pip install -r requirements.txt
Configure API credentials

Bash

cp .env.example .env
# Edit .env with your API credentials
Run your first analysis

Bash

python cli_runner.py --place "Sumatra" --radius 20 --include-osm --report
Launch the dashboard

Bash

streamlit run dashboard/app.py
🔧 Core Features
🌳 Forest Loss Monitoring
GLAD Alerts: Real-time deforestation alerts from Global Forest Watch
Satellite Imagery: High-resolution Sentinel-2 imagery via Sentinel Hub
Change Detection: NDVI analysis for vegetation health monitoring
🏢 Corporate Intelligence
Wikidata Integration: Company registries and corporate hierarchies
GLEIF Lookup: Legal Entity Identifier resolution
OpenSanctions Screening: Sanctions and PEP database checks
OSM Business Mapping: Local facility and business discovery
📱 Social Media Analysis
Reddit Scraping: PMAW for historical data + PRAW for real-time enrichment
Sentiment Analysis: TextBlob-powered sentiment scoring
Topic Modeling: Environmental crime discussion detection
📊 Interactive Dashboard
Interactive Maps: Folium-based alert and business mapping
Network Graphs: Corporate entity relationship visualization
Timeline Analysis: Social media and alert trend tracking
Risk Scoring: Multi-factor environmental risk assessment
📄 Intelligence Reports
PDF Export: Professional intelligence reports
Executive Summaries: Risk-focused executive briefings
Actionable Recommendations: Tiered response strategies
🗂️ Project Structure
text

ecoprofiler/
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── scripts/
│   ├── fetch_glad_alerts.py   # GLAD alert fetcher
│   ├── satellite_fetch.py     # Satellite imagery
│   ├── registry_search.py     # Company registry search
│   ├── reddit_scraper.py      # Social media analysis
│   └── generate_pdf.py        # Report generation
├── src/
│   ├── utils/
│   │   └── logger.py          # Centralized logging
│   ├── data_pipeline/         # Data processing modules
│   └── visualizations/        # Plotting and mapping
├── config/
│   └── settings.py            # Configuration management
├── data/                      # Generated data (gitignored)
├── cli_runner.py              # Command-line interface
├── requirements.txt           # Python dependencies
└── README.md                  # This file
🔐 API Configuration
Reddit API Setup
Visit https://www.reddit.com/prefs/apps
Create a new "script" application
Note your client ID and secret
Add to .env:
text

REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=EcoProfilerOSINT/1.0
Sentinel Hub Setup (Optional)
Register at https://www.sentinel-hub.com/
Create OAuth client credentials
Add to .env:
text

SENTINELHUB_CLIENT_ID=your_sentinel_client_id
SENTINELHUB_CLIENT_SECRET=your_sentinel_client_secret
🖥️ Usage Examples
Command Line Interface
Bash

# Analyze by place name
python cli_runner.py --place "Amazon Basin" --radius 50 --include-osm --report

# Analyze by coordinates
python cli_runner.py --coords "-3.4653,-62.2159" --radius 30 --days 60

# Minimal analysis (GLAD alerts only)
python cli_runner.py --place "Borneo" --radius 20
Dashboard Interface
Bash

streamlit run dashboard/app.py
Then access http://localhost:8501 in your browser.

📈 Data Sources
Source	Type	Use Case	Rate Limits
Global Forest Watch	Environmental	Deforestation alerts	Varies
Sentinel Hub	Satellite	Imagery & NDVI	Free tier: 50k units/month
Wikidata	Corporate	Company registries	No strict limits
GLEIF API	Financial	LEI resolution	1000 req/hour
OpenSanctions	Compliance	Sanctions screening	1000 req/day
OpenStreetMap	Geographic	Business mapping	10k req/hour
Reddit API	Social Media	Public discussions	60 req/minute
🔍 Analysis Pipeline
Input Processing: Geocode location and define search area
Environmental Data: Fetch GLAD alerts and satellite imagery
Corporate Intelligence: Search company registries and sanctions
Social Analysis: Scrape and analyze Reddit discussions
Risk Assessment: Calculate multi-factor risk score
Visualization: Generate maps, graphs, and timelines
Reporting: Create comprehensive PDF intelligence reports
🛡️ Legal & Ethical Considerations
Open Data Only: Uses exclusively publicly available data sources
Rate Limiting: Respects all API rate limits and terms of service
Privacy Protection: Anonymizes personal data where possible
Legal Compliance: Designed for legitimate research and monitoring purposes
🤝 Contributing
We welcome contributions! Please see our Contributing Guidelines for details.

Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request
📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
Global Forest Watch for deforestation alert data
Sentinel Hub for satellite imagery access
Wikidata for open corporate data
Reddit for social media data access
All open data providers that make this project possible
🆘 Support
For support and questions:

📧 Email: support@ecoprofiler.org
💬 Discussions: GitHub Discussions
🐛 Issues: GitHub Issues
<div align="center">
Built with ❤️ for environmental protection

"The Earth is what we all have in common." - Wendell Berry

</div> ```
4. License File
LICENSE

text

MIT License

Copyright (c) 2024 EcoProfiler Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
5. Environment File Template
.env.example

Bash

# EcoProfiler Configuration
# Copy this file to .env and fill in your credentials

# Reddit API Configuration (Required for social media analysis)
# Get from: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=EcoProfilerOSINT/1.0

# Sentinel Hub Configuration (Optional - for satellite imagery)
# Get from: https://www.sentinel-hub.com/
SENTINELHUB_CLIENT_ID=your_sentinelhub_client_id
SENTINELHUB_CLIENT_SECRET=your_sentinelhub_client_secret

# Geocoding Service (Optional - for place name resolution)
# You can use OpenStreetMap Nominatim (free) or Google Geocoding API
GEOCODING_API_KEY=your_geocoding_api_key_optional

# Analysis Settings (Optional - override defaults)
DEFAULT_RADIUS_KM=20
DEFAULT_DAYS_BACK=30
MAX_RADIUS_KM=100

# Logging Level (Optional)
LOG_LEVEL=INFO

# Note: All other data sources (GFW, Wikidata, GLEIF, OpenSanctions, OSM)
# are publicly accessible and don't require API keys



data/
├── alerts/          # GLAD alert CSVs
├── companies/       # Company registry JSONs  
├── satellite/       # Satellite imagery
├── reddit/         # Social media data
├── reports/        # Generated PDF reports
└── logs/           # Application logs
This completes the EcoProfiler system! The platform now includes:

✅ Complete data pipeline (GLAD, satellite, companies, Reddit)
✅ Interactive dashboard with maps and visualizations
✅ Professional PDF reporting
✅ Comprehensive documentation
✅ Configuration management
✅ Error handling and logging

The system is ready for deployment and can analyze any location worldwide using only open data sources as required














[## Basic Command Structure:
```bash
python cli_runner.py --place "REGION_NAME" --radius 20 --include-osm --include-satellite --report
```

## Specific Region Commands:

```bash
# Sumatra (Indonesia)
python cli_runner.py --place "Sumatra" --radius 20 --include-osm --include-satellite --report

# Amazon (Brazil)
python cli_runner.py --place "Amazon" --radius 20 --include-osm --include-satellite --report

# Borneo (Malaysia/Indonesia)
python cli_runner.py --place "Borneo" --radius 20 --include-osm --include-satellite --report

# Congo (Central Africa)
python cli_runner.py --place "Congo" --radius 20 --include-osm --include-satellite --report
```

## Alternative: Using Coordinates:
```bash
# Custom coordinates (latitude, longitude)
python cli_runner.py --coords "1.23,-56.77" --radius 20 --include-osm --include-satellite --report
```

## Customized Parameters:
```bash
# Larger search radius (50km)
python cli_runner.py --place "Sumatra" --radius 50 --include-osm --include-satellite --report

# Longer time period (90 days)
python cli_runner.py --place "Sumatra" --radius 20 --days 90 --include-osm --include-satellite --report

# Without satellite imagery (faster)
python cli_runner.py --place "Sumatra" --radius 20 --include-osm --report

# Without OSM business data
python cli_runner.py --place "Sumatra" --radius 20 --include-satellite --report

# Minimal data collection (no OSM, no satellite)
python cli_runner.py --place "Sumatra" --radius 20 --report
```

## Complete Example with All Options:
```bash
# Comprehensive data collection for Sumatra
python cli_runner.py --place "Sumatra" --radius 30 --days 60 --include-osm --include-satellite --report
```

## What Each Flag Does:
- `--place "Region"` - Specifies the geographic region
- `--radius 20` - Search radius in kilometers (default: 20)
- `--days 30` - Days to look back for data (default: 30)
- `--include-osm` - Include OpenStreetMap business data
- `--include-satellite` - Include satellite imagery download
- `--report` - Generate PDF report after data collection

## Available Regions in Your Code:
Your code currently supports these predefined regions:
- **Sumatra** → Coordinates: (0.7893, 101.3431)
- **Amazon** → Coordinates: (-3.4653, -62.2159)  
- **Borneo** → Coordinates: (0.9619, 114.5548)
- **Congo** → Coordinates: (-4.0383, 21.7587)

## Quick Start:
```bash
# Run for Sumatra with all data sources
python cli_runner.py --place "Sumatra" --radius 20 --include-osm --include-satellite --report

# After data collection, start the dashboard
streamlit run dashboard/app.py
```

The CLI will collect GLAD alerts, company data, Reddit posts, satellite imagery, and generate a PDF report for the specified region.]