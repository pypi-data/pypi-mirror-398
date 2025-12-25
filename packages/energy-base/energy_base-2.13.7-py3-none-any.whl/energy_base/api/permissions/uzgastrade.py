from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsUzGasTradeUser(BaseRolePermissions):
    required_role = 'uzgastrade'
