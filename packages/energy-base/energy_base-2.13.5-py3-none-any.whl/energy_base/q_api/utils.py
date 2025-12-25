def get_full_qualname(obj: object) -> str:
    return obj.__module__ + '.' + obj.__qualname__
