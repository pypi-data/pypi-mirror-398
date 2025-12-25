import os
import json

import requests
from django.utils.translation import get_language


def translate(key: str) -> str:
    base_url = os.environ.get('TRANSLATION_SERVICE_URL')
    lang = get_language()
    if lang == 'uz-cyr':
        lang = 'crl'
    if lang not in ['uz', 'ru', 'crl']:
        lang = 'ru'
    return requests.get(f'{base_url}/api/translations/{key}', params={
        'lang': lang
    }).text


def translate_month(month: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12):
    return json.loads(translate('primeng.monthNames'))[month - 1]


def translate_weekday(weekday: 1 | 2 | 3 | 4 | 5 | 6 | 7):
    return json.loads(translate('primeng.dayNames'))[weekday % 7]
