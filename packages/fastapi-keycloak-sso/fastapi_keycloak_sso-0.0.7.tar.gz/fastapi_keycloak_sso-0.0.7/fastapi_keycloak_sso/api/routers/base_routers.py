from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
    Request,
    Query,
    Path
)
from fastapi.responses import JSONResponse
from fastapi_keycloak_sso.initializer import RoutAccessInitializer
from fastapi_keycloak_sso.api.schemas import (
    LoginSchema,
    GiveTokenSchema,
    GroupSchema,
    PaginatedGroups,
    UserSchema,
    GroupCreateSchema,
    AssignRoleGroupManySchema,
    UserJoinGroupSchema
)
from fastapi_keycloak_sso.keycloak import KeyCloakConfidentialClient
from fastapi_keycloak_sso.auth import (
    authenticate,
    UserPayload
)
from fastapi_keycloak_sso.api.enums import DetailType
from fastapi_keycloak_sso.decorators import require_any_group


router = APIRouter(prefix='/keycloak')

# to routs access
access = {
    'group_read': RoutAccessInitializer.group_read_access,
    'group_find': RoutAccessInitializer.group_find_access,
    'group_create': RoutAccessInitializer.group_create_access,
    'group_delete': RoutAccessInitializer.group_delete_access,
    'users_read': RoutAccessInitializer.user_read_access,
    'roles_read': RoutAccessInitializer.role_read_access,
    'assign_role_group': RoutAccessInitializer.assign_role_group_access,
    'join_user_group': RoutAccessInitializer.join_user_group_access
}


@router.post('/token/', status_code=status.HTTP_200_OK, responses={
     200: {"description": "string"},
     400: {'description': {'detail':'string'}}
}, tags=['KeyCloak - Accounts'])
def give_access_token(body: GiveTokenSchema):
    """
    Create token for given user
    """
    keycloak = KeyCloakConfidentialClient()

    username = body.username
    password = body.password

    try:
        access_key = keycloak.send_request(
            request_type= keycloak.KeyCloakRequestTypeChoices.PASSWORD_ACCESS_TOKEN,
            request_type_choices= keycloak.KeyCloakRequestTypeChoices,
            request_method= keycloak.KeyCloakRequestMethodChoices.POST,
            panel_type= keycloak.KeyCloakPanelTypeChoices.USER,
            username=username,
            password=password
        )
    except keycloak.KeyCloakException as e:
        return JSONResponse({'detail': str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(access_key, status_code=status.HTTP_200_OK)


@router.post('/login/', status_code=status.HTTP_200_OK, responses={
    200: {'message':'string'},
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {"error": "string"}
            }
        }}
},tags=['KeyCloak - Accounts'])
def login(body: LoginSchema):
    """
    Set received token from keycloak on request cookie
    """
    keycloak_klass = KeyCloakConfidentialClient()

    try:
        decoded_token = keycloak_klass.decode_token(body.token)
    except KeyCloakConfidentialClient.KeyCloakException as e:
        return Response({"error": str(e)}, status_code=status.HTTP_401_UNAUTHORIZED)

    response = JSONResponse({
        "message": "Login successful",
        "token": body.token,
        "user": decoded_token
    }, status_code=status.HTTP_200_OK)

    if keycloak_klass.save_token_method == keycloak_klass.KeyCloakSaveTokenMethodChoices.COOKIE:
        response = keycloak_klass.set_httponly_cookie('access_token', body.token, response)
        response = keycloak_klass.set_httponly_cookie('refresh_token', body.refresh_token, response)
        response = keycloak_klass.set_httponly_cookie('client_id', body.client_id, response)

    return response

