from django_filters import rest_framework as filters


class TaskFilterSet(filters.FilterSet):
    success = filters.BooleanFilter()
