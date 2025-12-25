def is_element_a_list(path, key, value) -> bool:
    """
    A callable that says if a key must be treated as a list.

    This is needed for xmltodict to handle certain keys as lists, as it cannot
    automatically know if they must be converted as lists or as single items
    if the xml has only 1 element.

    This should be derived from the elements themselves by inspecting the tree
    and their attributes, but for now, we hardcode some keys that we know must be lists.
    This function could access the class registry and check if the key is a list in the
    corresponding class definition.
    """
    if key in ["comment", "observation"]:
        # Force these keys to be lists, even if they have a single item.
        return True

    # surface and dirVector are special cases, but only when they are in the definition element.
    return bool("definition" in [p[0] for p in path[-1:-2]] and key in ["surface", "dirVector"])


def remove_null_values(data, remove_none_from_lists=False):
    """
    Recursively removes all null (None) values from a dictionary, including
    nested dictionaries. Optionally removes null values from lists. Also
    removes empty lists from dictionaries.

    Args:
        data: The dictionary or list to process.
        remove_none_from_lists (bool): If True, None values in lists will be removed.

    Returns:
        The dictionary or list with all null values and empty lists removed.
    """
    if isinstance(data, dict):
        # Create a new dictionary to store non-null key-value pairs
        cleaned_data = {}
        for key, value in data.items():
            # Recursively call the function for nested dictionaries and lists
            cleaned_value = remove_null_values(value, remove_none_from_lists)
            # Only add the key-value pair if the value is not None or an empty list
            # This handles cases where a nested structure becomes empty after
            # null removal
            if cleaned_value is not None and cleaned_value != []:
                cleaned_data[key] = cleaned_value
        return (
            cleaned_data if cleaned_data else None
        )  # Return None if dictionary becomes empty after cleaning
    if isinstance(data, list):
        if remove_none_from_lists:
            # Create a new list to store non-null items
            cleaned_list = []
            for item in data:
                # Recursively call the function for nested dictionaries and lists
                cleaned_item = remove_null_values(item, remove_none_from_lists)
                # Only add the item if it's not None (after recursive cleaning)
                if cleaned_item is not None:
                    cleaned_list.append(cleaned_item)
            return (
                cleaned_list if cleaned_list else None
            )  # Return None if list becomes empty after cleaning
        # If not removing None from lists, just clean nested dicts/lists within the list
        cleaned_list = []
        for item in data:
            cleaned_list.append(remove_null_values(item, remove_none_from_lists))
        return cleaned_list
    # For non-dict/list types, return None if the value is None,
    # otherwise return the value itself
    return None if data is None else data
