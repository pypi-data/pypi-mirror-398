from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsSmartIntegrityUser(BaseRolePermissions):
    required_role = 'smart_integrity'
