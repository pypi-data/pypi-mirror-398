from rest_framework import serializers

from energy_base.services.telnet import ConnectionStatus


class ApiStatusSerializer(serializers.Serializer):
    url = serializers.CharField()
    host = serializers.CharField()
    port = serializers.IntegerField()
    status = serializers.ChoiceField(choices=ConnectionStatus.choices)
    error_message = serializers.CharField(required=False, allow_null=True)
