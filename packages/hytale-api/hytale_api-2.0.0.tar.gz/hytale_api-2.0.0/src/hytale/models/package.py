import re
from typing import Union

import attrs

from .base import FromDictMixin


@attrs.define(slots=True)
class Package(FromDictMixin):
    ordinal: int
    key: str
    entitlement: str
    name: str
    description: str
    class_: str
    card: str
    banner: str
    features: list[str]
    highlights: list[str]
    variationsPreview: str
    id: int
    upgrades: dict[str, int] = {}

    def get_color(self) -> Union[str, None]:
        """Get the branding color of the package from the website.

        Returns:
            Union[str, None]: The hexadecimal color if it was found.
        """
        match = re.search(r"#([0-9A-Fa-f]{6})", self.class_)
        if match:
            return match.group(0)
        return None
