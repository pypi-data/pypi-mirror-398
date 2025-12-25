import os

from django.utils.deprecation import MiddlewareMixin


class DebugOverrideMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if request.headers.get("X-Debug-Token") == os.environ.get("DJANGO_SECRET_KEY"):
            from django.views import debug
            return debug.technical_500_response(request, type(exception), exception, exception.__traceback__)
