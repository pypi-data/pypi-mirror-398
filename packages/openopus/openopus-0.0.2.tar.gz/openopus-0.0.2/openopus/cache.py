import time


class TTLCache:
    def __init__(self, ttl_seconds):
        self.ttl = ttl_seconds
        self.store = {}

    def get(self, key):
        item = self.store.get(key)
        if not item: return None

        value, expires = item
        if time.time() > expires:
            del self.store[key]
            return None
        return value

    def set(self, key, value):
        self.store[key] = (value, time.time() + self.ttl)
