from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsIesUser(BaseRolePermissions):
    required_role = 'ies'
