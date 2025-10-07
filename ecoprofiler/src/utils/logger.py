import logging
import logging.config
import yaml
from pathlib import Path
import sys
from datetime import datetime

def setup_logger(name=None, region="global"):
    """Setup centralized logging configuration"""
    
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': f'data/logs/{region}_{datetime.now().strftime("%Y%m%d")}.log',
                'mode': 'a',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'stream': sys.stdout
            }
        },
        'loggers': {
            '': {
                'handlers': ['file', 'console'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }
    
    # Create logs directory
    Path('data/logs').mkdir(parents=True, exist_ok=True)
    
    logging.config.dictConfig(log_config)
    logger = logging.getLogger(name)
    return logger