@router.post('/token/refresh/', status_code=status.HTTP_200_OK, responses={
    200: {"description": "string"},
    401: {
        "description": "No refresh token or client ID / Token refresh failed",
        "content": {
            "application/json": {
                "example": {"detail": "string"}
            }
        }}
},tags=['KeyCloak - Accounts'])
def refresh_token(request: Request):
    """
    Refresh received token from keycloak
    """

    keycloak_klass = KeyCloakConfidentialClient()
    refresh_token = keycloak_klass.get_token(request, 'refresh_token')
    client_id = keycloak_klass.get_token(request, 'client_id')

    if not refresh_token or not client_id:
        return JSONResponse({"detail": "No refresh token Or Client ID"}, status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        new_tokens = keycloak_klass.send_request(
            keycloak_klass.KeyCloakRequestTypeChoices.REFRESH_ACCESS_TOKEN,
            keycloak_klass.KeyCloakRequestTypeChoices,
            keycloak_klass.KeyCloakRequestMethodChoices.POST,
            keycloak_klass.KeyCloakPanelTypeChoices.USER,
            refresh_token=refresh_token,
            client_id=client_id,
        )
    except Exception as e:
        return JSONResponse({"detail": "string"}, status_code=status.HTTP_401_UNAUTHORIZED)

    response = JSONResponse({"detail": "Token refreshed"}, status_code=status.HTTP_200_OK)
    response.set_cookie("access_token", new_tokens["access_token"], httponly=True, secure=True)

    if keycloak_klass.save_token_method == keycloak_klass.KeyCloakSaveTokenMethodChoices.COOKIE:
        response = keycloak_klass.set_httponly_cookie('refresh_token', refresh_token, response)
        if "refresh_token" in new_tokens:
            response.set_cookie("refresh_token", new_tokens["refresh_token"], httponly=True, secure=True)
        return response

    return JSONResponse(new_tokens, status_code=status.HTTP_200_OK)


@router.post('/logout/', status_code=status.HTTP_200_OK, responses = {
            200: {
                'description': 'Logged out successfully',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string', 'example': 'Logged out'}
                            }
                        }
                    }
                }
            },
            401: {
                'description': 'No refresh token or client ID',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                  }
            }
},tags=['KeyCloak - Accounts'])
def logout(request: Request, user: UserPayload = Depends(authenticate)):
    """
    Logging out the user and deleting data from cookies
    """

    keycloak_klass = KeyCloakConfidentialClient()
    refresh_token = keycloak_klass.get_token(request, 'refresh_token')
    client_id = keycloak_klass.get_token(request, 'client_id')

    if not refresh_token or not client_id:
        return JSONResponse({"detail": "No refresh token Or Client ID"}, status_code=status.HTTP_401_UNAUTHORIZED)

    logout_res = keycloak_klass.send_request(
        keycloak_klass.KeyCloakRequestTypeChoices.LOGOUT,
        keycloak_klass.KeyCloakRequestTypeChoices,
        keycloak_klass.KeyCloakRequestMethodChoices.POST,
        keycloak_klass.KeyCloakPanelTypeChoices.USER,
        refresh_token=refresh_token,
        client_id=client_id,
    )

    if keycloak_klass.save_token_method == keycloak_klass.KeyCloakSaveTokenMethodChoices.COOKIE:
        response = JSONResponse({"detail": "Logged out"}, status_code=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        response.delete_cookie("client_id")
        return response

    return JSONResponse({"detail": "Logged out"}, status_code=status.HTTP_200_OK)


@router.get("/groups/", response_model=PaginatedGroups,tags=['KeyCloak - Admin'])
@require_any_group(*access['group_read'])
def group_read(
    pk: str = None,
    limit: int = Query(10, ge=1, le=100,
                       description='Maximum number of results to return (page size). Default is 10.'),
    offset: int = Query(0, ge=0,
                        description='Number of items to skip before starting to return results (starting index)'),
    user: UserPayload = Depends(authenticate)
):
    """
    Reading existing groups in the Realm system
    """

    keycloak_klass = KeyCloakConfidentialClient()

    try:
        response = keycloak_klass.send_request(
            keycloak_klass.KeyCloakRequestTypeChoices.GROUPS,
            keycloak_klass.KeyCloakRequestTypeChoices,
            keycloak_klass.KeyCloakRequestMethodChoices.GET,
            keycloak_klass.KeyCloakPanelTypeChoices.ADMIN,
            detail_pk=pk,
        )

        # Normalize empty or single result
        if response is None:
            response = []
        elif not isinstance(response, list):
            response = [response]

        # Convert raw dicts → Pydantic models
        groups = [GroupSchema.from_instance(item) for item in response]

        total = len(groups)

        # Apply pagination
        paginated = groups[offset : offset + limit]

        return PaginatedGroups(
            count=total,
            limit=limit,
            offset=offset,
            results=paginated
        )

    except keycloak_klass.KeyCloakNotFoundException:
        return JSONResponse({"detail": "Requested group not found"}, status_code=404)
    
@router.get('/profile/', response_model=UserSchema, status_code=status.HTTP_200_OK,
            tags=['KeyCloak - Admin'])
def user_profile(user: UserPayload = Depends(authenticate)):
    """
    Read profile data
    """
    return user.profile


def _find_group_exact(groups, search_name):
    """
    Recursively find the exact group (name matches exactly).
    Returns the full group object.
    """
    for group in groups:
        if group.get("name") == search_name:
            return group

        sub_groups = group.get("subGroups") or []
        if sub_groups:
            result = _find_group_exact(sub_groups, search_name)
            if result:
                return result

    return None


@router.get('/group/{group_name}/',tags=['KeyCloak - Admin'])
@require_any_group(*access['group_find'])
def find_group_detail_exact(
    group_name: str = Path(description='Enter group name'),
    detailing_type: DetailType = Query(
        default=DetailType.id,
        description="Type of detail to return: 'id' for group ID, 'full' for full group object"),
    user: UserPayload = Depends(authenticate)
):
    """
    Get exact group by name.
    """
    keycloak = KeyCloakConfidentialClient()

    # Extra params: search param helps Keycloak filter server-side
    extra_params = {'extra_query_params': {'search': group_name}}

    try:
        groups = keycloak.send_request(
            keycloak.KeyCloakRequestTypeChoices.GROUPS,
            keycloak.KeyCloakRequestTypeChoices,
            keycloak.KeyCloakRequestMethodChoices.GET,
            keycloak.KeyCloakPanelTypeChoices.ADMIN,
            **extra_params
        )

        group = _find_group_exact(groups, group_name)

        if not group:
            return JSONResponse(
                {"detail": "Group name not found"},
                status_code=status.HTTP_404_NOT_FOUND
            )

        if detailing_type == DetailType.id:
            return {"id": group.get("id")}

        return group

    except Exception as e:
        return JSONResponse(
            {"detail": "Error fetching groups", "error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get('/users/',tags=['KeyCloak - Admin'])
@require_any_group(*access['users_read'])
def users_read(
        user: UserPayload = Depends(authenticate),
        pk: str = None,
):
    """
    Read user information.
    """
    keycloak_klass = KeyCloakConfidentialClient()

    try:
        response = keycloak_klass.send_request(
            keycloak_klass.KeyCloakRequestTypeChoices.USERS,
            keycloak_klass.KeyCloakRequestTypeChoices,
            keycloak_klass.KeyCloakRequestMethodChoices.GET,
            keycloak_klass.KeyCloakPanelTypeChoices.ADMIN,
            detail_pk=pk,
        )
    except keycloak_klass.KeyCloakNotFoundException as e:
        return JSONResponse(
            {"detail": "Requested user data was not found"},
            status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(response, status_code=status.HTTP_200_OK)

@router.post('/groups/create/',tags=['KeyCloak - Admin'])
@require_any_group(*access['group_create'])
def group_create(
    body: GroupCreateSchema,
    group_parent_id: str = Query(default=None,description='Enter the group ID above of the branch.'),
    user: UserPayload = Depends(authenticate)
):
    """
    Create a group in a realm or create a group in a subdirectory of another group.
    """
    keycloak = KeyCloakConfidentialClient()

    group_name = body.name

    try:
        response = keycloak.send_request(
            keycloak.KeyCloakRequestTypeChoices.GROUPS,
            keycloak.KeyCloakRequestTypeChoices,
            keycloak.KeyCloakRequestMethodChoices.POST,
            keycloak.KeyCloakPanelTypeChoices.ADMIN,
            name=group_name,
            group_parent_id=group_parent_id,
        )

    except Exception as e:
        return JSONResponse({
            'detail': str(e)
        },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    return JSONResponse(response, status_code=status.HTTP_200_OK)


@router.delete('/groups/{group_id}/',tags=['KeyCloak - Admin'])
@require_any_group(*access['group_delete'])
def group_delete(
        group_id: str,
        user: UserPayload = Depends(authenticate)
):
    """
    Delete group by id.
    """
    keycloak = KeyCloakConfidentialClient()

    try:
        response = keycloak.send_request(
            keycloak.KeyCloakRequestTypeChoices.GROUPS,
            keycloak.KeyCloakRequestTypeChoices,
            keycloak.KeyCloakRequestMethodChoices.DELETE,
            keycloak.KeyCloakPanelTypeChoices.ADMIN,
            group_id=group_id
        )

    except Exception as e:
        return JSONResponse({'detail':str(e)},
                            status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(response, status_code=status.HTTP_200_OK)

@router.get('/roles/',tags=['KeyCloak - Admin'])
@require_any_group(*access['roles_read'])
def role_read(
        user: UserPayload = Depends(authenticate),
        role_id: str = Query(default=None,description='Enter the role ID.'),
):
    """
    Reading client roles
    """
    keycloak = KeyCloakConfidentialClient()
    try:
        response = keycloak.send_request(
            keycloak.KeyCloakRequestTypeChoices.CLIENT_ROLES,
            keycloak.KeyCloakRequestTypeChoices,
            keycloak.KeyCloakRequestMethodChoices.GET,
            keycloak.KeyCloakPanelTypeChoices.ADMIN,
            role_id=role_id
        )
    except Exception as e:
        return JSONResponse({"detail": str(e)},
                            status_code=status.HTTP_400_BAD_REQUEST)

    return JSONResponse(response, status_code=status.HTTP_200_OK)


@router.post('/groups/{group_id}/roles/assign/',tags=['KeyCloak - Admin'])
@require_any_group(*access['assign_role_group'])
def assign_roles_to_group(
        roles: AssignRoleGroupManySchema,
        group_id: str,
        user: UserPayload = Depends(authenticate)
):
    """
    Assigning roles to group
    """
    keycloak = KeyCloakConfidentialClient()

    try:
        response = keycloak.send_request(
            keycloak.KeyCloakRequestTypeChoices.ASSIGN_ROLE_GROUP,
            keycloak.KeyCloakRequestTypeChoices,
            keycloak.KeyCloakRequestMethodChoices.POST,
            keycloak.KeyCloakPanelTypeChoices.ADMIN,
            group_id=group_id,
            roles=roles.dict()
        )

    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

    return JSONResponse(response, status_code=status.HTTP_200_OK)


@router.post('/users/group/join/',tags=['KeyCloak - Admin'])
@require_any_group(*access['join_user_group'])
def user_join_to_group(
        body: UserJoinGroupSchema,
        user: UserPayload = Depends(authenticate)
):
    """
    User membership to a group using their IDs
    """
    keycloak = KeyCloakConfidentialClient()

    try:
        response = keycloak.send_request(
            keycloak.KeyCloakRequestTypeChoices.USER_JOIN_GROUP,
            keycloak.KeyCloakRequestTypeChoices,
            keycloak.KeyCloakRequestMethodChoices.PUT,
            keycloak.KeyCloakPanelTypeChoices.ADMIN,
            user_id=body.user_id,
            group_id=body.group_id,
        )

    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

    return JSONResponse(response, status_code=status.HTTP_200_OK)
