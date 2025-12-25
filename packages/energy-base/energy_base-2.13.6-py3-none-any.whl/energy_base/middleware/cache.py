from django.middleware.cache import UpdateCacheMiddleware, FetchFromCacheMiddleware


class CachePermissionMixin:
    # noinspection PyMethodMayBeStatic
    def should_cache(self, request):
        user = request.user
        if not user.is_authenticated:
            return True
        if hasattr(user, 'should_cache_requests') and not user.should_cache_requests:
            return False
        return True


class EnergyBaseUpdateCacheMiddleware(CachePermissionMixin, UpdateCacheMiddleware):
    def process_response(self, request, response):
        if not self.should_cache(request):
            return response
        return super().process_response(request, response)


class EnergyBaseFetchFromCacheMiddleware(CachePermissionMixin, FetchFromCacheMiddleware):
    def process_request(self, request):
        if not self.should_cache(request):
            return None
        return super().process_request(request)
