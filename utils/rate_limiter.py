import time
import threading
from collections import defaultdict


class RateLimiter:
    
    def __init__(self):
        self._locks = defaultdict(threading.Lock)
        self._last_call = defaultdict(float)
    
    def wait_if_needed(self, api_name, delay):
        with self._locks[api_name]:
            elapsed = time.time() - self._last_call[api_name]
            if elapsed < delay:
                time.sleep(delay - elapsed)
            self._last_call[api_name] = time.time()


_rate_limiter = RateLimiter()


def get_rate_limiter():
    return _rate_limiter


