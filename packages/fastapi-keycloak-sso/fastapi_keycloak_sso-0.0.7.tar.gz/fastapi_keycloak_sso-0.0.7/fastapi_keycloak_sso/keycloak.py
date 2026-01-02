import gettext
import datetime
import time
import base64
import hashlib
import os
from enum import Enum
from typing import Type, Any, Optional
from urllib.parse import urlencode

import requests
from jose import exceptions as jose_exceptions
from jose import jwt
from fastapi import Response, status, Request
from .initializer import KeyCloakInitializer



gettext.bindtextdomain('myapp', 'locales')
gettext.textdomain('myapp')
_ = gettext.gettext


_jwks = None

class KeyCloakBaseManager(KeyCloakInitializer):
    class KeyCloakException(Exception):
        pass

    class KeyCloakNotFoundException(Exception):
        pass

    class KeyCloakGroupRoleChoices(str, Enum):
        MANAGER = "MANAGER"
        ASSISTANT = "ASSISTANT"
        EMPLOYEE = "EMPLOYEE"

    class KeyCloakClientTypeChoices(str, Enum):
        CONFIDENTIAL = "CONFIDENTIAL"
        PUBLIC = "PUBLIC"

    class KeyCloakPanelTypeChoices(str, Enum):
        ADMIN = "ADMIN"
        USER = "USER"

    class KeyCloakRequestMethodChoices(str, Enum):
        GET = "GET"
        POST = "POST"
        PUT = "PUT"
        DELETE = "DELETE"

    class KeyCloakSaveTokenMethodChoices(str, Enum):
        COOKIE = "COOKIE"
        HEADER = "HEADER"

    def __init__(self, save_token_method: str = KeyCloakSaveTokenMethodChoices.HEADER):
        self.save_token_method =  save_token_method

    def _get_jwks(self):
        global _jwks
        if not _jwks:
            resp = requests.get(
                self.jwks_url,
                verify=False
            )
            resp.raise_for_status()
            _jwks = resp.json()
        return _jwks

    def decode_token(self, token: str):
        jwks = self._get_jwks()
        try:
            decoded_content = jwt.decode(
                token,
                jwks,
                algorithms=[self.algorithms],
                audience=self.user_audience
            )
        except (jose_exceptions.JWTError, jose_exceptions.ExpiredSignatureError, jose_exceptions.JWTClaimsError) as e:
            raise self.KeyCloakException(f"Failed to decode token : {str(e)}")
        return decoded_content

    @staticmethod
    def _generate_code_verifier() -> str:
        return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')

    @staticmethod
    def _generate_code_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('utf-8')

    @classmethod
    def validate_enum_value(cls, value: str, enum_class: Type[Enum]):
        if value not in [e.value for e in enum_class]:
            raise cls.KeyCloakException(f"Value '{value}' is not valid for {enum_class.__name__}")

    @staticmethod
    def _build_url(base_url: str, endpoint: str, params: dict = None) -> str:
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url

    def _get_headers(self, extra_headers: dict = None) -> dict:
        headers = {}
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _get_request_data(
            self,
            *,
            endpoint: str,
            request_method: KeyCloakRequestMethodChoices,
            post_data: Any = None,
            extra_headers: dict = None,
            is_admin: bool = False
        ) -> Any:
            url = f"{self.base_admin_url}{endpoint}" if is_admin else f"{self.base_panel_url}{endpoint}"
            headers = self._get_headers(extra_headers)

            try:
                response = None

                if request_method == self.KeyCloakRequestMethodChoices.GET:
                    response = requests.get(url, headers=headers, verify=False)

                elif request_method == self.KeyCloakRequestMethodChoices.POST:
                    content_type = headers.get("Content-Type", "").lower()
                    if "application/json" in content_type:
                        response = requests.post(url, headers=headers, json=post_data, verify=False)
                    else:
                        response = requests.post(url, headers=headers, data=post_data, verify=False)

                elif request_method == self.KeyCloakRequestMethodChoices.PUT:
                    content_type = headers.get("Content-Type", "").lower()
                    if "application/json" in content_type:
                        response = requests.put(url, headers=headers, json=post_data, verify=False)
                    else:
                        response = requests.put(url, headers=headers, data=post_data, verify=False)

                elif request_method == self.KeyCloakRequestMethodChoices.DELETE:
                    response = requests.delete(url, headers=headers, data=post_data, verify=False)

                if response is not None:
                    response.raise_for_status()
                    if response.status_code in (200, 201, 204):
                        if not response.content or not response.content.strip():
                            return {"detail": "Request successful"}
                        try:
                            return response.json()
                        except ValueError:
                            return {"detail": "Non-JSON response", "raw": response.text}

            except requests.HTTPError as http_err:
                if http_err.response.status_code == 404:
                    raise self.KeyCloakNotFoundException(f"Not found: {url}")
                elif http_err.response.status_code == 409:
                    raise self.KeyCloakException("Conflict: object already exists")
                else:
                    raise self.KeyCloakException(str(http_err))
            except Exception as err:
                raise self.KeyCloakException(str(err))

    def send_request(
        self,
        request_type: Enum,
        request_type_choices: Type[Enum],
        request_method: KeyCloakRequestMethodChoices,
        panel_type: KeyCloakPanelTypeChoices,
        *args,
        **kwargs
    ):
        
        if request_method not in self.KeyCloakRequestMethodChoices:
            raise self.KeyCloakException("Invalid request method")
        if panel_type not in self.KeyCloakPanelTypeChoices:
            raise self.KeyCloakException("Invalid panel type")
        if request_type not in request_type_choices:
            raise self.KeyCloakException("Invalid request type")


        get_data_method = getattr(self, f"_{request_method.lower()}_{request_type.name.lower()}", None)
        if not get_data_method or not callable(get_data_method):
            raise self.KeyCloakException("Data get method for Keycloak is not defined")
        return get_data_method(*args, **kwargs)
    
    @staticmethod
    def get_token_from_header(request):
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if auth.startswith('Bearer '):
            return auth.split(' ')[1]
        return None

    @staticmethod
    def get_token_from_cookie(request, key: str) -> str:
        token = request.COOKIES.get(key, None)
        return token

    @staticmethod
    def get_token_from_request(request: Request, key: str) -> str | None:
        token = None

        try:
            body = request.json()
            token = body.get(key)
        except Exception:
            pass

        if token is None:
            try:
                form = request.form()
                token = form.get(key)
            except Exception:
                pass

        if token is None:
            token = request.query_params.get(key)
        return token

    def get_token(self, request, key: str = '') -> str:
        token = None
        if self.save_token_method == self.KeyCloakSaveTokenMethodChoices.COOKIE:
            token = self.get_token_from_cookie(request, key)
        elif self.save_token_method == self.KeyCloakSaveTokenMethodChoices.HEADER:
            if key == 'access_token':
                token = self.get_token_from_header(request)
            else:
                token = self.get_token_from_request(request, key)
        return token


