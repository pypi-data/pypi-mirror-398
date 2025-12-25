from django.utils import timezone
from django.utils.translation import activate, get_language
from rest_framework.request import Request
from rest_framework.views import APIView

from energy_base.models import JWTUser


AVAILABLE_LANGUAGES = ['uz', 'ru', 'crl']


class BaseRequest(Request):

    @property
    def user(self) -> JWTUser:
        return super(BaseRequest, self).user()


class BaseAPIView(APIView):
    user_id_assign_fields_on_create = []
    user_id_assign_fields_on_update = []
    user_id_assign_fields_on_delete = []
    deleted_at_field = None

    def __init__(self, **kwargs):
        # Check user_id_assign_fields_on_create
        assert isinstance(self.user_id_assign_fields_on_create, list), (
            'Expected iterable user_id_assign_fields_on_create field'
        )

        # Check user_id_assign_fields_on_update
        assert isinstance(self.user_id_assign_fields_on_update, list), (
            'Expected iterable user_id_assign_fields_on_update field'
        )

        # Check user_id_assign_fields_on_delete
        assert isinstance(self.user_id_assign_fields_on_delete, list), (
            'Expected iterable user_id_assign_fields_on_delete field'
        )

        # Check deleted_at_field
        assert isinstance(self.deleted_at_field, (str, type(None))), (
            'Expected str | None deleted_at_field field'
        )
        super().__init__(**kwargs)
        self.request: BaseRequest | None = None

    def perform_create(self, serializer):
        kws = {}
        for attr in getattr(self, 'user_id_assign_fields_on_create', []):
            kws[attr] = self.request.user.id
        serializer.save(**kws)

    def perform_update(self, serializer):
        kws = {}
        for attr in getattr(self, 'user_id_assign_fields_on_update', []):
            kws[attr] = self.request.user.id
        serializer.save(**kws)

    def perform_destroy(self, instance):
        for attr in getattr(self, 'user_id_assign_fields_on_delete', []):
            setattr(instance, attr, self.request.user.id)
        if self.deleted_at_field and hasattr(instance, self.deleted_at_field):
            setattr(instance, self.deleted_at_field, timezone.now())
        instance.save()

    def update_lang(self):
        activate(self.get_language())

    def get_language(self):
        if lang_from_header := self.request.headers.get('accept-language'):
            if lang_from_header and lang_from_header not in AVAILABLE_LANGUAGES:
                lang_from_header = 'ru'

        return lang_from_header or get_language()
