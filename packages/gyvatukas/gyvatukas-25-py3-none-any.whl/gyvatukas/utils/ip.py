"""Bunch of IP related utilities relying on 3rd party."""
import ipaddress
import logging
import random

import httpx

from gyvatukas.utils.decorators import timer

_logger = logging.getLogger("gyvatukas")


@timer()
def get_my_ipv4() -> str:
    """Lookup external ipv4 address. Uses https://ifconfig.me or https://wasab.is or http://checkip.amazonaws.com/.

    🚨 Performs external request.
    """
    # List of IP lookup services with their respective endpoints and response parsing
    ip_services = [
        {"url": "https://wasab.is/json", "parser": lambda data: data["ip"]},
        {"url": "https://ifconfig.me/ip", "parser": lambda data: data.text.strip()},
        {
            "url": "http://checkip.amazonaws.com",
            "parser": lambda data: data.text.strip(),
        },
    ]

    random.shuffle(ip_services)

    for service in ip_services:
        try:
            result = httpx.get(url=service["url"], timeout=5)
            result.raise_for_status()
            ip = service["parser"](result)
            return ip

        except Exception as e:
            _logger.error(f"Error getting ip: {e}")
            continue

    raise RuntimeError("All IP lookup services failed!")


@timer()
def get_ipv4_meta(ip: str) -> dict | None:
    """Lookup ipv4 information. Uses https://wasab.is.

    🚨 Performs external request.
    """
    _logger.debug("performing ipv4 meta lookup for ip `%s`.", ip)
    url = f"https://wasab.is/json?ip={ip}"

    result = httpx.get(url=url, timeout=5)

    if result.status_code == 200:
        result = result.json()
    else:
        result = None

    return result


@timer()
def get_ip_country(ip: str) -> str | None:
    """Get country for given ip address or "Unknown" if not found. Uses https://wasab.is."""
    data = get_ipv4_meta(ip)
    if data is None:
        return None
    return data.get("country", "Unknown")


def ip_to_int(ip: str) -> int:
    return int(ipaddress.IPv4Address(ip))


def int_to_ip(ip_int: int) -> str:
    return str(ipaddress.IPv4Address(ip_int))


if __name__ == "__main__":
    my_ip = get_my_ipv4()
    print(my_ip)
    print(get_ip_country("8.8.8.8"))
