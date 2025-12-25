from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsLiquidHydrocarbonsUser(BaseRolePermissions):
    required_role = 'liquidhydrocarbons'
