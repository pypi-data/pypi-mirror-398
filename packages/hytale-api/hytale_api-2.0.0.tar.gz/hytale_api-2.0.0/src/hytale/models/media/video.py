from .media import Media


class Video(Media):
    caption: str
    download: str = (
        None  # TODO: str is guessed here, could be something else (only seen as null so far)
    )
