from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsElectricityUser(BaseRolePermissions):
    required_role = 'electricity'
