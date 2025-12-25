from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsMetUser(BaseRolePermissions):
    required_role = 'met'
