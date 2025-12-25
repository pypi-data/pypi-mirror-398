import httpx
import diskcache

from gyvatukas.internal import get_app_cache

cache = get_app_cache()


class PowerHitRadioLt:
    URL_CURRENTLY_PLAYING = "https://powerhitradio.tv3.lt/Pwr/lastSong"

    @diskcache.throttle(cache, 1, 1, name="www.powerhitradio.lt")
    def get_currently_playing(self) -> dict:
        """Get currently playing song from Power Hit Radio LT.

        Returns parsed result, original response is stored in `_raw` key.
        """
        response = httpx.get(url=self.URL_CURRENTLY_PLAYING)
        data = response.json()
        return data


if __name__ == "__main__":
    phr = PowerHitRadioLt()
    print(phr.get_currently_playing())
