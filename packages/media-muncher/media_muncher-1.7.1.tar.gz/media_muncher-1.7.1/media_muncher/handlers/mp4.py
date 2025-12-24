from media_muncher.format import MediaFormat

from .generic import ContentHandler


class MP4Handler(ContentHandler):
    media_format = MediaFormat.MP4
    content_types = ["video/mp4"]

    def __init__(self, url, content, **kwargs):
        self.url = url
        self._content = content

    def read(self):
        return "Handling MP4 file."

    @staticmethod
    def is_supported_content(content):
        # TODO - add handling by trying to open the video (or at least the start of it)
        return False
