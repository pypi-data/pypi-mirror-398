import redis
import json
from typing import Any, Optional
from fastapi_keycloak_sso.initializer import KeyCloakInitializer

redis_host = KeyCloakInitializer.redis_host


class RedisSSOCache:
    def __init__(self, host=redis_host, port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def get_custom_class_cached_value(self, cache_key: str) -> Optional[Any]:
        data = self.client.get(cache_key)
        if data:
            return json.loads(data)
        return None

    def set_custom_class_cache_value(self, cache_key: str, value: Any, timeout: int = 3600) -> None:
        self.client.set(cache_key, json.dumps(value), ex=timeout)
