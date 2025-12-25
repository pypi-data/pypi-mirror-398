from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsNeftegazNaturalgazUser(BaseRolePermissions):
    required_role = 'neftegaz_naturalgaz'
