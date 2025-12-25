from django.http import HttpRequest
from rest_framework.request import Request


def is_internal_microservice_request(request: HttpRequest | Request):
    # check request sending from gateway, if so it is not internal
    return 'HTTP_X_FORWARDED_PREFIX' not in request.META
