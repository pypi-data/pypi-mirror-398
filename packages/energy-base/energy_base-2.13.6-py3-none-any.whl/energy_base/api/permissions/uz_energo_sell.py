from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsUzEnergoSaleUser(BaseRolePermissions):
    required_role = 'uz_energo_sell'
