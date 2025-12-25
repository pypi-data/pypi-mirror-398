from typing import Any


def dict_remove_matching_values(d: dict, values: list) -> dict:
    """Remove all key-value pairs from dict where value is in values.
    Useful for removing None values from dict or empty strings when working with form data.

    Returns new dict.
    🐌 Creates a new dict, not recommended for large dicts.
    """
    new_d = {}
    for k, v in d.items():
        if v not in values:
            new_d[k] = v

    return new_d


def dict_get_by_path(
    d: dict,
    path: str,
    separator: str = ".",
    allow_none: bool = False,
    default: Any = None,
) -> Any:
    """
    Access a nested value in a dictionary using a string path.
    Less bloated alternative for glom, that just works for this very thing.

    Args:
        d: The dictionary to traverse
        path: String path with parts separated by the separator
        separator: Character that separates parts of the path
        allow_none: If True, return None for invalid paths instead of raising exceptions
        default: Default value to return when path is invalid (overrides allow_none behavior)

    Returns:
        The value at the specified path, the default value if path is invalid and default is set,
        or None if allow_none is True and path is invalid

    Usage:
        >>> data = {"a": {"b": [1, 2, {"c": 3}]}}
        >>> dict_get_by_path(data, "a.b.2.c")
        3
        >>> dict_get_by_path(data, "a.b.2.d", default="not found")
        'not found'
        >>> dict_get_by_path(data, "a.b.2.d", allow_none=True)
        None
    """
    if not path:
        return d

    # Pre-split the path for better performance with longer paths
    parts = path.split(separator)
    current = d

    for part in parts:
        if isinstance(current, dict):
            try:
                current = current[part]
                continue
            except KeyError:
                if default is not None:
                    return default
                if allow_none:
                    return None
                raise

        if isinstance(current, (list, tuple)):
            try:
                idx = int(part)
                try:
                    current = current[idx]
                    continue
                except IndexError:
                    if default is not None:
                        return default
                    if allow_none:
                        return None
                    raise IndexError(f"Index {idx} out of range")
            except ValueError:
                if default is not None:
                    return default
                if allow_none:
                    return None
                raise ValueError(f"'{part}' is not a valid integer index")

        if default is not None:
            return default
        if allow_none:
            return None
        raise TypeError(f"Cannot index into {type(current).__name__} with key '{part}'")

    return current


def dict_flatten(d: dict, parent_key: str = "", separator: str = ".") -> dict:
    if not isinstance(d, dict):
        raise TypeError("Input must be a dictionary")

    items = []

    for key, value in d.items():
        try:
            str_key = str(key)
        except Exception:
            raise TypeError(f"Dictionary key {key!r} cannot be converted to string")

        if separator in str_key:
            raise ValueError(
                f"Dictionary key '{str_key}' cannot contain separator '{separator}'"
            )

        new_key = f"{parent_key}{separator}{str_key}" if parent_key else str_key

        if isinstance(value, dict):
            items.extend(dict_flatten(value, new_key, separator).items())
        elif isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(
                        dict_flatten(
                            item, f"{new_key}{separator}{i}", separator
                        ).items()
                    )
                else:
                    items.append((f"{new_key}{separator}{i}", item))
        else:
            items.append((new_key, value))

    return dict(items)


if __name__ == "__main__":
    d = {"a": {"b": {"c": 123}}, "foo.bar": [1, 2, "something"]}
    print(dict_flatten(d, separator=">"))
