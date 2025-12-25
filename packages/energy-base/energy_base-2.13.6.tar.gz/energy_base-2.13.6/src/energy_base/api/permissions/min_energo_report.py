from energy_base.api.permissions.base.roles import BaseRolePermissions


class IsMinEnergoReportUser(BaseRolePermissions):
    required_role = 'min-energo-report'