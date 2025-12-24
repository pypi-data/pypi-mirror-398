from media_muncher.format import MediaFormat

from .generic import ContentHandler


class PNGHandler(ContentHandler):
    media_format = MediaFormat.PNG
    content_types = ["image/png"]

    def __init__(self, url, content, **kwargs):
        self.url = url
        self.content = content

    def read(self):
        return "Handling PNG file."

    @staticmethod
    def is_supported_content(content):
        # TODO - add handling by trying to open the image
        return False
