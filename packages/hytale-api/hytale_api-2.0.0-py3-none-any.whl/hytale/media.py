from .http import get
from .models.media.image import Image
from .models.media.video import Video


def get_screenshots() -> list[Image]:
    """Get screenshots from the media API.

    Returns:
        list[Image]: A list of images.
    """
    data = get("/media/category/screenshots")
    return [Image.from_dict(item) for item in data]


def get_desktop_wallpapers() -> list[Image]:
    """Get desktop wallpapers from the media API.

    Returns:
        list[Image]: A list of images.
    """
    data = get("/media/category/desktopWallpapers")
    return [Image.from_dict(item) for item in data]


def get_mobile_wallpapers() -> list[Image]:
    """Get mobile wallpapers from the media API.

    Returns:
        list[Image]: A list of images.
    """
    data = get("/media/category/mobileWallpapers")
    return [Image.from_dict(item) for item in data]


def get_concept_arts() -> list[Image]:
    """Get concept arts from the media API.

    Returns:
        list[Image]: A list of images.
    """
    data = get("/media/category/conceptArt")
    return [Image.from_dict(item) for item in data]


def get_videos() -> list[Video]:
    """Get videos from the media API.

    Returns:
        list[Video]: A list of videos.
    """
    data = get("/media/category/videos")
    return [Video.from_dict(item) for item in data]
