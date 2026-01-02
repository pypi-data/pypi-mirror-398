import os
from typing import Any
from .caching import RedisSSOCache
from fastapi_keycloak_sso.keycloak import KeyCloakConfidentialClient
from fastapi_keycloak_sso.initializer import KeyCloakInitializer

redis_host = KeyCloakInitializer.redis_host

sso_cache = RedisSSOCache(host=redis_host, port=6379, db=0)

class CustomGetterObjectClass:
    def __init__(self, payload: dict):
        self.is_exists = bool(payload)
        self._payload = payload
        self.keycloak_klass = KeyCloakConfidentialClient()

    def __getattr__(self, name):
        if not self.is_exists:
            return None
        if name in self._payload:
            return self._payload[name]
        return super().__getattribute__(name)

    def __bool__(self):
        return self.is_exists

    def __repr__(self):
        return f"<CustomGetterObjectClass()>"

    @property
    def pk(self):
        if 'id' in self._payload:
            return str(self._payload['id'])
        elif 'sub' in self._payload:
            return str(self._payload['sub'])
        return None

    def _get_cache_key(self, cache_base_key: str):
        return f"{cache_base_key}_{self.pk}"

    def _get_cached_value(self, cache_base_key: str) -> Any:
        cache_key = self._get_cache_key(cache_base_key)
        return sso_cache.get_custom_class_cached_value(cache_key)

    def _set_cache_value(self, cache_base_key: str, value: Any, timeout: int = 3600) -> None:
        cache_key = self._get_cache_key(cache_base_key)
        sso_cache.set_custom_class_cache_value(cache_key, value, timeout)
