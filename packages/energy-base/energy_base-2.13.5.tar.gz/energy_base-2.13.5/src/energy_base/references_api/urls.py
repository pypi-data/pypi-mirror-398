from .utils import get_model_classes, create_view_set, get_basename, get_url_prefix
from ..api.routers import OptionalSlashRouter

router = OptionalSlashRouter()

for model_class in get_model_classes():
    router.register(
        prefix=get_url_prefix(model_class),
        viewset=create_view_set(model_class),
        basename=get_basename(model_class)
    )

urlpatterns = router.urls
