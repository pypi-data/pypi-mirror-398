from collections.abc import Iterable
from copy import deepcopy
from typing import Any

from django.db.models import QuerySet


def deep_map(data: dict | list, func_cond, func_map, in_place=True):
    if not in_place:
        data = deepcopy(data)

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (list, dict, QuerySet)):
                deep_map(value, func_cond, func_map, True)
            elif func_cond(value):
                data[key] = func_map(value)
    elif isinstance(data, (list, QuerySet)):
        for index, value in enumerate(data):
            if isinstance(value, (list, dict, QuerySet)):
                deep_map(value, func_cond, func_map, True)
            elif func_cond(value):
                data[index] = func_map(value)

    return data


def null_to_zero(data: dict | list, in_place=True):
    return deep_map(data, lambda value: value is None, lambda _: 0, in_place)


def deep_round(data: dict | list, ndigits: int, in_place=True):
    return deep_map(data, lambda value: isinstance(value, float), lambda value: round(value, ndigits), in_place)


class EData:
    def __init__(self, data):
        self.data = data

    def null_to_zero(self):
        null_to_zero(self.data)
        return self

    def round(self, ndigits: int):
        deep_round(self.data, ndigits)
        return self

    def map(self, func_cond, func_map):
        deep_map(self.data, func_cond, func_map)
        return self


def key_mapper(obj: dict, key_dict: dict, delete_other=True):
    new_obj = {}
    for old_key, new_key in key_dict.items():
        new_obj[new_key] = obj[old_key]

    if not delete_other:
        for key, value in obj.items():
            if key not in key_dict:
                new_obj[key] = value

    return new_obj


def items_values_list(items: list[dict] | Any, *keys, flat=True):
    values_list = []
    for item in items:
        if len(keys) == 1 and flat:
            values_list.append(item[keys[0]])
        else:
            values_list.append(tuple(item[key] for key in keys))

    return values_list


def to_numeric_or_none(*args):
    _is_iterable = isinstance(args[0], Iterable) and not isinstance(args[0], str)
    if _is_iterable:
        args = args[0]
    result = []

    for x in args:
        if isinstance(x, (int, float, complex, bool)):
            result.append(x)
        else:
            result.append(None)
    if not _is_iterable and len(result) == 1 and len(args) == 1:
        return result[0]
    return result


def safe_sum(*args, allow_null=True):
    args = to_numeric_or_none(*args)

    if all(arg is None for arg in args):
        return None
    if not allow_null and any(arg is None for arg in args):
        return None

    _sum = 0
    for arg in args:
        _sum += arg or 0
    return _sum


def safe_subtract(*args, allow_null=False):
    args = to_numeric_or_none(*args)

    if all(arg is None for arg in args):
        return None
    if not allow_null and any(arg is None for arg in args):
        return None

    _sum = args[0] or 0
    for arg in args[1:]:
        _sum -= arg or 0
    return _sum


def safe_multiply(*args, allow_null=False):
    args = to_numeric_or_none(*args)

    if all(arg is None for arg in args):
        return None
    if not allow_null and any(arg is None for arg in args):
        return None

    result = 1
    for arg in args:
        value = 0 if allow_null and arg is None else arg
        result *= value
    return result


def safe_divide(*args, allow_null=False):
    args = to_numeric_or_none(*args)

    if all(arg is None for arg in args):
        return None
    if not allow_null and any(arg is None for arg in args):
        return None

    result = 0 if allow_null and args[0] is None else args[0]

    for arg in args[1:]:
        value = 0 if allow_null and arg is None else arg
        if value == 0:
            return None
        result /= value

    return result
