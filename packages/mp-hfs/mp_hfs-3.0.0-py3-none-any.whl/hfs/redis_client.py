"""Redis 客户端封装"""
import redis
from urllib.parse import urlparse


class RedisClient:
    def __init__(self, url: str):
        p = urlparse(url)
        self._client = redis.Redis(
            host=p.hostname,
            port=p.port or 6379,
            password=p.password,
            decode_responses=True
        )

    def get(self, key):
        return self._client.get(key)

    def set(self, key, value, ex=None):
        return self._client.set(key, value, ex=ex)

    def delete(self, key):
        return self._client.delete(key)

    def keys(self, pattern):
        return self._client.keys(pattern)

    def setnx(self, key, value):
        return self._client.setnx(key, value)

    def expire(self, key, seconds):
        return self._client.expire(key, seconds)

    @property
    def client(self):
        return self._client
