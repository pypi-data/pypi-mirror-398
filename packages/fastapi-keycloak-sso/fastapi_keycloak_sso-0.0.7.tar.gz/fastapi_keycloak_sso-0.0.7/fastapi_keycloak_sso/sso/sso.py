import os
from enum import Enum
from typing import Type
from urllib.parse import urlencode
import logging
from .caching import RedisSSOCache
from fastapi_keycloak_sso.keycloak import KeyCloakConfidentialClient
from fastapi_keycloak_sso.keycloak import KeyCloakInitializer

logger = logging.getLogger(__name__)

redis_host = KeyCloakInitializer.redis_host

sso_cache = RedisSSOCache(host=redis_host, port=6379, db=0)


class SSOClass:
    class SSOClassException(Exception):
        pass

    class SSOClassNotFoundException(Exception):
        pass

    class CompanyGroupRoleChoices(Enum):
        MANAGER = "MANAGER"
        ASSISTANT = "ASSISTANT"
        EMPLOYEE = "EMPLOYEE"

    class SSODataTypeChoices(Enum):
        USER = "USER"
        USER_ROLE = "USER_ROLE"
        COMPANY_GROUP = "COMPANY_GROUP"

    class SSODataFormChoices(Enum):
        DETAIL = "DETAIL"
        LIST = "LIST"
        CUSTOM = "CUSTOM"

    class SSOFieldTypeChoices(Enum):
        GROUP = "GROUP"
        USER = "USER"
        ROLE = "ROLE"

    sso_request_exceptions = (
        SSOClassException,
        SSOClassNotFoundException,
        KeyCloakConfidentialClient.KeyCloakException,
        KeyCloakConfidentialClient.KeyCloakNotFoundException,
    )

    def __init__(self):
        self.keycloak = KeyCloakConfidentialClient()

    @classmethod
    def validate_enums_value(cls, value: str, enums_class: Type[Enum]):
        if value not in [e.value for e in enums_class]:
            raise cls.SSOClassException("Value is not exists in that enums")

    @staticmethod
    def _build_filter_url(*, base_url: str, ids_filtering_list: list = None, id_range_filtering_list: list = None):
        query_params = {}
        return f"{base_url}?{urlencode(query_params)}" if query_params else base_url

    def get_sso_data(self, data_type: Enum, data_form: Enum, *args, **kwargs):
        self.validate_enums_value(data_type.value, data_type.__class__)
        self.validate_enums_value(data_form.value, data_form.__class__)
        if data_form == self.SSODataFormChoices.DETAIL and 'pk' not in kwargs:
            raise self.SSOClassException("Get detail of a object need object pk")
        get_data_method = getattr(self, f'get_{data_type.value.lower()}_{data_form.value.lower()}_data', None)
        if not get_data_method:
            raise self.SSOClassException("Data get method for sso data is not valid")
        return get_data_method(*args, **kwargs)

    def get_user_detail_data(self, pk, *args, **kwargs):
        cache_key = f"user_detail_{pk}"
        data = sso_cache.get_custom_class_cached_value(cache_key)
        if data:
            logger.info(f"Cache HIT for user {pk}")
            return data

        logger.info(f"Cache MISS for user {pk}")
        user_data = self.keycloak.send_request(
            self.keycloak.KeyCloakRequestTypeChoices.USERS,
            self.keycloak.KeyCloakRequestTypeChoices,
            self.keycloak.KeyCloakRequestMethodChoices.GET,
            self.keycloak.KeyCloakPanelTypeChoices.ADMIN,
            detail_pk=pk,
        )
        if user_data:
            sso_cache.set_custom_class_cache_value(cache_key, user_data, timeout=3600)
            return user_data
        raise self.SSOClassException("Failed to retrieve data with user ID")

    def get_user_list_data(self, *args, **kwargs):
        cache_key = "user_list"
        data = sso_cache.get_custom_class_cached_value(cache_key)
        if data:
            logger.info("Cache HIT for user list")
            return data

        logger.info("Cache MISS for user list")
        users_data = self.keycloak.send_request(
            self.keycloak.KeyCloakRequestTypeChoices.USERS,
            self.keycloak.KeyCloakRequestTypeChoices,
            self.keycloak.KeyCloakRequestMethodChoices.GET,
            self.keycloak.KeyCloakPanelTypeChoices.ADMIN,
        )
        if users_data:
            sso_cache.set_custom_class_cache_value(cache_key, users_data, timeout=3600)
            return users_data
        raise self.SSOClassException("Failed to retrieve user list data")

    def get_company_group_detail_data(self, pk, *args, **kwargs):
        cache_key = f"company_group_detail_{pk}"
        data = sso_cache.get_custom_class_cached_value(cache_key)
        if data:
            logger.info(f"Cache HIT for company group {pk}")
            return data

        logger.info(f"Cache MISS for company group {pk}")
        group_data = self.keycloak.send_request(
            self.keycloak.KeyCloakRequestTypeChoices.GROUPS,
            self.keycloak.KeyCloakRequestTypeChoices,
            self.keycloak.KeyCloakRequestMethodChoices.GET,
            self.keycloak.KeyCloakPanelTypeChoices.ADMIN,
            detail_pk=pk
        )
        if group_data:
            sso_cache.set_custom_class_cache_value(cache_key, group_data, timeout=3600)
            return group_data
        raise self.SSOClassException("Failed to retrieve company groups detail data")
