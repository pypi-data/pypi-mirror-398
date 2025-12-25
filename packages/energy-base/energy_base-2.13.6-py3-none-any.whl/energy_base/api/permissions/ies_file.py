from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsIesFileUser(BaseRolePermissions):
    required_role = 'ies-file'
