import json
import hashlib
import os
from threading import Lock


class RequestCache:
    
    def __init__(self, cache_dir='./cache'):
        self.cache_dir = cache_dir
        self.memory_cache = {}
        self.lock = Lock()
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, url, params=None):
        key_data = f"{url}:{json.dumps(params, sort_keys=True) if params else ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key):
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, url, params=None):
        cache_key = self._get_cache_key(url, params)
        
        with self.lock:
            if cache_key in self.memory_cache:
                return self.memory_cache[cache_key]
        
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    with self.lock:
                        self.memory_cache[cache_key] = data
                    return data
            except:
                pass
        
        return None
    
    def set(self, url, params, response_data):
        if response_data is None:
            return
        
        cache_key = self._get_cache_key(url, params)
        
        with self.lock:
            self.memory_cache[cache_key] = response_data
        
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f)
        except:
            pass


_request_cache = RequestCache()


def get_request_cache():
    return _request_cache






