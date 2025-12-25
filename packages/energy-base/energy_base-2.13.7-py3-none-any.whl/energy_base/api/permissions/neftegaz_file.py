from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsNeftegazFileUser(BaseRolePermissions):
    required_role = 'neftegaz-file'
