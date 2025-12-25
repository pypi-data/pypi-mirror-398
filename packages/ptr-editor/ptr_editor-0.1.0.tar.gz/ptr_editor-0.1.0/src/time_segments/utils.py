from typing import Any


def _flatten_nested_dictionary_dotted(
    d: dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> dict[str, Any]:
    """Flatten a nested dictionary with dotted keys, including lists and tuples."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_nested_dictionary_dotted(v, new_key, sep=sep).items())
        elif isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                indexed_key = f"{new_key}[{i}]"
                if isinstance(item, dict):
                    items.extend(_flatten_nested_dictionary_dotted(item, indexed_key, sep=sep).items())
                elif isinstance(item, (list, tuple)):
                    # Recursively handle nested lists/tuples
                    nested_dict = {f"[{j}]": nested_item for j, nested_item in enumerate(item)}
                    items.extend(_flatten_nested_dictionary_dotted(nested_dict, indexed_key, sep=sep).items())
                else:
                    items.append((indexed_key, item))
        else:
            items.append((new_key, v))
    return dict(items)
