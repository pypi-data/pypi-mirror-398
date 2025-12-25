from datetime import datetime

import attrs

from ..base import FromDictMixin
from .cover_image import CoverImage


@attrs.define(slots=True)
class BlogPost(FromDictMixin):
    publishedTo: list[str]
    featured: bool
    tags: list[str]
    _id: str = attrs.field(alias="_id")
    disableCfAutoplay: bool
    author: str
    title: str
    body: str
    publishedAt: datetime
    coverImage: CoverImage
    createdAt: datetime
    slug: str
    previous: "BlogPost" = None

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        if "publishedAt" in data:
            data["publishedAt"] = datetime.fromisoformat(data["publishedAt"])
        if "createdAt" in data:
            data["createdAt"] = datetime.fromisoformat(data["createdAt"])
        if "coverImage" in data:
            data["coverImage"] = CoverImage.from_dict(data["coverImage"])
        if "previous" in data:
            data["previous"] = BlogPost.from_dict(data["previous"])
        return super().from_dict(data)
