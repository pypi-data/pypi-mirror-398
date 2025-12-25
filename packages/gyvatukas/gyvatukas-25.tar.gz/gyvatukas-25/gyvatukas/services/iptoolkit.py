import csv
import gzip
import logging
import pathlib
import tempfile

import httpx

from gyvatukas.internal import get_app_storage_path
from gyvatukas.utils.dict_ import dict_get_by_path
from gyvatukas.utils.ip import ip_to_int
from gyvatukas.utils.sql import get_conn_cur

logger = logging.getLogger("gyvatukas.iptoolkit")


class IpToolKit:
    """Simple ip to country lookup tool based on free ip databases.

    - If provider config is not passed, only db-ip.com database will be used.
    - Currently supported providers: db-ip.com, ipinfo.io.
    - Do not forget to run setup_db() when changing provider config to get new data.

    Provider configuration:
    # TODO: Document ant validate. If key matches, validate that all info passed.
    {
        "ipinfo.io": {
            "token": "<your_token>",
        }
    }

    """

    DB_SCHEMA = """
        CREATE TABLE IF NOT EXISTS ip_to_country (
            ipf INTEGER,
            ipt INTEGER,
            cc CHAR(2),
            provider TEXT
        );
        CREATE INDEX IF NOT EXISTS ip_to_country_idx ON ip_to_country (ipf, ipt);
    """

    def __init__(
        self, provider_config: dict | None = None, db_path: pathlib.Path | None = None
    ):
        self.provider_config = provider_config or {}
        self.path_db = db_path or get_app_storage_path() / "iptoolkit.db"

        if not self.db_exists():
            logger.warning("IpToolKit database not found, setting up...")
            self.setup_db()

    def db_exists(self) -> bool:
        return self.path_db.exists()

    def _insert_into_db(self, entries: list[dict]) -> None:
        with get_conn_cur(self.path_db) as (conn, cur):
            conn.executescript(self.DB_SCHEMA)

            # Drop existing provider data.
            conn.execute(
                "DELETE FROM ip_to_country WHERE provider = :provider",
                {"provider": entries[0]["provider"]},
            )

            conn.executemany(
                "INSERT INTO ip_to_country(ipf, ipt, cc, provider) VALUES (:ipf, :ipt, :cc, :provider)",
                entries,
            )
            conn.commit()

    def _setup_dbipcom(self) -> None:
        logger.info("Setting up db-ip.com database.")

        url = "https://download.db-ip.com/free/dbip-country-lite-2024-12.csv.gz"
        entries: list[dict] = []

        with (
            tempfile.TemporaryDirectory() as temp_dir,
        ):
            gz_path = pathlib.Path(temp_dir) / "data.csv.gz"

            # Download the file
            response = httpx.get(url)

            if response.status_code != 200:
                logger.warning(
                    f"Could not download db-ip.com database @ {url} with http {response.status_code}, please investigate."
                )
                return

            with open(gz_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

            # Read and yield rows directly from gz file
            with gzip.open(gz_path, "rt", encoding="utf-8") as gz_file:
                reader = csv.DictReader(gz_file)

                for row in reader:
                    try:
                        entries.append(
                            {
                                "ipf": ip_to_int(row["0.0.0.0"]),
                                "ipt": ip_to_int(row["0.255.255.255"]),
                                "cc": row["ZZ"],
                                "provider": "db-ip.com",
                            }
                        )
                    except Exception:
                        pass

        self._insert_into_db(entries)

    def _setup_ipinfoio(self) -> None:
        logger.info("Setting up ipinfo.io database.")

        token = dict_get_by_path(self.provider_config, "ipinfo.io/token", "/")
        if not token:
            logger.warning("Cannot setup ipinfo.io database, token is not in config.")
            return

        url = "https://ipinfo.io/data/free/country.csv.gz?token={token}".format(
            token=token
        )
        entries: list[dict] = []

        with (
            tempfile.TemporaryDirectory() as temp_dir,
        ):
            gz_path = pathlib.Path(temp_dir) / "data.csv.gz"

            # Download the file
            response = httpx.get(url)
            if response.status_code not in [200, 302]:
                logger.warning(
                    f"Could not download ipinfo.io database @ {url} with http {response.status_code}, please investigate."
                )
                return

            # If 302, extract download url.
            if response.status_code == 302:
                url = response.headers["Location"]
                response = httpx.get(url)
                if response.status_code != 200:
                    logger.warning(
                        f"Could not download ipinfo.io database @ {url} with http {response.status_code}, please investigate."
                    )
                    return

            with open(gz_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

            # Read and yield rows directly from gz file
            with gzip.open(gz_path, "rt", encoding="utf-8") as gz_file:
                reader = csv.DictReader(gz_file)

                for row in reader:
                    try:
                        entries.append(
                            {
                                "ipf": ip_to_int(row["start_ip"]),
                                "ipt": ip_to_int(row["end_ip"]),
                                "cc": row["country"],
                                "provider": "ipinfo.io",
                            }
                        )
                    except Exception:
                        pass

        self._insert_into_db(entries)

    def setup_db(self) -> None:
        # Always setup db-ip.com since their db is free and no signup required.
        if "ipinfo.io" in self.provider_config:
            self._setup_ipinfoio()

        self._setup_dbipcom()

    def get_country_by_ipv4(self, ipv4: str) -> str | None:
        """Given ipv4 address, return best matched country code or None."""
        # todo: Validate IP4.
        ip_int = ip_to_int(ipv4)
        with get_conn_cur(self.path_db) as (conn, cur):
            cur.execute(
                "SELECT cc, COUNT(*) as count FROM ip_to_country WHERE ipf <= :ipf AND ipt >= :ipt GROUP BY cc ORDER BY count DESC LIMIT 1",
                {"ipf": ip_int, "ipt": ip_int},
            )
            result = cur.fetchone()
            return result["cc"] if result else None


if __name__ == "__main__":
    iptk = IpToolKit()
    print(iptk.get_country_by_ipv4("8.8.8.8"))

"""
Rewrite current logic to use class based approach
Each provider is a class.

Here is napkin "code":

IpToolKit
 init(config: dict, base_dir: pathlib.Path)
   create provider instances based on config, call their setup methods.
 get_country_by_ipv4(ipv4: str) -> str | None
   add lru cache
 get_stats() -> dict
   total rows, rows per provider

 AbstractProvider
  init(config: dict, base_dir: pathlib.Path)

  _current_db_is_up_to_date() -> bool
    check if downloaded db is up to date (scraping i guess)

  _download_db() -> None
    download db from provider.

  _insert_into_db(entries: list[dict]) -> None
    insert into db, should work with same data format so that can be implemented in abstract class.

  setup()
    check if db is up to date.
    download db if needed.
    insert into db.

  get_stats() -> dict
    path to downloaded data, is_latest...?
 

 provider classes to setup: db-ip.com, ipinfo.io, ip2location.com, maxmind.com
 For now do not implement their methods, just create classes and methods that raise not implemented error.

"""
