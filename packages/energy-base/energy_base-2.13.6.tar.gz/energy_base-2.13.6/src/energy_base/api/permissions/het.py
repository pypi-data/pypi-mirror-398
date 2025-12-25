from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsHetUser(BaseRolePermissions):
    required_role = 'het'
