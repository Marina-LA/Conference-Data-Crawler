import os
from typing import List, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class APIConfig:
    """API configuration."""
    semantic_scholar_url: str = "https://api.semanticscholar.org/graph/v1/paper"
    openalex_url: str = "https://api.openalex.org/works"
    use_semantic_scholar_api_keys: bool = False
    semantic_scholar_api_key: str = os.getenv('SEMANTIC_SCHOLAR_API_KEY', None)


@dataclass
class RequestConfig:
    """HTTP and retry settings."""
    timeout: int = 10
    max_retries: int = 3
    retry_backoff_factor: int = 2
    semantic_scholar_rate_limit: float = 1.0
    openalex_rate_limit: float = 0.3


@dataclass
class CrawlerConfig:
    """Crawler settings."""
    max_workers: int = 5
    use_caching: bool = True
    enable_progress_bar: bool = True
    skip_sections: List[str] = None
    
    def __post_init__(self):
        if self.skip_sections is None:
            self.skip_sections = [
                "workshop", "tutorial", "keynote", "panel", "poster",
                "demo", "doctoral", "posters", "short papers", "demos", 
                "short paper", "tutorials", "demonstration", "PhD Symposium", 
                "short research"
            ]


@dataclass
class PathConfig:
    """Filesystem paths."""
    default_output_dir: str = './data'
    base_crawler_output_dir: str = './data/base_crawler_data'
    extended_crawler_output_dir: str = './data/extended_crawler_data'
    citations_crawler_output_dir: str = './data/citations_crawler_data'
    cache_dir: str = './cache'
    logs_dir: str = './logs'


@dataclass
class LoggingConfig:
    """Logging settings."""
    log_file: str = './logs/crawler.log'
    log_level: str = 'INFO'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


api_config = APIConfig()
request_config = RequestConfig()
crawler_config = CrawlerConfig()
path_config = PathConfig()
logging_config = LoggingConfig()

USE_SEMANTIC_SCHOLAR_API_KEYS = api_config.use_semantic_scholar_api_keys
SEMANTIC_SCHOLAR_API_KEY = api_config.semantic_scholar_api_key
SEMANTIC_SCHOLAR_API_URL = api_config.semantic_scholar_url
OPENALEX_API_URL = api_config.openalex_url

REQUEST_TIMEOUT = request_config.timeout
MAX_RETRIES = request_config.max_retries
RETRY_BACKOFF_FACTOR = request_config.retry_backoff_factor
SEMANTIC_SCHOLAR_RATE_LIMIT = request_config.semantic_scholar_rate_limit
OPENALEX_RATE_LIMIT = request_config.openalex_rate_limit

MAX_WORKERS = crawler_config.max_workers
USE_CACHING = crawler_config.use_caching
ENABLE_PROGRESS_BAR = crawler_config.enable_progress_bar
SKIP_SECTIONS = crawler_config.skip_sections

DEFAULT_OUTPUT_DIR = path_config.default_output_dir
BASE_CRAWLER_OUTPUT_DIR = path_config.base_crawler_output_dir
EXTENDED_CRAWLER_OUTPUT_DIR = path_config.extended_crawler_output_dir
CITATIONS_CRAWLER_OUTPUT_DIR = path_config.citations_crawler_output_dir

LOG_FILE = logging_config.log_file
LOG_LEVEL = logging_config.log_level
LOG_FORMAT = logging_config.log_format
