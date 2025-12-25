from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsGasUser(BaseRolePermissions):
    required_role = 'gas'
