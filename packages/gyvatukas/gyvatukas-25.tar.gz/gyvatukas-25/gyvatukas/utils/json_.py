import json
import logging
from typing import Any
import pathlib
import decimal
import datetime

from gyvatukas.utils.fs import read_file, write_file

_logger = logging.getLogger("gyvatukas")


def _convert_key_to_str(key):
    """Convert a key to string, handling special types consistently with EnhancedJSONEncoder."""
    if isinstance(key, (datetime.datetime, datetime.date)):
        return key.isoformat()
    elif isinstance(key, decimal.Decimal):
        return str(key)
    elif isinstance(key, pathlib.Path):
        return str(key)
    else:
        return str(key)


def _convert_keys_to_str(obj):
    if isinstance(obj, dict):
        return {_convert_key_to_str(k): _convert_keys_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_keys_to_str(i) for i in obj]
    else:
        return obj


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, pathlib.Path):
            return str(obj)
        return super().default(obj)


def json_dumps_safe(obj, **kwargs) -> str:
    """json.dumps with encoder that 'fixes' the common annoyance of getting exceptions when
    dict contains datetime or decimal."""
    obj = _convert_keys_to_str(obj)
    return json.dumps(obj, cls=EnhancedJSONEncoder, **kwargs)


def get_pretty_json(data: dict | list) -> str:
    """Return pretty json string."""
    result = json.dumps(data, indent=4, default=str, ensure_ascii=False)
    return result


def read_json(path: pathlib.Path, default: Any | None = None) -> dict | list:
    """Read JSON from file. Return empty dict if file not found or JSON is invalid."""
    data = read_file(path=path)
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            pass
    if default is not None:
        return default
    return {}


def write_json(
    path: pathlib.Path, data: dict | list, pretty: bool = False, override: bool = False
) -> bool:
    """Write JSON to file. Return true if written, false if not."""
    if pretty:
        content = json_dumps_safe(data, indent=4, ensure_ascii=False)
    else:
        content = json_dumps_safe(data)

    result = write_file(path=path, content=content, override=override)
    return result
