import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# API Keys
USE_SEMANTIC_SCHOLAR_API_KEYS = False
SEMANTIC_SCHOLAR_API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY', None)

# API Endpoints
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper"
OPENALEX_API_URL = "https://api.openalex.org/works"

# Threading and Retry Configuration
REQUEST_TIMEOUT = 10  # API request timeout in seconds
MAX_RETRIES = 3  # Maximum retries on failed API requests
RETRY_BACKOFF_FACTOR = 2  # Backoff factor for retries 

# Rate limiting to avoid API throttling
SEMANTIC_SCHOLAR_RATE_LIMIT = 2  # Delay between requests in seconds
OPENALEX_RATE_LIMIT = 0.5  # Delay between requests in seconds

# Default Directories
DEFAULT_OUTPUT_DIR = './data'
BASE_CRAWLER_OUTPUT_DIR = f'{DEFAULT_OUTPUT_DIR}/base_crawler_data'
EXTENDED_CRAWLER_OUTPUT_DIR = f'{DEFAULT_OUTPUT_DIR}/extended_crawler_data'
CITATIONS_CRAWLER_OUTPUT_DIR = f'{DEFAULT_OUTPUT_DIR}/citations_crawler_data'

# Logging Configuration
LOG_FILE = './logs/crawler.log'
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Crawler Configuration
SKIP_SECTIONS = ["workshop", "tutorial", "keynote", "panel", "poster",
                "demo", "doctoral", "posters", "short papers", "demos", "short paper", "tutorials", 
                "demonstration", "PhD Symposium", "short research"]