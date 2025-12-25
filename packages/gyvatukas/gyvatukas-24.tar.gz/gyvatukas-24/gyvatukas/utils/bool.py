from typing import Any, Union

TRUE_VALUES: set[str] = {"true", "1", "yes", "y", "on", "t"}
FALSE_VALUES: set[str] = {"false", "0", "no", "n", "off", "f"}


def is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.lower().strip() in TRUE_VALUES
    return bool(value)


def is_false(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value.lower().strip() in FALSE_VALUES
    return not bool(value)


def value_to_bool(value: Any) -> Union[bool, None]:
    if is_true(value):
        return True
    if is_false(value):
        return False
    return None
