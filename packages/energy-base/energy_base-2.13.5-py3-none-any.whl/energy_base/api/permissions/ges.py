from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsGesUser(BaseRolePermissions):
    required_role = 'ges'
