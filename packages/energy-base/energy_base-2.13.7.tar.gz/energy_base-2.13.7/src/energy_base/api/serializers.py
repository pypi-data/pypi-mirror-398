from django.utils import translation
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from energy_base.translation import translate as _


class DashboardDateSerializer(serializers.Serializer):
    datetime = serializers.DateTimeField()
    period = serializers.ChoiceField(choices=['daily', 'hourly'], default='daily')


class DashboardSerializer(serializers.Serializer):
    datetime = serializers.DateTimeField(required=False)
    period = serializers.ChoiceField(choices=['hourly', 'today', 'daily', 'monthly', 'yearly'], default='daily')

    def validate(self, attrs):
        period = attrs.get('period', 'daily')
        datetime = attrs.get('datetime')

        if period != 'today' and datetime is None:
            raise ValidationError({
                'datetime': _('This field is required when period is not "today".')
            })
        return attrs


class TranslatedField(serializers.CharField):
    _AVAILABLE_LANGUAGES = ['uz', 'ru', 'crl']

    def get_language(self):
        if lang_from_header := self.context['request'].headers.get('accept-language'):
            if lang_from_header and lang_from_header not in self._AVAILABLE_LANGUAGES:
                lang_from_header = 'ru'

        return lang_from_header or translation.get_language()

    def get_attribute(self, instance):
        field_name = self.source or self.field_name

        lang = self.get_language()
        translated_field = f"{field_name}_{lang}"

        if hasattr(instance, translated_field):
            return getattr(instance, translated_field)

        return getattr(instance, field_name, None)
