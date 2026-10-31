import ipaddress
import logging
import os
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv() 

log = logging.getLogger("geo")
TIMEOUT = float(os.getenv("GEO_TIMEOUT_SECONDS", "2"))
GEO_A_URL = os.environ["GEO_A_URL"]   # e.g. http://ip-api.com/json
GEO_B_URL = os.environ["GEO_B_URL"]   # e.g. https://ipapi.co

@dataclass
class Geo:
    country: str | None = None
    city: str | None = None

def _clean(value) -> str | None:
    # return None unless value is a non-empty str; strip it and cut to 100 chars
    if not isinstance(value, str):
        return None

    value = value.strip()

    if value == "":
        return None

    return value[:100]


def lookup_a(ip: str) -> Geo:

    url = f"{GEO_A_URL}/{ip}?fields=status,country,city"

    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.get(url)
        r.raise_for_status()

    j = r.json()

    if j.get("status") != "success":
        raise ValueError("Geo provider A lookup failed")

    return Geo(
        country=_clean(j.get("country")),
        city=_clean(j.get("city"))
    )

def lookup_b(ip: str) -> Geo:
    url = f"{GEO_B_URL}/{ip}/json/"

    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.get(url)
        r.raise_for_status()

    j = r.json()

    if "error" in j:
        raise ValueError("Geo provider B lookup failed")

    return Geo(
        country=_clean(j.get("country_name")),
        city=_clean(j.get("city"))
    )
        


PROVIDERS = [("A", lookup_a), ("B", lookup_b)]

def enrich(ip: str) -> Geo:
  
    try:
        ip_obj = ipaddress.ip_address(ip)
        
    except ValueError:
        return Geo()
    if not ip_obj.is_global:
        return Geo()
    for name,fn in PROVIDERS:
        try:
            result = fn(ip)
        except Exception as e:
            log.warning("geo provider %s failed: %s",name,e)
            continue 
        if result.country or result.city:
            return result
    return Geo()

    