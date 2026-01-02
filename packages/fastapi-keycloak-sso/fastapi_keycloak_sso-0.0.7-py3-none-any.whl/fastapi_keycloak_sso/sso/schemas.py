from typing import Any, get_origin, get_args, Optional, Union
from pydantic_core import core_schema
from fastapi_keycloak_sso.sso.authenticate import CustomUser
from fastapi_keycloak_sso.sso.fields import SSOUserField
from .exceptions import SSOUserNotFound



class LazySSOUser:
    def __init__(self, pk: str, sso_field: SSOUserField):
        self.pk = pk
        self._sso_field = sso_field

    def get_full_data(self):
        data: CustomUser = self._sso_field.get_full_data(self.pk)
        if hasattr(data, "to_dict"):
            return data.to_dict()
        return dict(data)

    def __str__(self):
        return self.pk


class SSOUserPydanticField:
    """
    Serializer of user ID field in pydantic
    """

    sso_field: SSOUserField = SSOUserField()

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):

        def _validate(v: Any, info: Any):

            is_optional = (
                get_origin(source_type) is Optional or
                (get_origin(source_type) is Union and type(None) in get_args(source_type))
            )

            if v is None:
                if is_optional:
                    return None
                raise TypeError("User ID cannot be None")

            if isinstance(v, LazySSOUser):
                user = v
            elif isinstance(v, CustomUser):
                user = LazySSOUser(v.pk, cls.sso_field)
            elif isinstance(v, str):
                user = LazySSOUser(v, cls.sso_field)
            elif hasattr(v, "id"):
                user = LazySSOUser(v.id, cls.sso_field)
            else:
                raise TypeError(f"Invalid user id: {v}")

            return user

        return core_schema.no_info_wrap_validator_function(
            _validate,
            core_schema.any_schema(),
            serialization=core_schema.to_string_ser_schema()
        )


class SSOUserPydanticWithValidation(SSOUserPydanticField):
    """
    Serializer of user ID field in pydantic by checking if the user exists in the system
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):

        def _validate(v: Any, info: Any):

            is_optional = (
                get_origin(source_type) is Optional or
                (get_origin(source_type) is Union and type(None) in get_args(source_type))
            )

            if v is None:
                if is_optional:
                    return None
                raise TypeError("User ID cannot be None")

            if isinstance(v, LazySSOUser):
                user = v
            elif isinstance(v, CustomUser):
                user = LazySSOUser(v.pk, cls.sso_field)
            elif isinstance(v, str):
                user = LazySSOUser(v, cls.sso_field)
            elif hasattr(v, "id"):
                user = LazySSOUser(v.id, cls.sso_field)
            else:
                raise TypeError(f"Invalid user id: {v}")
            return user

        def validator_with_context(v: Any, info: Any):
            user = _validate(v, info)
            data = user.get_full_data()
            if data is None:
                raise SSOUserNotFound(user_id=str(user))
            return user

        return core_schema.no_info_wrap_validator_function(
            validator_with_context,
            core_schema.any_schema(),
            serialization=core_schema.to_string_ser_schema()
        )

SSOUserPydanticField.sso_field = SSOUserField()
