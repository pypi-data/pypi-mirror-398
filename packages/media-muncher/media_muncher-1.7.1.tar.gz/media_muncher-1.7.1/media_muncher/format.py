from enum import Enum
from os import path
from typing import Optional
from urllib.parse import urlparse


class MediaFormat(Enum):
    DASH = "DASH"
    HLS = "HLS"
    JPEG = "JPEG"
    PNG = "PNG"
    MP4 = "MP4"

    def __str__(self):
        return str(self.value)

    @staticmethod
    def guess_from_url(url) -> "Optional[MediaFormat]":
        # Check for a (final) extension first
        ext = path.splitext(urlparse(url).path)[1]
        match ext:
            case ".m3u8":
                return MediaFormat.HLS
            case ".mpd":
                return MediaFormat.DASH

        # otherwise search for match in the URL
        if any(s in url for s in [".mpd", "dash"]):
            return MediaFormat.DASH
        if any(s in url for s in [".m3u8", "hls"]):
            return MediaFormat.HLS
