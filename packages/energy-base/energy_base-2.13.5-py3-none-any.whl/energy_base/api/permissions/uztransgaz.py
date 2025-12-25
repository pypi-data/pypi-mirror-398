from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsUzTransGazUser(BaseRolePermissions):
    required_role = 'uztransgaz'
