from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsNationalDispatchUser(BaseRolePermissions):
    required_role = 'national-dispatch-center'
