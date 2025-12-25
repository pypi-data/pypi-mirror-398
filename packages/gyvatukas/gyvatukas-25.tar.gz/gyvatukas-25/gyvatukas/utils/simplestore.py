from abc import ABC, abstractmethod
from pathlib import Path
import json
import pickle
import base64
from typing import Optional
import logging
from decimal import Decimal

_logger = logging.getLogger("gyvatukas")


class KeyValueStore(ABC):
    @abstractmethod
    def set(self, key: str, value: any, override: bool = False) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> any:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def pop(self, key: str) -> any:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def keys(self) -> list[str]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class DirStore(KeyValueStore):
    """
    Simple key-value store that stores data in a directory.
    Modern unix systems can have hundreds of millions of files in a single directory.

    Data is stored in two files:
    - <key>.data: data file
    - <key>.meta: metadata file

    Data is serialized to json or pickle. Deserialization is done based on metadata.

    Usage:
        >>> store = DirStore(base_dir=Path("someplace"))
        >>> store.set("key", "value", override=True)
        >>> value = store.get("key")
        >>> print(value)
        >>> store.delete("key")
        >>> value = store.pop("key")
        >>> print(value)
        >>> exists = store.exists("key")
        >>> print(f"exists? {exists}")
        >>> all_keys = store.keys()
        >>> print(len(all_keys))
        >>> store.clear()
    """

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(exist_ok=True)

    def _safe_filename(self, key: str) -> str:
        if not key or not key.strip():
            raise ValueError("Key cannot be empty or only whitespace")

        safe = key.replace("/", "_").replace("\\", "_").replace(":", "_")
        safe = "".join(c for c in safe if c.isalnum() or c in "._-")

        if not safe:
            raise ValueError(f"Key `{key}` cannot be converted to safe filename")

        return safe

    def _get_file_paths(self, key: str) -> tuple[Path, Path]:
        safe_key = self._safe_filename(key)
        data_file = self.base_dir / f"{safe_key}.data"
        meta_file = self.base_dir / f"{safe_key}.meta"
        return data_file, meta_file

    def set(self, key: str, value: any, override: bool = False) -> None:
        if not override and self.exists(key):
            raise ValueError(
                f"Key `{key}` already exists. Use override=True to overwrite."
            )

        data_file, meta_file = self._get_file_paths(key)

        metadata = {"type": type(value).__name__, "encoding": "json"}

        try:
            serialized_data = self._serialize_for_json(value)
            metadata["encoding"] = "json"

            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(serialized_data, f, indent=2, ensure_ascii=False)

        except (TypeError, ValueError):
            metadata["encoding"] = "pickle"

            with open(data_file, "wb") as f:
                pickle.dump(value, f)

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def get(self, key: str) -> any:
        data_file, meta_file = self._get_file_paths(key)

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            if metadata["encoding"] == "json":
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return self._deserialize_from_json(data, metadata["type"])

            elif metadata["encoding"] == "pickle":
                with open(data_file, "rb") as f:
                    return pickle.load(f)

            else:
                raise ValueError(f"Unknown encoding: {metadata['encoding']}")

        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, pickle.PickleError, KeyError) as e:
            _logger.error(f"Could not read file @ {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        data_file, meta_file = self._get_file_paths(key)
        deleted = False

        try:
            data_file.unlink()
            deleted = True
        except FileNotFoundError:
            pass

        try:
            meta_file.unlink()
            deleted = True
        except FileNotFoundError:
            pass

        return deleted

    def pop(self, key: str) -> any:
        value = self.get(key)
        if value is not None:
            self.delete(key)
        return value

    def exists(self, key: str) -> bool:
        data_file, meta_file = self._get_file_paths(key)
        return data_file.exists() and meta_file.exists()

    def keys(self) -> list[str]:
        keys = []
        for meta_file in self.base_dir.glob("*.meta"):
            key = meta_file.stem
            keys.append(key)
        return keys

    def clear(self) -> None:
        for file_path in self.base_dir.glob("*.data"):
            file_path.unlink()
        for file_path in self.base_dir.glob("*.meta"):
            file_path.unlink()

    def get_info(self, key: str) -> Optional[dict]:
        data_file, meta_file = self._get_file_paths(key)

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            if data_file.exists():
                metadata["size_bytes"] = data_file.stat().st_size

            return metadata
        except FileNotFoundError:
            return None

    def _serialize_for_json(self, value: any) -> any:
        value_type = type(value).__name__

        if value_type in ("set", "frozenset"):
            return list(value)
        elif value_type == "tuple":
            return list(value)
        elif value_type == "bytes":
            return base64.b64encode(value).decode("ascii")
        elif value_type == "Decimal":
            return str(value)
        elif hasattr(value, "isoformat"):
            return value.isoformat()
        else:
            json.dumps(value)
            return value

    def _deserialize_from_json(self, data: any, original_type: str) -> any:
        if original_type == "set":
            return set(data)
        elif original_type == "frozenset":
            return frozenset(data)
        elif original_type == "tuple":
            return tuple(data)
        elif original_type == "bytes":
            return base64.b64decode(data.encode("ascii"))
        elif original_type == "Decimal":
            return Decimal(data)
        elif original_type in ("date", "datetime", "time"):
            from datetime import datetime, date, time

            if original_type == "datetime":
                return datetime.fromisoformat(data)
            elif original_type == "date":
                return date.fromisoformat(data)
            elif original_type == "time":
                return time.fromisoformat(data)
        else:
            return data


if __name__ == "__main__":
    store: KeyValueStore = DirStore("my_scripts")

    store.set("script1", "print('hello world')")
    store.set("config", {"debug": True, "port": 8080})
    store.set("numbers", [1, 2, 3, 4, 5])
    store.set("coordinates", (10, 20))
    store.set("tags", {"python", "script", "storage"})
    store.set("binary_data", b"hello world")

    store.set("price", Decimal("19.99"))

    from datetime import datetime

    store.set("timestamp", datetime.now())

    try:
        store.set("script1", "new script")
    except ValueError as e:
        print(f"Expected error: {e}")

    store.set("script1", "new script", override=True)

    popped_value = store.pop("coordinates")
    print(f"Popped: {popped_value}")
    print(f"Coordinates exists: {store.exists('coordinates')}")

    print("Script:", store.get("script1"))
    print("Config:", store.get("config"))
    print("Price:", store.get("price"), type(store.get("price")))
    print("Timestamp:", store.get("timestamp"), type(store.get("timestamp")))
    print("Tags:", store.get("tags"), type(store.get("tags")))
    print("Binary:", store.get("binary_data"), type(store.get("binary_data")))

    print("Keys:", store.keys())
