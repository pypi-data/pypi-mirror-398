import httpx
import diskcache

from gyvatukas.exceptions import GyvatukasException
from gyvatukas.internal import get_app_cache

from pydantic import BaseModel, Field

cache = get_app_cache()


class NtfySHParams(BaseModel):
    # See: https://docs.ntfy.sh/publish/#publish-as-json
    topic: str
    message: str
    title: str | None = None
    tags: list[str] | None = None
    priority: int | None = Field(3, ge=1, le=5)


class NtfySH:
    """ntfy.sh API client.

    🚨 Employs 1 request per second rate limit, as per ntfy.sh policy.
    See: https://docs.ntfy.sh/publish/
    """

    def __init__(self, base_url: str = "https://ntfy.sh/"):
        self.base_url = base_url
        super().__init__()

    def _get_request_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
        }
        return headers

    @diskcache.throttle(cache, 1, 1, name="www.ntfy.sh")
    def post(self, payload: NtfySHParams) -> dict:
        try:
            response = httpx.post(
                self.base_url,
                data=payload.model_dump_json(),
                headers=self._get_request_headers(),
                timeout=10,
            )
        except Exception as e:
            raise GyvatukasException(f"Failed POST'ing to {self.base_url}: {e}")
        if not response.status_code or response.status_code >= 400:
            raise GyvatukasException(
                f"{self.base_url} POST failed with status {response.status_code}: {response.text}"
            )
        try:
            return response.json()
        except Exception:  # noqa: Don't care.
            return {"status_code": response.status_code, "text": response.text}
