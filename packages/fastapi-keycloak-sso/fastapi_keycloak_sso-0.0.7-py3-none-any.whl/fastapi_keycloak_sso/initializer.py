import os
from dotenv import load_dotenv, find_dotenv


env_path = find_dotenv(usecwd=True)
load_dotenv(env_path)


class KeyCloakInitializer:
    realm = os.getenv('KEYCLOAK_REALM')
    client_id = os.getenv('KEYCLOAK_CLIENT_ID')
    client_pk = os.getenv('KEYCLOAK_CLIENT_PK')
    client_title = os.getenv('KEYCLOAK_CLIENT_TITLE')
    client_name = os.getenv('KEYCLOAK_CLIENT_NAME')
    algorithms = os.getenv('KEYCLOAK_ALGORITHMS')
    secret_key_algorithm = os.getenv('KEYCLOAK_SECRET_KEY_ALGORITHM')
    user_audience = "account"
    base_prefix_url = os.getenv('KEYCLOAK_SERVER_URL')
    base_panel_url = f'{base_prefix_url}/realms/{realm}'
    base_admin_url = f'{base_prefix_url}/admin/realms/{realm}'
    jwks_url = f"{base_panel_url}/protocol/openid-connect/certs"
    issuer_prefix = os.getenv('KEYCLOAK_ISSUER_PREFIX')
    issuer = f'{issuer_prefix}/realms/{realm}'
    client_secret = os.getenv('KEYCLOAK_CLIENT_SECRET')
    admin_groups = os.getenv('ADMIN_GROUPS')  # list set in env split(',')
    service_base_url = os.getenv('SSO_SERVICE_BASE_URL')
    redis_host = os.getenv('KEYCLOAK_REDIS_HOST')


class RoutAccessInitializer:
    group_read_access = (os.getenv('KEYCLOAK_GROUP_READ_ACCESS') or "").split(',') or None
    group_find_access = (os.getenv('KEYCLOAK_GROUP_FIND_ACCESS') or "").split(',') or None
    group_create_access = (os.getenv('KEYCLOAK_GROUP_CREATE_ACCESS') or "").split(',') or None
    group_delete_access = (os.getenv('KEYCLOAK_GROUP_DELETE_ACCESS') or "").split(',') or None
    user_read_access = (os.getenv('KEYCLOAK_USER_READ_ACCESS') or "").split(',') or None
    role_read_access = (os.getenv('KEYCLOAK_ROLE_READ_ACCESS') or "").split(',') or None
    assign_role_group_access = (os.getenv('KEYCLOAK_ASSIGN_ROLE_GROUP_ACCESS') or "").split(',') or None
    join_user_group_access = (os.getenv('KEYCLOAK_JOIN_USER_GROUP_ACCESS') or "").split(',') or None
