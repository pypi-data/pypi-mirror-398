from typing import Optional, List, Any, Dict
from pydantic import BaseModel, field_validator, model_validator
from ..sso.authenticate import CustomGroup


class GiveTokenSchema(BaseModel):
    username: str
    password: str


class LoginSchema(BaseModel):
    token: str
    refresh_token: str
    client_id: str


class GroupSchema(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    subGroups: Optional[List[Dict[str, Any]]] = None

    @model_validator(mode="before")
    def compute_title(cls, values):
        obj = values

        if hasattr(obj, "name"):
            values["title"] = obj.name

        elif isinstance(obj, dict) and obj.get("name"):
            values["title"] = obj["name"]

        return values

    @classmethod
    def from_instance(cls, instance):

        if not isinstance(instance, CustomGroup):
            instance = CustomGroup(payload=instance)

        if not instance.is_exists:
            return cls()  # empty model

        # Convert CustomGroup attributes to dict
        data = {
            "id": getattr(instance, "id", None),
            "name": getattr(instance, "name", None),
            "subGroups": getattr(instance, "subGroups", None),
        }

        return cls(**data)


class UserSchema(BaseModel):
    id: str
    username: str | None
    first_name: str | None
    last_name: str | None
    full_name: str | None
    roles: dict
    groups: list[str]


class PaginatedGroups(BaseModel):
    count: int
    limit: int
    offset: int
    results: List[GroupSchema]


class GroupCreateSchema(BaseModel):
    name: str

class AssignRoleGroupSchema(BaseModel):
    """assigning role to group one object"""
    role_id: str
    role_name: str


class AssignRoleGroupManySchema(BaseModel):
    """assigning role to group many object"""
    roles: List[AssignRoleGroupSchema]


class UserJoinGroupSchema(BaseModel):
    group_id: str
    user_id: str
