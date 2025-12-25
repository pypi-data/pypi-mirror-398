import importlib.metadata
import pathlib
from platformdirs import user_data_dir
import diskcache


def get_gyvatukas_version() -> str:
    """Returns the version of the gyvatukas package (maybe)"""
    meta = importlib.metadata.metadata("gyvatukas")
    if meta:
        try:
            return meta.json["version"]
        except KeyError:
            return "unknown"
    return "unknown"


def get_app_storage_path() -> pathlib.Path:
    path = pathlib.Path(
        user_data_dir(appname="gyvatukas", appauthor="gyvtaukas", ensure_exists=True)
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_app_cache() -> diskcache.Cache:
    path = get_app_storage_path() / "cache"
    return diskcache.Cache(directory=path)
