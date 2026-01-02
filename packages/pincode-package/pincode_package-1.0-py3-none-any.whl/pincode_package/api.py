import logging
import time
import asyncio
import requests
import httpx

from requests.exceptions import RequestException

from .cache import get_cached_pincode, save_cached_pincode
from .exceptions import (
    APIUnavailableError,
    PincodeNotFoundError,
    PostOfficeNotFoundError
)

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "pincode-package/1.0 (contact: kssreelakshmi2211@gmail.com)"
}

BASE_PINCODE_URL = "https://api.postalpincode.in/pincode/"
BASE_POSTOFFICE_URL = "https://api.postalpincode.in/postoffice/"


# -------------------------------------------------------------------
# Retry helpers
# -------------------------------------------------------------------

def _retry_request(func, retries=3, backoff=1):
    """
    Retry a synchronous request with exponential backoff.
    """
    for attempt in range(retries):
        result = func()
        if result:
            return result
        sleep_time = backoff * (2 ** attempt)
        logger.warning(
            "Retry %s/%s after %ss", attempt + 1, retries, sleep_time
        )
        time.sleep(sleep_time)
    return None


async def _retry_request_async(func, retries=3, backoff=1):
    """
    Retry an async request with exponential backoff.
    """
    for attempt in range(retries):
        result = await func()
        if result:
            return result
        sleep_time = backoff * (2 ** attempt)
        logger.warning(
            "Async retry %s/%s after %ss", attempt + 1, retries, sleep_time
        )
        await asyncio.sleep(sleep_time)
    return None


# -------------------------------------------------------------------
# HTTP helpers
# -------------------------------------------------------------------

def _safe_get(url: str):
    """
    Internal synchronous HTTP helper.
    Returns parsed API dict or None.
    """
    logger.debug("Requesting URL: %s", url)

    def request():
        try:
            response = requests.get(url, headers=HEADERS, timeout=5)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data:
                logger.info("API success: %s", url)
                return data[0]
        except RequestException as e:
            logger.warning("API request failed: %s | %s", url, e)
        return None

    return _retry_request(request)


async def _safe_get_async(url: str):
    """
    Internal async HTTP helper.
    Returns parsed API dict or None.
    """
    logger.debug("Async requesting URL: %s", url)

    async def request():
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url, headers=HEADERS)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list) and data:
                    logger.info("Async API success: %s", url)
                    return data[0]
        except httpx.RequestError as e:
            logger.warning("Async API request failed: %s | %s", url, e)
        return None

    return await _retry_request_async(request)


# -------------------------------------------------------------------
# Public API (sync)
# -------------------------------------------------------------------

def fetch_by_pincode(pincode: str):
    """
    Fetch post office details by pincode (sync).

    Returns:
        list[dict]

    Raises:
        PincodeNotFoundError
        APIUnavailableError
    """
    logger.debug("Fetching pincode (sync): %s", pincode)

    result = _safe_get(f"{BASE_PINCODE_URL}{pincode}")

    if result and result.get("Status") == "Success":
        post_offices = result.get("PostOffice", [])
        if not post_offices:
            logger.error("No post offices found for pincode %s", pincode)
            raise PincodeNotFoundError(
                f"No post offices found for pincode {pincode}"
            )

        logger.debug("Saving pincode %s to cache", pincode)
        save_cached_pincode(pincode, post_offices)
        return post_offices

    cached = get_cached_pincode(pincode)
    if cached:
        logger.info("Cache hit for pincode %s", pincode)
        return cached

    logger.error("API unavailable and no cache for pincode %s", pincode)
    raise APIUnavailableError(
        f"Unable to fetch data for pincode {pincode}"
    )


def fetch_by_postoffice_name(name: str):
    """
    Fetch post office details by post office name (sync).

    Returns:
        list[dict]

    Raises:
        PostOfficeNotFoundError
        APIUnavailableError
    """
    logger.debug("Fetching post office (sync): %s", name)

    result = _safe_get(f"{BASE_POSTOFFICE_URL}{name}")

    if result and result.get("Status") == "Success":
        post_offices = result.get("PostOffice", [])
        if not post_offices:
            logger.error("No post offices found for '%s'", name)
            raise PostOfficeNotFoundError(
                f"No post offices found for '{name}'"
            )
        return post_offices

    logger.error("API unavailable for post office '%s'", name)
    raise APIUnavailableError(
        f"Unable to fetch data for post office '{name}'"
    )


# -------------------------------------------------------------------
# Public API (async)
# -------------------------------------------------------------------

async def fetch_by_pincode_async(pincode: str):
    """
    Fetch post office details by pincode (async).
    """
    logger.debug("Fetching pincode (async): %s", pincode)

    result = await _safe_get_async(f"{BASE_PINCODE_URL}{pincode}")

    if result and result.get("Status") == "Success":
        post_offices = result.get("PostOffice", [])
        if not post_offices:
            raise PincodeNotFoundError(
                f"No post offices found for pincode {pincode}"
            )
        save_cached_pincode(pincode, post_offices)
        return post_offices

    cached = get_cached_pincode(pincode)
    if cached:
        return cached

    raise APIUnavailableError(
        f"Unable to fetch data for pincode {pincode}"
    )


async def fetch_by_postoffice_name_async(name: str):
    """
    Fetch post office details by post office name (async).
    """
    logger.debug("Fetching post office (async): %s", name)

    result = await _safe_get_async(f"{BASE_POSTOFFICE_URL}{name}")

    if result and result.get("Status") == "Success":
        post_offices = result.get("PostOffice", [])
        if not post_offices:
            raise PostOfficeNotFoundError(
                f"No post offices found for '{name}'"
            )
        return post_offices

    raise APIUnavailableError(
        f"Unable to fetch data for post office '{name}'"
    )
