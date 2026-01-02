from jose import jwt, JWSError, ExpiredSignatureError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .initializer import KeyCloakInitializer


ALGORITHM = KeyCloakInitializer.algorithms
SECRET_KEY_ALGORITHM = KeyCloakInitializer.secret_key_algorithm


authentication = HTTPBearer()

class UserPayload:
    def __init__(self, payload_dict: dict):
        self._payload = payload_dict
        self.__dict__.update(payload_dict)

    @property
    def id(self):
        return self._payload.get("sub")

    @property
    def username(self):
        return self._payload.get("preferred_username")

    @property
    def first_name(self):
        return self._payload.get("given_name")
    
    @property
    def last_name(self):
        return self._payload.get("family_name")
    
    @property
    def full_name(self):
        return self._payload.get("name")

    @property
    def groups(self):
        return self._payload.get("groups", [])

    @property
    def email(self):
        return self._payload.get("email")

    @property
    def roles(self):
        resource_access = self._payload.get("resource_access", {}) or {}
        realm_access = self._payload.get("realm_access", {}) or {}

        client_roles = (
            resource_access.get(KeyCloakInitializer.client_name, {})
                           .get("roles", [])
        )

        realm_roles = realm_access.get("roles", [])

        return {
            "client_roles": client_roles,
            "realm_roles": realm_roles
        }
    
    @property
    def profile(self):
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'roles': self.roles,
            'groups': self.groups
        }

    @property
    def companies(self):
        companies = self._payload.get("companies", [])
        return companies


async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(authentication)):
    token = credentials.credentials

    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid authentication credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    if not ALGORITHM or not SECRET_KEY_ALGORITHM:
        raise HTTPException(
            status_code=400,
            detail="ERROR: Keycloak ALGORITHM or SECRET_KEY_ALGORITHM is not set in environment or initializer.")

    try:

        if ALGORITHM.upper() == "RS256":
            key = f"-----BEGIN PUBLIC KEY-----\n{SECRET_KEY_ALGORITHM}\n-----END PUBLIC KEY-----"
        else:
            key = SECRET_KEY_ALGORITHM

        payload_dict = jwt.decode(token, key, algorithms=[ALGORITHM], options={"verify_aud": False})
        payload = UserPayload(payload_dict)

        if payload.id is None:
            raise auth_error

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Token signature has expired.'
        )
    except JWSError:
        raise auth_error

    return payload
