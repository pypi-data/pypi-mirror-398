from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsUzTransGazFileUser(BaseRolePermissions):
    required_role = 'uztransgaz-file'
