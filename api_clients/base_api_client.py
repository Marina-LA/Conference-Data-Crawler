import requests
import logging
import time
from config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF_FACTOR

class BaseApiClient:
    def __init__(self):
        pass

    def make_request(self, url, params=None, headers=None, method='GET', citations=None):
        """Make an HTTP request with retries and backoff."""
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                if method == "GET":
                    response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
                elif method == "POST":
                    response = requests.post(url, params=params, json={"ids":citations}, headers=headers, timeout=REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logging.error(f"Error {response.status_code}: {response.text}")
                    return None
                else:
                    logging.error(f"Error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error: {e}. Retrying...")
            
            retries += 1
            time.sleep(RETRY_BACKOFF_FACTOR * retries)
        
        logging.error(f"Failed to retrieve data after {MAX_RETRIES} retries.")
        return None