from .http import get
from .models.status import Status


def get_status() -> Status:
    """Get the current status of the Hytale API.

    Returns:
        Status: The current status.
    """
    data = get("/status")
    return Status(data)
