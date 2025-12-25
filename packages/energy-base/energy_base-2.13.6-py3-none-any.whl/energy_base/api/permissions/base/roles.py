import os

from rest_framework.permissions import IsAuthenticated

from energy_base.utils.microservices import is_internal_microservice_request


class BaseRolePermissions(IsAuthenticated):
    required_role = None
    role_apps = set()

    @classmethod
    def add_role_app(cls, app):
        if 'role_apps' not in cls.__dict__:
            cls.role_apps = set()
        cls.role_apps.add(app)

    def has_permission(self, request, view):
        # Check IsAuthenticated
        if not super().has_permission(request, view):
            return False

        # Give full access for superadmin or admin
        if request.user.is_superuser or 'admin' in request.user.roles:
            return True

        # Give full access for microservice
        if not os.getenv('DONT_CHECK_MICROSERVICE_REQUEST') and is_internal_microservice_request(request):
            return True

        # Check application role access
        app_name = view.__class__.__module__.split('.')[1]
        if self.role_apps and app_name not in self.role_apps:
            return False

        # Check role access
        if hasattr(request.user, 'roles'):
            return self.required_role in request.user.roles

        return False