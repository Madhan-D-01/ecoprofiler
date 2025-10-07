import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"

# API Configuration
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
    'user_agent': os.getenv('REDDIT_USER_AGENT', 'EcoProfilerOSINT/1.0')
}

SENTINELHUB_CONFIG = {
    'client_id': os.getenv('SENTINELHUB_CLIENT_ID'),
    'client_secret': os.getenv('SENTINELHUB_CLIENT_SECRET')
}

# Analysis Settings
DEFAULT_RADIUS_KM = 20
DEFAULT_DAYS_BACK = 30
MAX_RADIUS_KM = 100

# Data Collection Settings
GLAD_SETTINGS = {
    'max_alerts': 1000,
    'min_confidence': 0.5
}

REDDIT_SETTINGS = {
    'max_posts_per_query': 100,
    'max_comments_per_post': 10,
    'search_terms': [
        'illegal logging',
        'deforestation', 
        'mining',
        'environmental crime',
        'pollution',
        'wildlife trafficking',
        'forest fire'
    ]
}

# Risk Assessment Weights
RISK_WEIGHTS = {
    'forest_alerts': 0.4,
    'sanctioned_companies': 0.3,
    'negative_sentiment': 0.2,
    'industrial_sites': 0.1
}

# Visualization Settings
MAP_SETTINGS = {
    'default_zoom': 10,
    'alert_color': 'red',
    'business_color': 'blue',
    'high_risk_color': 'darkred'
}

# PDF Report Settings
REPORT_SETTINGS = {
    'company_display_limit': 10,
    'post_display_limit': 5,
    'include_satellite_previews': True
}

def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not REDDIT_CONFIG['client_id'] or not REDDIT_CONFIG['client_secret']:
        errors.append("Reddit API credentials not configured")
    
    # Create required directories
    required_dirs = [DATA_DIR, LOGS_DIR, DATA_DIR / 'alerts', DATA_DIR / 'companies', 
                    DATA_DIR / 'satellite', DATA_DIR / 'reddit', DATA_DIR / 'reports']
    
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)
    
    return errors