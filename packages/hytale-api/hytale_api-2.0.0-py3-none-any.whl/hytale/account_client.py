from .exceptions import HytaleAPIError
from .http import get


class AccountClient:
    """Client to interact with Hytale account endpoints."""

    def __init__(self, ory_kratos_session: str, proxies={}):
        """Initialize AccountClient class with cookie to allow the endpoints to be used.

        Args:
            ory_kratos_session (str): The ory_kratos_session cookie value (seems to expire every month)
            proxies (dict): Proxies to use for requests. Defaults to None
        """
        self.ory_kratos_session = self._extract_value_from_ory_kratos_cookie(
            ory_kratos_session
        )
        self.proxies = proxies

    def _extract_value_from_ory_kratos_cookie(self, part: str) -> str:
        """
        Extracts the value from a 'ory_kratos_session=...' or just '...'

        Returns:
            str: The value of the ory_kratos_session key
        """
        if part.startswith("ory_kratos_session="):
            return part.split("=", 1)[1]
        else:
            return part.replace(";", "").strip()

    def get_available(self, username: str) -> bool:
        """Check if a username is not reserved by another user

        Args:
            username (str): The username to check

        Returns:
            bool: True if the username is available
        """
        try:
            data = get(
                "/account/username-reservations/availability",
                "accounts.",
                {"ory_kratos_session": self.ory_kratos_session},
                proxies=self.proxies,
                username=username,
            )
        except HytaleAPIError as e:
            if str(e) == "" and e.http_code == 400:
                return False
            else:
                raise e

        return data == ""  # assuming the only "ok" response is 200
