from fastapi import Depends
from fastapi_keycloak_sso.initializer import KeyCloakInitializer
from fastapi_keycloak_sso.auth import UserPayload, authenticate

def check_user_permission_access(
        user,
        role_titles: list[str],
        group_titles: list[str],
        group_roles: list[str],
        match_group_roles: bool = False,
        permissive: bool = False,
) -> bool :
    """
    Check permissions for either CustomUser or UserPayload.
    Extracts roles and groups from payload if needed.
    """

    # Realm roles
    user_roles = [r.lower() for r in getattr(user, "realm_access", {}).get("roles") or []]

    # Client roles
    client_name = KeyCloakInitializer.client_name
    user_client_roles = [
        r.lower() for r in (getattr(user, "resource_access", {}).get(client_name, {}).get("roles") or [])
    ]

    # Groups
    user_groups_raw = getattr(user, "groups", []) or []

    # Normalize input
    role_titles = [r.lower() for r in role_titles]
    group_titles = [g.lower() for g in group_titles]
    group_roles = [r.lower() for r in group_roles]

    # Parse groups (from paths like '/group_1/managers')
    parsed_user_groups = []
    for group_path in user_groups_raw:
        parts = group_path.strip("/").split("/")
        for part in parts:
            parsed_user_groups.append((part.lower(), None))

    # Rule 1: required roles
    denied_required_role = False
    require_required_role = False
    for required_role in role_titles:
        require_required_role = True
        if required_role not in user_roles and required_role not in user_client_roles:
            denied_required_role = True

    # Rule 2: required group titles
    denied_group_title_role = False
    require_group_title_role = False
    user_group_names = [group for group, _ in parsed_user_groups]
    for required_group in group_titles:
        require_group_title_role = True
        if required_group not in user_group_names:
            denied_group_title_role = True

    # Rule 3: required group roles
    denied_group_role = False
    require_group_role = False
    if group_roles:
        require_group_role = True
        matched = False
        for group, role in parsed_user_groups:
            if match_group_roles:
                if group in group_titles and role in group_roles:
                    matched = True
                    break
            else:
                if role in group_roles:
                    matched = True
                    break
        if not matched:
            denied_group_role = True

    # Adjust denied flags
    denied_required_role = denied_required_role if require_required_role else False
    denied_group_title_role = denied_group_title_role if require_group_title_role else False
    denied_group_role = denied_group_role if require_group_role else False

    # Return final decision
    if permissive:
        return not (denied_required_role and denied_group_title_role and denied_group_role)
    else:
        return not (denied_required_role or denied_group_title_role or denied_group_role)
