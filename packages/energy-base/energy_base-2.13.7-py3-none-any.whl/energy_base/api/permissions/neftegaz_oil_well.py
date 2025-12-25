from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsOilWellUser(BaseRolePermissions):
    required_role = 'oil_well'
