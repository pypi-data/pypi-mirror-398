import time
from openopus.cache import TTLCache


def test_cache_set_get():
    cache = TTLCache(ttl_seconds=1)
    cache.set("key", "67")
    assert cache.get("key") == "67"


def test_cache_expiry():
    cache = TTLCache(ttl_seconds=0.1)
    cache.set("key", "67")
    time.sleep(0.2)
    assert cache.get("key") is None
