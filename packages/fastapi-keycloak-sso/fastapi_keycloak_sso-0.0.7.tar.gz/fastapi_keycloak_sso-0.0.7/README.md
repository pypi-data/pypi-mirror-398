#  FastAPI-Keycloak Integration

This package is used when you want to manage users in your services in a keycloak environment.

## Install

Installation command from pypi:

```python
 pip install fastapi-keycloak-sso
```

Setting up the authenticate function and UserPayload to use authentication:

```python
from fastapi import FastAPI, Depends
from fastapi_keycloak_sso.auth import UserPayload, authenticate

app = FastAPI()

@app.get('/')
def test_api(user: UserPayload = Depends(authenticate)):
    pass
```

For proper identification, you should use the 'user' parameter in your route.


## Environment  Configurations

To use the authentication features of this package, you need to set the following in your '.env' file:

(Preferably the '.env' file is next to your project's main file)

```python
# Keycloak SSO
KEYCLOAK_SERVER_URL=https://sso.domain # if using in dokcer : https://<keycloak_container>:8443
KEYCLOAK_ISSUER_PREFIX=https://sso.domain 
KEYCLOAK_REALM=your_realm
KEYCLOAK_CLIENT_ID=your_client_id 
KEYCLOAK_CLIENT_PK=your_client_primary_key # example: 'test-client'
KEYCLOAK_CLIENT_SECRET=your_client_secret_key
KEYCLOAK_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/auth/callback/ # for login in ssr sites
KEYCLOAK_CLIENT_NAME=your_client_name
KEYCLOAK_CLIENT_TITLE=your_client_title
KEYCLOAK_ALGORITHMS=RS256
KEYCLOAK_SECRET_KEY_ALGORITHM=your_algorithm_secret_key # if using RS256: Go to Realm Settings > Keys > your algorithm public key 

# redis config (to user's data caching)
KEYCLOAK_REDIS_HOST=<your_redis_host>
```

## Predefined fields

### Model fields
* SSOUserField

The default for this field is string type.

### Usage Example

```python
from fastapi_keycloak_sso.sso import fields as sso_fields
from sqlalchemy import Column

class UserTest(Base):
    ...
    user_id = Column(sso_fields.SSOUserField)
    

```

### Pydantic fields

* SSOUserPydanticField
* SSOUserPydanticWithValidation

If you want to make sure the user exists in your system before saving or reading information,
use the 'SSOUserPydanticWithValidation' field.

### Usage Example

```python
from fastapi_keycloak_sso.sso import schemas as sso_schemas
from pydantic import BaseModel

class UserSchema(BaseModel):
    ...
    user_id: sso_schemas.SSOUserPydanticField
```
To get the complete information of the desired user and display it,
you can do the following to get a dictionary of information:

```python
from fastapi_keycloak_sso.sso import schemas as sso_schemas
from pydantic import (
    BaseModel,
    field_serializer
)

class UserSchema(BaseModel):
    ...
    user_id = sso_schemas.SSOUserPydanticField
    
    @field_serializer("user_id")
    def serialize_user_id(self, value: sso_schemas.LazySSOUser, _info):
        return value.get_full_data()
```


## Permissions

To use access levels for users in your Keycloak system, you can use the decorators available in the package:


```python
from fastapi_keycloak_sso.decorators import (
    require_roles,
    require_groups,
    require_group_roles,
    require_any_group,
    require_any_role,
    require_all_permissions
)

@app.get('/')
@requiire_groups('test-admin','test-editor')
def test_api(user: UserPayload = Depends(authenticate)):
    pass
```

All decorators should be close to the rout and the associated permissions should be entered as str inside the decorator.


### require_roles:

In this decorator, the user must have all the permissions entered to access rout.


### require_groups:

To check that the user must exist in all groups entered in the decorator.

### require_group_roles:

@require_group_roles(*group_roles, match_group_roles=False)

Checks if the user has at least one of the specified roles within any group. Use match_group_roles=True to only allow matches where the group name is also explicitly listed via @require_groups.

```python
@app.get('/')
@require_group_roles('manager')  # Any group
@require_group_roles('admin', match_group_roles=True)  # Must match both group and role
def test_api():
    pass
```

### require_any_group:

The user must belong to at least one of the groups listed.

### require_any_role:

The user must belong to at least one of the roles listed.

### require_all_permissions:

@require_all_permissions(role_titles=[], group_titles=[], group_roles=[], match_group_roles=False)

Combined decorator that allows you to check all types of permissions in one call.

```python
@app.get('/')
@require_all_permissions(
    role_titles=['superuser'],
    group_titles=['group_1'],
    group_roles=['manager'],
    match_group_roles=True
)
def test_api():
    pass
```

### Default APIs

To use default APIs, you must include them in your system app.

```python
from fastapi_keycloak_sso.api.routers.base_routers import router as keycloak_router


app = FastAPI()

app.include_router(keycloak_router)
```


The package provides a number of default APIs to make it easy to work with your keycloak system:

* Set token cookie
* Logout token from cookie
* Create token
* Refresh token
* User profile
* Group read
* Find group detail exact
* Group create
* Group delete
* Role read
* Assign role to group
* User join to group


### Setting permissions on default APIs:
By default, the existing APIs do not have any specific permissions,
but you can enforce them by adding the permissions you need to your '.env' file.

It is worth noting that your input permissions are checked against user groups,
and the user must have at least one of the entries.

```python
# Keycloak access groups
KEYCLOAK_GROUP_READ_ACCESS=admin,test
KEYCLOAK_GROUP_FIND_ACCESS=admin,test
KEYCLOAK_GROUP_CREATE_ACCESS=admin,test
KEYCLOAK_GROUP_DELETE_ACCESS=admin,test
KEYCLOAK_USER_READ_ACCESS=admin,test
KEYCLOAK_ROLE_READ_ACCESS=admin,test
KEYCLOAK_ASSIGN_ROLE_GROUP_ACCESS=admin,test
KEYCLOAK_JOIN_USER_GROUP_ACCESS=admin,test
```
