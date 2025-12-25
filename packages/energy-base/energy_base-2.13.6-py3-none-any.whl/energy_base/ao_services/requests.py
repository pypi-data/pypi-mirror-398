import requests
from rest_framework.request import Request

from .constants import AOServices
from .models import AOService


def get(request: Request, ao_service: AOServices, prefix: str, params: any = None):
    headers = {
        'Authorization': request.headers.get('Authorization'),
        'Accept-Language': request.headers.get('Accept-Language'),
    }
    return requests.get(
        url=AOService.get_by_name(ao_service).get_url(prefix),
        params=params,
        headers=headers,
    )


def post(request: Request, ao_service: AOServices, prefix: str, params: any = None, data: any = None):
    headers = {
        'Authorization': request.headers.get('Authorization'),
        'Accept-Language': request.headers.get('Accept-Language'),
    }
    return requests.post(
        url=AOService.get_by_name(ao_service).get_url(prefix),
        params=params,
        headers=headers,
        json=data,
    )
