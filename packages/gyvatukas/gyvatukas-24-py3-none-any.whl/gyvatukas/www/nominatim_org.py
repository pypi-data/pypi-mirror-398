import diskcache
import httpx

from gyvatukas.exceptions import GyvatukasException
from gyvatukas.internal import get_app_cache

cache = get_app_cache()


class NominatimOrg:
    """Nominatim.org API client.

    🚨 Employs 1 request per second rate limit, as per Nominatim.org policy.
    See: https://operations.osmfoundation.org/policies/nominatim/
    """

    def __init__(self, user_agent: str):
        self.user_agent = user_agent
        super().__init__()

    def _get_request_headers(self) -> dict:
        """Return request headers."""
        return {
            "User-Agent": self.user_agent,
        }

    @diskcache.throttle(cache, 1, 1, name="www.nominatim.org")
    def resolve_coords_to_address(self, lat: float, lon: float) -> str:
        """Given lat/lon, return address."""
        response = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "limit": 1,
            },
            headers=self._get_request_headers(),
        )
        data = response.json()
        if not data:
            raise GyvatukasException(
                f"Failed to resolve {lat=} {lon=} to address with http {response.status_code}"
            )
        return data["display_name"]

    @diskcache.throttle(cache, 1, 1, name="www.nominatim.org")
    def resolve_address_to_coords(self, address: str) -> tuple[float, float]:
        """Given address, return coords as lat/lon.

        🚨 Precision required, since will return first match.
        """
        # todo: maybe return dataclass with bbox, formatted addr, etc?
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": address,
                "format": "json",
                "limit": 1,
            },
            headers=self._get_request_headers(),
        )
        data = response.json()
        if not data:
            raise GyvatukasException(
                f"Failed to resolve address `{address}` to coords with http {response.status_code}"
            )
        return data[0]["lat"], data[0]["lon"]


if __name__ == "__main__":
    nom = NominatimOrg(user_agent="gyvatukas library")
    address = "svitrigailos 32, vilnius"
    lat, lon = nom.resolve_address_to_coords(address=address)
    print(f"{address} translated to {lat=} {lon=}")
    address = nom.resolve_coords_to_address(lat=lat, lon=lon)
    print(f"{lat=} {lon=} translated to {address=}")