class KeyCloakConfidentialClient(KeyCloakBaseManager):
    default_client_roles = [
        "offline_access",
        "uma_authorization",
        "default-roles-markaz",
    ]

    class KeyCloakRequestTypeChoices(str, Enum):
        CLIENT_CREDENTIALS_ACCESS_TOKEN = "CLIENT_CREDENTIALS_ACCESS_TOKEN"
        PASSWORD_ACCESS_TOKEN = "PASSWORD_ACCESS_TOKEN"
        REFRESH_ACCESS_TOKEN = "REFRESH_ACCESS_TOKEN"
        INTROSPECT_TOKEN = "INTROSPECT_TOKEN"
        USER_INFO = "USER_INFO"
        LOGOUT = "LOGOUT"
        JWKS_VERIFY = "JWKS_VERIFY"
        GROUPS = "GROUPS"
        USERS = "USERS"
        USER_ROLES = "USER_ROLES"
        USER_GROUPS = "USER_GROUPS"
        CLIENT_ROLES = "CLIENT_ROLES"
        ASSIGN_ROLE_GROUP = "ASSIGN_ROLE_GROUP"
        USER_JOIN_GROUP = "USER_JOIN_GROUP"
        FIND_GROUP = "FIND_GROUP"

    KEYCLOAK_TOKEN_CACHE_KEY = "keycloak_credentials_client_access_token"
    KEYCLOAK_TOKEN_EXPIRE_KEY = "keycloak_credentials_client_access_token_expiry"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_type = self.KeyCloakClientTypeChoices.CONFIDENTIAL

    def set_client_access_token(self, headers: dict) -> dict:
        access_token = self.get_cached_access_token()
        headers.update({"Authorization": f"Bearer {access_token}"})
        return headers

    def _get_jwks(self):
        global _jwks
        if not _jwks:
            resp = requests.get(self.jwks_url, verify=False)
            resp.raise_for_status()
            _jwks = resp.json()
        return _jwks
    

    @staticmethod
    def set_httponly_cookie(
        key: str,
        value: str,
        response: Optional[Response] = None,
        expires_hours: int = 1
    ) -> Response:
        if not response:
            response = Response(status_code=status.HTTP_200_OK)
        expire_time = datetime.datetime.utcnow() + datetime.timedelta(hours=expires_hours)
        response.set_cookie(
            key=key,
            value=value,
            httponly=True,
            secure=False,
            expires=expire_time.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            samesite="Lax"
        )
        return response
    
    @staticmethod
    def _build_filter_url(*, base_url: str, extra_query_params: dict = None, detail_pk: str | None = None) -> str:
        query_params = {}
        base_url = f'{base_url}/{detail_pk}' if detail_pk else base_url
        if extra_query_params:
            query_params.update(extra_query_params)
        return f"{base_url}?{urlencode(query_params)}" if query_params else base_url

    def get_cached_access_token(self):

        cache_dict = getattr(self, "_token_cache", {})
        access_token = cache_dict.get(self.KEYCLOAK_TOKEN_CACHE_KEY)
        expiry_time = cache_dict.get(self.KEYCLOAK_TOKEN_EXPIRE_KEY)
        if access_token and expiry_time and expiry_time > time.time():
            return access_token

        return self._post_client_credentials_access_token()



    def _post_client_credentials_access_token(self, *args, **kwargs):
        endpoint = "/protocol/openid-connect/token"
        endpoint = self._build_filter_url(base_url=endpoint, **kwargs)

        post_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.POST,
            extra_headers=None,
            post_data=post_data,
            is_admin=False
        )

        if response_data:
            access_token = response_data.get("access_token")
            expires_in = response_data.get("expires_in", 300)  # default 5 mins

            self._token_cache = getattr(self, "_token_cache", {})
            self._token_cache[self.KEYCLOAK_TOKEN_CACHE_KEY] = access_token
            self._token_cache[self.KEYCLOAK_TOKEN_EXPIRE_KEY] = time.time() + expires_in - 30

            return access_token

        raise self.KeyCloakException("Failed to retrieve client credentials access token")


    def _post_password_access_token(self, username: str, password: str, *args, **kwargs):
        endpoint = "/protocol/openid-connect/token"
        endpoint = self._build_filter_url(base_url=endpoint, **kwargs)
        post_data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password,
        }
        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.POST,
            extra_headers=None,
            post_data=post_data,
            is_admin=False
        )

        if response_data:
            return response_data.get('access_token', None)
        else:
            raise self.KeyCloakException(_("Failed to retrieve data"))


    def _post_refresh_access_token(self, refresh_token: str, client_id: str = None, *args, **kwargs) -> dict:
        endpoint = "/protocol/openid-connect/token"
        endpoint = self._build_filter_url(base_url=endpoint, **kwargs)
        post_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        if client_id:
            post_data.update({
                "client_id": client_id,
            })
        else:
            post_data.update({
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            })
        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.POST,
            extra_headers=None,
            post_data=post_data,
            is_admin=False
        )

        if not response_data:
            raise self.KeyCloakException(_("Failed to retrieve data"))
        return response_data


    def _get_groups(self , *args, **kwargs) -> dict:
        """
        Retrieves all groups from Keycloak using the Admin REST API.
        Requires a valid admin-level access token.
        """
        endpoint = "/groups"
        endpoint = self._build_filter_url(base_url=endpoint, **kwargs)
        extra_headers = {
            "Content-Type": "application/json"
        }
        extra_headers = self.set_client_access_token(extra_headers)
        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.GET,
            extra_headers=extra_headers,
            post_data=None,
            is_admin=True
        )

        if not response_data:
            raise self.KeyCloakException(_("Failed to retrieve groups from Keycloak"))

        return response_data

    def _get_users(self, *args, **kwargs) -> dict:
        """
        Retrieves all users from Keycloak using the Admin REST API.
        Requires a valid admin-level access token.
        """
        endpoint = "/users"
        endpoint = self._build_filter_url(base_url=endpoint, **kwargs)
        extra_headers = {
            "Content-Type": "application/json"
        }
        extra_headers = self.set_client_access_token(extra_headers)
        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.GET,
            extra_headers=extra_headers,
            post_data=None,
            is_admin=True
        )

        if not response_data:
            raise self.KeyCloakException(_("Failed to retrieve users from Keycloak"))

        return response_data


    # for create group
    def _post_groups(self , name: str , group_parent_id: str = None):
        endpoint = '/groups'

        if group_parent_id:
            endpoint = f'/groups/{group_parent_id}/children'

        endpoint = self._build_filter_url(base_url=endpoint)
        extra_headers = {
            "Content-Type": "application/json"
        }
        data = {
            'name': name
        }
        extra_headers = self.set_client_access_token(extra_headers)
        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.POST,
            extra_headers=extra_headers,
            post_data=data,
            is_admin=True
        )
        return response_data

    def _delete_groups(self , group_id: str):
        endpoint = f'/groups/{group_id}'
        endpoint = self._build_filter_url(base_url=endpoint)
        extra_headers = {
            "Content-Type": "application/json"
        }
        extra_headers = self.set_client_access_token(extra_headers)
        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.DELETE,
            extra_headers=extra_headers,
            post_data=None,
            is_admin=True
        )
        return response_data

    def _get_client_roles(self , role_id: str = None):
        endpoint = f'/clients/{self.client_pk}/roles'
        if role_id:
            endpoint = f'/roles-by-id/{role_id}'

        endpoint = self._build_filter_url(base_url=endpoint)
        extra_headers = {
            "Content-Type": "application/json"
        }
        extra_headers = self.set_client_access_token(extra_headers)
        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.GET,
            extra_headers=extra_headers,
            post_data=None,
            is_admin=True
        )
        return response_data

    def _post_assign_role_group(self, group_id: str , roles: dict):
        endpoint = f'/groups/{group_id}/role-mappings/clients/{self.client_pk}'
        endpoint = self._build_filter_url(base_url=endpoint)
        extra_headers = {
            "Content-Type": "application/json"
        }
        extra_headers = self.set_client_access_token(extra_headers)

        role_objects = roles['roles']

        data = []
        for role in role_objects:
            role_id = role['role_id']
            role_name = role['role_name']
            data.append({
                'id' : role_id,
                'name' : role_name
            })

        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.POST,
            extra_headers=extra_headers,
            post_data=data,
            is_admin=True
        )
        return response_data

    def _put_user_join_group(self,user_id,group_id):
        endpoint = f'/users/{user_id}/groups/{group_id}'
        endpoint = self._build_filter_url(base_url=endpoint)
        extra_headers = {
            "Content-Type": "application/json"
        }
        extra_headers = self.set_client_access_token(extra_headers)

        response_data = self._get_request_data(
            endpoint=endpoint,
            request_method=self.KeyCloakRequestMethodChoices.PUT,
            extra_headers=extra_headers,
            post_data=None,
            is_admin=True
        )
        return response_data
