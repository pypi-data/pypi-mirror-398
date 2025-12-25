from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsUzbekkomirUser(BaseRolePermissions):
    required_role = 'uzbekkomir'
