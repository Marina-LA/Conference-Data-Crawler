import requests
import logging
import time
from config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF_FACTOR, USE_CACHING
from utils.rate_limiter import get_rate_limiter
from utils.request_cache import get_request_cache


class BaseApiClient:
    def __init__(self):
        self.rate_limiter = get_rate_limiter()
        self.cache = get_request_cache() if USE_CACHING else None

    def make_request(self, url, params=None, headers=None, method='GET', citations=None, 
                     api_name=None, rate_limit=0):
        """Make an HTTP request with retries, backoff, rate limiting, and caching.
        
        Args:
            url: The URL to request
            params: Query parameters
            headers: Request headers
            method: HTTP method ('GET' or 'POST')
            citations: Citations data for batch POST requests
            api_name: Name of the API for rate limiting
            rate_limit: Delay between requests in seconds
        """
        # Check cache first (only for GET requests)
        if method == 'GET' and self.cache:
            cached_response = self.cache.get(url, params)
            if cached_response is not None:
                return cached_response
        
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                # Apply rate limiting if specified
                if api_name and rate_limit > 0:
                    self.rate_limiter.wait_if_needed(api_name, rate_limit)
                
                if method == "GET":
                    response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
                elif method == "POST":
                    response = requests.post(url, params=params, json={"ids": citations}, 
                                           headers=headers, timeout=REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    # Cache successful GET requests
                    if method == 'GET' and self.cache:
                        self.cache.set(url, params, data)
                    return data
                elif response.status_code == 404:
                    logging.warning(f"Resource not found (404): {url}")
                    return None
                elif response.status_code == 429:
                    # Rate limit exceeded, wait longer
                    wait_time = RETRY_BACKOFF_FACTOR * (retries + 2) * 2
                    logging.warning(f"Rate limit exceeded (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Error {response.status_code}: {response.text}")
            except requests.exceptions.Timeout:
                logging.warning(f"Request timeout for {url}. Retrying...")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error: {e}. Retrying...")
            
            retries += 1
            if retries <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_FACTOR * retries)
        
        logging.error(f"Failed to retrieve data from {url} after {MAX_RETRIES} retries.")
        return None