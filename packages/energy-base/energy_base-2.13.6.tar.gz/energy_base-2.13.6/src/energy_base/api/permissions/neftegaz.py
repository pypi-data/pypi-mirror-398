from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsNeftegazUser(BaseRolePermissions):
    required_role = 'neftegaz'
