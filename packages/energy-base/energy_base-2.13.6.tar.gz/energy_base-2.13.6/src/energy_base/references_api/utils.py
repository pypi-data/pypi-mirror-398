import importlib
from urllib.parse import urlparse

import inflect
from django.conf import settings
from django.db.models import Model, CharField
from drf_spectacular.utils import extend_schema, extend_schema_serializer
from rest_framework import filters
from rest_framework import viewsets, serializers

from ..api.views import TranslatedListView

serializer_classes = {}


def find_model(model_name: str):
    for model_class in get_model_classes():
        if get_model_class_name(model_class).lower() == model_name.lower():
            return model_class


def get_api_meta_property(model: Model, property_name: str):
    if hasattr(model, 'ApiMeta'):
        if hasattr(model.ApiMeta, property_name):
            return getattr(model.ApiMeta, property_name)


def get_model_class_name(model: Model):
    return model._meta.object_name


def get_model_fields_list(model: Model):
    return model._meta.get_fields()


def get_view_set_name(model: Model):
    return get_model_class_name(model) + 'ViewSet'


def get_basename(model: Model):
    return 'admin-' + get_plural_form(get_model_class_name(model).lower())


def camel_to_snake(name: str):
    return ''.join(map(lambda c: '-' + c.lower() if c.isupper() else c, name)).removeprefix('-')


def get_url_prefix(model: Model):
    return 'admin/' + get_plural_form(camel_to_snake(get_model_class_name(model))).replace(' ', '-')


def get_plural_form(word: str):
    p = inflect.engine()
    return p.plural(word)


def get_serializer_name(model: Model):
    return get_model_class_name(model) + 'Serializer'


def get_ordering(model: Model):
    if model._meta.ordering:
        return model._meta.ordering
    if hasattr(model, 'created_at'):
        return ('-created_at',)
    if hasattr(model, 'id'):
        return ('id',)
    return ()


def get_model_classes():
    model_classes = []
    for model_import_path in settings.REFERENCE_API_MODELS:
        module_name, class_name = model_import_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        model_classes.append(getattr(module, class_name))

    return model_classes


def create_view_set(model: Model):
    fields_list = get_model_fields_list(model)

    @extend_schema(tags=[get_url_prefix(model)])
    class ViewSet(viewsets.ModelViewSet, TranslatedListView):
        http_method_names = get_api_meta_property(model, 'http_method_names') or ['get', 'patch']
        manager = model.objects.order_by(*get_ordering(model))
        filter_backends = [filters.SearchFilter]
        search_fields = (get_api_meta_property(model, 'search_fields') or
                         [field.name for field in fields_list if isinstance(field, CharField)])

        def get_serializer_class(self):
            if self.action == 'create':
                return create_serializer_for_create(model)

            if self.action == 'partial_update':
                return create_serializer_for_partial_update(model)

            return create_serializer(model)

    return ViewSet


def create_serializer_for_create(model: Model):
    @extend_schema_serializer(component_name='Admin' + get_serializer_name(model))
    class Serializer(serializers.ModelSerializer):
        class Meta:
            fields = '__all__'

    Serializer.Meta.model = model
    return Serializer


def create_serializer_for_partial_update(model: Model):
    fields_list = get_model_fields_list(model)

    @extend_schema_serializer(component_name='Admin' + get_serializer_name(model))
    class Serializer(serializers.ModelSerializer):
        class Meta:
            fields = '__all__'
            read_only_fields = list(
                {
                    'created_at',
                    'updated_at',
                    'deleted_at',
                    'created_by',
                    'updated_by',
                    'deleted_by',
                    'code'
                } & set([field.name for field in fields_list])
            )

    Serializer.Meta.model = model
    return Serializer


def create_serializer(model: Model, depth=0):
    if get_model_class_name(model) in serializer_classes:
        return serializer_classes[get_model_class_name(model)]

    fields_list = get_model_fields_list(model)

    class ImageNameField(serializers.ImageField):
        def to_representation(self, value):
            if not value:
                return None
            parsed_url = urlparse(value.url)
            return f'{parsed_url.path}?{parsed_url.query}'

    @extend_schema_serializer(component_name='Admin' + get_serializer_name(model))
    class Serializer(serializers.ModelSerializer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            nonlocal model, fields_list
            for field in fields_list:
                if field.__class__.__name__.endswith('ImageField') or field.__class__.__name__.endswith('FileField'):
                    self.fields[field.name] = ImageNameField()

                if field.__class__.__name__.endswith('ForeignKey'):
                    model_name = field.name
                    _model = find_model(model_name)
                    if _model is not None and depth == 0:
                        self.fields[model_name] = create_serializer(_model, depth + 1)()

        class Meta:
            fields = '__all__'
            read_only_fields = list(
                {
                    'created_at',
                    'updated_at',
                    'deleted_at',
                    'created_by',
                    'updated_by',
                    'deleted_by',
                    'code'
                } & set([field.name for field in fields_list])
            )

    Serializer.Meta.model = model
    serializer_classes[get_model_class_name(model)] = Serializer
    return Serializer
