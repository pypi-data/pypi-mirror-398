from typing import Union

import requests

from ._version import __version__
from .exceptions import BlockedError, HytaleAPIError, RedirectError

BASE_URL = "hytale.com/api"
DEFAULT_USER_AGENT = (
    f"hytale-api/{__version__} (+https://github.com/DRagssss/hytale-api)"
)

_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",  # expect JSON but can handle other responses
    }
)


def get(
    path: str,
    sub_domain: str = "",
    cookies: dict = {},
    headers: dict = {},
    proxies: dict = {},
    **params,
) -> Union[dict, list, str]:
    """Send a get request to the Hytale API

    Args:
        path (str): The path of the endpoint (eg. "/blog/post/archive")
        sub_domain (str, optional): The subdomain of the API (eg. "store."). Defaults to "".
        headers (dict, optional): Additional headers to include in the request. Defaults to None.
        proxies (dict, optional): Proxies to use for the request. Defaults to None.

    Raises:
        HytaleAPIError: Generic error
        BlockedError: Error raised if cloudflare blocks the request (due to spam or headers misconfiguration)
        HytaleAPIError: Generic HTTP error

    Returns:
        Union[dict, list, str]: Converted JSON response from the API if the response's Content-Type is `application/json`, otherwise a string.
    """
    url = "https://" + sub_domain + BASE_URL + path
    try:
        response = _session.get(
            url,
            params=params,
            headers=headers,
            proxies=proxies,
            cookies=cookies,
            timeout=3,
        )
    except requests.RequestException as exc:
        raise HytaleAPIError(str(exc), None) from exc

    if not response.ok:
        if "Attention Required! | Cloudflare" in response.text:
            raise BlockedError("This IP is blocked", response.status_code)
        raise HytaleAPIError(response.text, response.status_code)

    if "Login | Hytale" in response.text:
        raise RedirectError(
            "Incorrect cookie: ensure you inputted a value ory_kratos_session cookie.",
            response.status_code,
        )

    content_type = response.headers.get("Content-Type", "")

    if content_type == "application/json":
        return response.json()
    else:
        return response.text
