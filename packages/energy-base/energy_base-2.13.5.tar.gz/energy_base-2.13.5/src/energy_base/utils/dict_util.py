def get_by_dotted(dict_obj: dict, dotted_key: str, default=None):
    """
    Get a value from a dictionary using a dotted key notation.

    Args:
        dict_obj (dict): The dictionary to retrieve the value from.
        dotted_key (str): The dotted key notation to access nested keys.
        default: The default value to return if the key is not found.

    Returns:
        The value at the given dotted key, or default if not found.
    """
    parts = dotted_key.split('.')
    for part in parts:
        # Check if current part is in the dictionary and is a dictionary itself
        if isinstance(dict_obj, dict) and part in dict_obj:
            dict_obj = dict_obj.get(part, default)
        else:
            return default
    return dict_obj
