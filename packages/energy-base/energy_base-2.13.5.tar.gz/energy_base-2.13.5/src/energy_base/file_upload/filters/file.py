from django_filters import rest_framework as filters

from ..models import ImportFile


class FileFilterSet(filters.FilterSet):
    active = filters.BooleanFilter(field_name='active')
    created_at = filters.DateFilter(lookup_expr='date')

    class Meta:
        model = ImportFile
        fields = ['active', 'created_at']
