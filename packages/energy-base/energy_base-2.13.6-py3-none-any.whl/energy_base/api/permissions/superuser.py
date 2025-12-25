from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """
    Custom permission to allow access only to superusers.
    """

    def has_permission(self, request, view):
        # Check if the requesting user is a superuser
        return request.user and request.user.is_superuser
