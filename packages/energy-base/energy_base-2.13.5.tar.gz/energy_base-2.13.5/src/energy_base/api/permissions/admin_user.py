from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsAdminUser(BaseRolePermissions):
    required_role = 'admin'
