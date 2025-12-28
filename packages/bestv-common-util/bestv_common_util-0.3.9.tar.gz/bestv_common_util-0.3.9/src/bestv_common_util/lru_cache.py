import time
from datetime import datetime


class LRUCache:
    def __init__(self, capacity: int, cache_ttl_ms=-1, cache_empty=False):
        self.capacity = capacity
        self.cache = {}
        self.lru = []
        self.init_ms = LRUCache.current_ms()
        self.cache_ttl_ms = cache_ttl_ms
        self.cache_empty = cache_empty

    @staticmethod
    def current_ms():
        return round(time.time() * 1000)

    def has(self, key):
        return key in self.cache

    def get(self, key):
        if key not in self.cache:
            return
        value = self.cache[key]
        if self.cache_ttl_ms < 0:
            self.lru.remove(key)
            self.lru.append(key)
            return value
        elif value and isinstance(value, list):
            if LRUCache.current_ms() - self.init_ms - int(value[1]) > self.cache_ttl_ms:
                del self.cache[key]
                self.lru.remove(key)
            else:
                self.lru.remove(key)
                self.lru.append(key)
                return value[0]

    def put(self, key, value) -> None:
        if self.cache_empty or value is not None:
            if key in self.cache:
                self.lru.remove(key)
            if len(self.cache) >= self.capacity:
                del self.cache[self.lru[0]]
                self.lru.pop(0)
            # If the ttl less than 0, store the value directly
            # Else store the value and different time from init
            self.cache[key] = value if self.cache_ttl_ms < 0 else [value, LRUCache.current_ms() - self.init_ms]
            self.lru.append(key)
