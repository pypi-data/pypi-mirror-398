from typing import Union


class BaseHytaleError(Exception):
    pass


class HytaleAPIError(BaseHytaleError):
    """Base exception for Hytale API errors."""

    def __init__(self, message: str, http_code: Union[int, None]):
        super().__init__(message)
        self.http_code = http_code


class BlockedError(HytaleAPIError):
    """Exception for when access is blocked by Cloudflare."""


class RedirectError(HytaleAPIError):
    """Request in accounts API had incorrect cookies so was redirected"""
