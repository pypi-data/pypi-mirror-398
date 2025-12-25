from datetime import datetime

import attrs

from ..base import FromDictMixin


@attrs.define(slots=True)
class CoverImage(FromDictMixin):
    variants: list[str]
    _id: str = attrs.field(alias="_id")
    s3Key: str
    mimeType: str
    attached: bool
    createdAt: datetime
    contentId: str
    contentType: str

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        if "createdAt" in data:
            data["createdAt"] = datetime.fromisoformat(data["createdAt"])
        return super().from_dict(data)
