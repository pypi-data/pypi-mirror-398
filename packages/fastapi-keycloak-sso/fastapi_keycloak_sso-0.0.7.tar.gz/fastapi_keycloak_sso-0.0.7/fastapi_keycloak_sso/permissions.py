from .initializer import KeyCloakInitializer
from fastapi import HTTPException, status


class GroupAccess(KeyCloakInitializer):
    """
    You can check if a user has the allowed group by sending the name of the desired group and
    user and setting the admin group in .env.
    """

    def require_all_groups(self, user , groups_name: list):
        groups_list = user.groups
        admin_groups = self.admin_groups.split(',')

        if (not any(admin in groups_list for admin in admin_groups) and
            not all(item in groups_list for item in groups_name)):
            raise HTTPException(
                detail='You are not allowed to access this API',
                status_code=status.HTTP_403_FORBIDDEN
            )
        return True

    def require_any_groups(self, user, groups_names: list):
        groups_list = user.groups
        admin_groups = self.admin_groups.split(',')

        if not (
                any(admin in groups_list for admin in admin_groups)
                or any(item in groups_list for item in groups_names)
        ):
            raise HTTPException(
                detail='You are not allowed to access this API',
                status_code=status.HTTP_403_FORBIDDEN
            )
        return True
