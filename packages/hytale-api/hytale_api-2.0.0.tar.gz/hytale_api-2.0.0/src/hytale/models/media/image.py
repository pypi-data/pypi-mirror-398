from .media import Media


class Image(Media):

    file: str

    def get_link(self):
        return (
            "https://cdn.hytale.com/variants/"
            + "media_"
            + self.category.prefixed()
            + "thumb_"
            + self.src
        )
