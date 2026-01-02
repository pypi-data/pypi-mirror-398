import inspect
from functools import wraps
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status, Depends
from .sso.utils import check_user_permission_access
from .auth import UserPayload,authenticate


def _is_coroutine(func):
    return callable(getattr(func, "__await__", None))

def check_permission_decorator(
    role_titles=None,
    group_titles=None,
    group_roles=None,
    match_group_roles=False,
    permissive=False,
):
    role_titles = role_titles or []
    group_titles = group_titles or []
    group_roles = group_roles or []

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: UserPayload = Depends(authenticate), **kwargs):
            if not user or not getattr(user, "id", None):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authentication required")

            if not role_titles and not group_titles and not group_roles:
                return await func(*args, user=user, **kwargs) if _is_coroutine(func) else func(*args, user=user, **kwargs)

            has_access = check_user_permission_access(
                user=user,
                role_titles=role_titles,
                group_titles=group_titles,
                group_roles=group_roles,
                match_group_roles=match_group_roles,
                permissive=permissive,
            )

            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this API")

            return await func(*args, user=user, **kwargs) if _is_coroutine(func) else func(*args, user=user, **kwargs)

        return wrapper
    return decorator


# ---------------- Helper decorators ----------------

def require_roles(*role_titles):
    return check_permission_decorator(role_titles=list(role_titles))


def require_groups(*group_titles):
    return check_permission_decorator(group_titles=list(group_titles))


def require_group_roles(*group_roles):
    return check_permission_decorator(group_roles=list(group_roles))


def require_any_group(*group_titles):
    group_titles = [r.lower() for r in group_titles if r]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: UserPayload = Depends(authenticate), **kwargs):
            if not user or not getattr(user, "id", None):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authentication required")

            if not group_titles:
                return await func(*args, user=user, **kwargs) if _is_coroutine(func) else func(*args, user=user, **kwargs)

            user_groups = getattr(user, 'groups', [])
            if not any(group in [g.lower() for g in user_groups] for group in group_titles):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this API")

            return await func(*args, user=user, **kwargs) if _is_coroutine(func) else func(*args, user=user, **kwargs)

        return wrapper
    return decorator

def require_any_role(*role_titles):
    role_titles = [r for r in role_titles if r]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: UserPayload = Depends(authenticate), **kwargs):
            if not user or not getattr(user, "id", None):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authentication required")

            if not role_titles:
                return await func(*args, user=user, **kwargs) if _is_coroutine(func) else func(*args, user=user, **kwargs)

            user_roles = set(user.roles.get("client_roles", []) + user.roles.get("realm_roles", []))
            user_roles = [r.lower() for r in user_roles if r]

            if any(role.lower() in user_roles for role in role_titles):
                return await func(*args, user=user, **kwargs) if _is_coroutine(func) else func(*args, user=user, **kwargs)

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to access this API")

        return wrapper
    return decorator

def require_all_permissions(
    *,
    role_titles=None,
    group_titles=None,
    group_roles=None,
    match_group_roles=False,
    permissive=False
):
    return check_permission_decorator(
        role_titles=role_titles or [],
        group_titles=group_titles or [],
        group_roles=group_roles or [],
        match_group_roles=match_group_roles,
        permissive=permissive
    )
