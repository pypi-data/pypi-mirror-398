import json
import os
from typing import Union

SUPPORTED_ENV_TYPES: set = {str, int, float, bool, list, dict}


def get_env(
    name: str,
    type: SUPPORTED_ENV_TYPES,
    default: SUPPORTED_ENV_TYPES = None,
    required: bool = False,
) -> SUPPORTED_ENV_TYPES:
    """Try to parse environment variable as given type.

    🚩 Does not load environment variables. Use `python-dotenv` for that.

    type: Output type, will split "a,b,c" into ["a", "b", "c"] if type=list.
    default: Default value if given name does not exist in environ
    required: Fail if not found in environment? Useful for things like database port :)
    """
    truthy = ("true", "1", "yes")
    falsy = ("false", "0", "no")
    value: Union[None, str] = os.getenv(name, None)

    if value is None or value == "":
        if required:
            raise ValueError(
                f"Value `{value}` is required but not found in environment!"
            )
        return default

    if type == bool:
        if value.lower() not in truthy + falsy:
            raise ValueError(
                f"Invalid value `{value}` for variable `{name}`. Cannot be parsed as bool..."
            )
        return value in truthy

    if type == list:
        return value.split(",")

    if type == int:
        return int(value)

    if type == float:
        return float(value)

    if type == dict:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ValueError(
                f"Invalid value `{value}` for variable `{name}`. Cannot be parsed as dict..."
            )

    return str(value)
