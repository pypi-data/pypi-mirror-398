from typing import Any, Optional, Type
from sqlalchemy.types import TypeDecorator, String
from .helpers import sso_cache
from .authenticate import CustomUser
from fastapi_keycloak_sso.sso.sso import SSOClass



class CustomSSORelatedField:
    """
    Get field information from cache and if not, get it from keycloak and store it in cache
    """
    def __init__(self, max_length: int = 36):
        self.max_length = max_length

    def _get_sso_field_value(
        self,
        value: str | int,
        sso_method: str,
        cache_key: Optional[str] = None,
        getter_klass: Optional[Type] = None
    ) -> Any:

        key = f"{cache_key}_{value}" if cache_key else f"{str(self.__class__.__name__).lower()}_{value}"
        data = sso_cache.get_custom_class_cached_value(key)
        if not data:
            sso_client = SSOClass()
            if not hasattr(sso_client, sso_method):
                raise Exception("SSO Class hasn't specified method")
            try:
                data = getattr(sso_client, sso_method)(pk=value)
                sso_cache.set_custom_class_cache_value(key, data, timeout=3600)
            except Exception:
                data = None

        getter_klass = getter_klass or CustomUser
        return getter_klass(payload=data)


class SSOUserField(TypeDecorator, CustomSSORelatedField):
    """
    Type the field for the desired id value in the database, preferably sqlalchemy
    """
    impl = String
    cache_base_key = "sso_user"
    cache_ok = True

    def __init__(self, *args, **kwargs):
        TypeDecorator.__init__(self, *args, **kwargs)
        CustomSSORelatedField.__init__(self)

    def process_result_value(self, value: Any, dialect) -> Optional[CustomUser]:
        if value is None:
            return None
        return CustomUser(False, {"id": value})

    def process_bind_param(self, value: Any, dialect) -> Optional[str]:
        from .schemas import LazySSOUser

        if value is None:
            return None

        if isinstance(value, CustomUser):
            return value.pk

        if isinstance(value, str):
            return value

        if isinstance(value, LazySSOUser):
            return str(value)

        raise ValueError("SSOUserField only accepts CustomUser, LazySSOUser, or string user_id.")

    def get_full_data(self, value: str | int) -> Any:

        key = f"{self.cache_base_key}_{value}"
        return self._get_sso_field_value(
            value=value,
            sso_method="get_user_detail_data",
            cache_key=key,
            getter_klass=CustomUser
        )
