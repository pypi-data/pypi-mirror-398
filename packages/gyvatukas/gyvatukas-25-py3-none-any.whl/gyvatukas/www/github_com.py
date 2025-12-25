import logging
import httpx
import diskcache

from gyvatukas.exceptions import GyvatukasException
from gyvatukas.internal import get_app_cache

_logger = logging.getLogger("gyvatukas")
cache = get_app_cache()


class GithubComBase:
    """Base class for GitHub API clients with rate limiting."""

    GITHUB_API_VERSION = "2022-11-28"  # Latest as of 2024-01.
    URL_API_MARKDOWN_CONVERT = "https://api.github.com/markdown"

    @staticmethod
    def _get_api_version_header() -> dict:
        """GitHub wants us to send api version. We comply.

        See: https://docs.github.com/en/rest/about-the-rest-api/api-versions?apiVersion=2022-11-28
        """
        return {
            "X-GitHub-Api-Version": GithubComBase.GITHUB_API_VERSION,
        }

    def _get_base_headers(self) -> dict:
        """Return base headers for GitHub API requests."""
        return {
            "Accept": "application/vnd.github+json",
            **self._get_api_version_header(),
        }

    def _get_auth_headers(self) -> dict:
        """Return auth headers for GitHub API requests. Override in subclasses."""
        return {}

    def convert_md_to_html(self, text: str, fancy_gfm_mode: bool = False) -> str:
        """Convert markdown to HTML using GitHub API.
        Extremely inefficient, but hey, no need to install markdown parsing library and internet is already
        mostly bot traffic anyway.

        See: https://docs.github.com/en/rest/reference/markdown
        """
        response = httpx.post(
            url=self.URL_API_MARKDOWN_CONVERT,
            json={
                "mode": "gfm" if fancy_gfm_mode else "markdown",
                "text": text,
            },
            headers={
                **self._get_base_headers(),
                **self._get_auth_headers(),
            },
            timeout=15,
        )
        if response.status_code == 200:
            return response.text

        _logger.error(
            "Failed to convert markdown to HTML!",
            extra={
                "text": text,
                "fancy_gfm_mode": fancy_gfm_mode,
                "response_status_code": response.status_code,
                "response_text": response.text,
            },
        )
        raise GyvatukasException("Failed to convert markdown to HTML!")


class GithubComNoAuth(GithubComBase):
    """
    Unauthenticated GitHub API client.

    🚨 Rate limited to 60 requests per hour.
    See: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#about-primary-rate-limits
    """

    RATE_LIMIT_PER_SECOND = 60 / 3600  # 60 requests per hour

    def __init__(self):
        super().__init__()

    @diskcache.throttle(cache, 60, 3600, name="github.com (unauthenticated)")
    def convert_md_to_html(self, text: str, fancy_gfm_mode: bool = False) -> str:
        """Rate-limited wrapper for convert_md_to_html."""
        return super().convert_md_to_html(text, fancy_gfm_mode)


class GithubComAuth(GithubComBase):
    """
    Authenticated GitHub API client.

    🚨 Rate limited to 5000 requests per hour.
    See: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#about-primary-rate-limits
    """

    RATE_LIMIT_PER_SECOND = 5000 / 3600  # 5000 requests per hour

    def __init__(self, api_token: str):
        if not api_token:
            raise ValueError("API token is required for authenticated GitHub client")
        self.api_token = api_token
        super().__init__()

    def _get_auth_headers(self) -> dict:
        """Return auth headers for GitHub API."""
        return {
            "Authorization": f"Bearer {self.api_token}",
        }

    @diskcache.throttle(cache, 5000, 3600, name="github.com (authenticated)")
    def convert_md_to_html(self, text: str, fancy_gfm_mode: bool = False) -> str:
        """Rate-limited wrapper for convert_md_to_html."""
        return super().convert_md_to_html(text, fancy_gfm_mode)
