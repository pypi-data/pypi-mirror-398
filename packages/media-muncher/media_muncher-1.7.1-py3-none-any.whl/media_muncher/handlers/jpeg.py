from media_muncher.format import MediaFormat

from .generic import ContentHandler


class JPEGHandler(ContentHandler):
    media_format = MediaFormat.JPEG
    content_types = ["image/jpeg"]
    file_extensions = [".jpeg", ".jpg"]

    def __init__(self, url, content, **kwargs):
        super().__init__(url, content, **kwargs)

    def read(self):
        return "Handling JPEG file."

    @staticmethod
    def is_supported_content(content):
        # TODO - add handling by trying to open the image
        return False
