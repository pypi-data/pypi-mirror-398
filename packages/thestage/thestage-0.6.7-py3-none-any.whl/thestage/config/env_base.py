import os

THESTAGE_CONFIG_DIR = os.getenv('THESTAGE_CONFIG_DIR', '.thestage')
THESTAGE_CONFIG_FILE = os.getenv('THESTAGE_CONFIG_FILE', 'config.json')
THESTAGE_AUTH_TOKEN = os.getenv('THESTAGE_AUTH_TOKEN', None)
THESTAGE_LOGGING_FILE = os.getenv('THESTAGE_LOGGING_FILE', 'thestage.log')
THESTAGE_API_URL = os.getenv('THESTAGE_API_URL', 'https://backend.thestage.ai')
