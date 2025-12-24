import redis

from nlbone.config.settings import get_settings


class RedisClient:
    _client: redis.Redis | None = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
        return cls._client

    @classmethod
    def close(cls):
        if cls._client is not None:
            cls._client.close()
            cls._client = None
