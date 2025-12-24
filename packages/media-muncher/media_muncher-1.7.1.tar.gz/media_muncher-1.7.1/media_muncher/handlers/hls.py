import os
import random
from functools import lru_cache
from typing import Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import m3u8
import requests
from loguru import logger

from media_muncher.analysers.hls import HlsAnalyser
from media_muncher.codecstrings import CodecStringParser
from media_muncher.exceptions import MediaHandlerError
from media_muncher.format import MediaFormat
from media_muncher.handlers.generic import ContentHandler


class HLSHandler(ContentHandler):
    media_format = MediaFormat.HLS
    content_types = ["application/x-mpegurl", "application/vnd.apple.mpegurl"]

    def __init__(self, url, content: bytes | None = None, **kwargs):
        super().__init__(url, content, **kwargs)
        self._document: m3u8.M3U8 = None

    @property
    def document(self) -> m3u8.M3U8:
        if not self._document:
            try:
                if isinstance(self.content, bytes):
                    self._document = m3u8.loads(
                        content=self.content.decode(), uri=self.url
                    )
                else:
                    self._document = m3u8.loads(content=self.content, uri=self.url)
            except Exception as e:
                raise MediaHandlerError(
                    message="The HLS manifest could not be parsed",
                    original_message=e.args[0],
                )
        return self._document

    def read(self):
        return "Handling HLS file."

    @property
    def inspector(self) -> HlsAnalyser:
        return HlsAnalyser(self)

    @staticmethod
    def is_supported_content(content):
        if isinstance(content, bytes):
            return content.decode().startswith("#EXTM3U")
        else:
            return content.startswith("#EXTM3U")

    def appears_supported(self) -> bool:
        return self.is_supported_content(self.content)

    def has_children(self) -> bool:
        if self.document.is_variant:
            return True
        return False

    def sub_playlists(self):
        return self.document.playlists + [m for m in self.document.media if m.uri]

    def num_children(self) -> int:
        return len(self.sub_playlists())

    def get_child(self, index: int, additional_query_params: dict = {}):
        playlists = self.sub_playlists()

        child_url = playlists[index - 1].absolute_uri
        if additional_query_params:
            child_url = self._add_query_parameters_from_dict(
                child_url, additional_query_params
            )

        try:
            return HLSHandler(
                url=child_url,
                headers=self.headers,
            )
        except IndexError as e:
            raise MediaHandlerError(
                message=f"The HLS manifest only has {len(self.document.playlists)} renditions.",
                original_message=e.args[0],
            )

    def get_child_by_uri(self, uri: str):
        playlists = self.sub_playlists()
        for i, playlist in enumerate(playlists):
            if playlist.uri == uri:
                return self.get_child(i + 1)
        return None

    @staticmethod
    def _add_query_parameters_from_dict(url: str, new_params: dict):
        parsed_url = urlparse(url)

        # Parse the existing query parameters
        query_params = parse_qs(parsed_url.query)

        # Add the new query parameter
        for key, value in new_params.items():
            query_params[key] = value

        # Reconstruct the query string
        new_query = urlencode(query_params, doseq=True)

        # Reconstruct the full URL with the new query string
        new_url = urlunparse(parsed_url._replace(query=new_query))

        return new_url

    @lru_cache()
    def _fetch_sub(self, uri, cache_buster=None):
        logger.debug(f"Fetching sub-playlist from {uri} with headers {self.headers}")
        try:
            return m3u8.load(
                uri,
                headers=self.headers,
                # TODO - ability to set exact CERT.
                # See https://github.com/globocom/m3u8?tab=readme-ov-file#using-different-http-clients
                verify_ssl=(True if self.verify_ssl is True else False),
            )
        except Exception as e:
            raise MediaHandlerError(
                message=f"The HLS media playlist could not be parsed: {uri}",
                original_message=e.args[0] if e.args and len(e.args) else str(e),
            )

    def protocol_version(self):
        """Returns the protocol version of the HLS

        Returns:
            str
        """
        # Prefer extraction from the sub-playlists
        ver = None
        if self.has_children():
            sub = self._fetch_sub(self.document.playlists[0].absolute_uri)
            ver = sub.version

        if ver is None:
            ver = self.document.version

        if ver is None:
            ver = 3

        return int(ver)

    def is_live(self):
        """Checks if the HLS is a live stream (ie. without an end)

        Returns:
            bool
        """
        # Check the first sub-playlist
        if len(self.document.playlists):
            sub = self._fetch_sub(self.document.playlists[0].absolute_uri)
            if not sub.is_endlist:  # type: ignore
                return True
            else:
                return False

        else:
            return not self.document.is_endlist

    def get_duration(self):
        """Calculates the duration of the stream (in seconds)

        Returns:
            int
        """
        if self.is_live():
            return -1
        else:
            sub = self._fetch_sub(self.document.playlists[0].absolute_uri)
            return sum([seg.duration for seg in sub.segments])

    def num_segments(self):
        """Calculates the number of segments in the stream

        Returns:
            int
        """
        if self.has_children():
            sub = self._fetch_sub(self.document.playlists[0].absolute_uri)
            return len(sub.segments)
        else:
            return len(self.document.segments)

    def first_segment_url(self):
        sub = self._fetch_sub(
            self.document.playlists[0].absolute_uri, cache_buster=random.random()
        )
        segment = sub.segments[0]
        return segment.absolute_uri

    def container_format(self):
        """Checks the container format of the segments

        Returns:
            str
        """
        if len(self.document.playlists) == 0:
            raise MediaHandlerError("There seem to be no playlists in this manifest")
        sub = self._fetch_sub(self.document.playlists[0].absolute_uri)

        # We just check if there is a segment map
        if len(sub.segment_map):
            return "ISOBMFF"
        else:
            return "MPEG-TS"

    def has_muxed_audio(self) -> bool:
        """Checks is the audio stream is muxed in with video

        Returns:
            bool
        """
        # TODO - 2 additional use cases:
        #  - video only
        #  - audio only (no video)

        audio_media = [m for m in self.document.media if m.type == "AUDIO"]

        # If there is no media, then must be muxed
        if len(audio_media) == 0:
            return True

        # Otherwise, if the media doesn't have a URI, then must be muxed
        for media in self.document.media:
            if media.uri is None:
                return True
        return False

    def has_audio_only(self) -> bool:
        for playlist in self.document.playlists:
            # extract info from codecs
            cdc = CodecStringParser.parse_multi_codec_string(
                playlist.stream_info.codecs
            )
            # find any rendition without a video codec
            cdc_v = next((d for d in cdc if d.get("type") == "video"), None)
            if not cdc_v:
                return True
        return False

    def target_duration(self):
        if self.has_children():
            sub = self._fetch_sub(self.document.playlists[0].absolute_uri)
            return sub.target_duration
        else:
            return self.document.target_duration

    def standard_segment_duration(self):
        if self.has_children():
            sub = self._fetch_sub(self.document.playlists[0].absolute_uri)
            # Check the duration of all segments
            durations = [seg.duration for seg in sub.segments]

        else:
            durations = [seg.duration for seg in self.document.segments]

        # Crudely, we just pick the duration that is present most often in the playlists
        durations = sorted(durations, key=durations.count, reverse=True)
        return durations[0]

    def get_update_interval(self):
        return self.target_duration()

    def extract_info(self) -> Dict:
        info = {
            "format": "HLS",
            "version": self.protocol_version(),
            "type": "Live" if self.is_live() else "VOD",
            "container": self.container_format(),
            "audio_only": self.has_audio_only(),
            "target_duration": self.target_duration(),
            "duration": (
                "(live)" if self.is_live() else seconds_to_timecode(self.get_duration())
            ),
            "duration (sec)": (
                "(live)" if self.is_live() else f"{self.get_duration():.3f}"
            ),
            "segments": self.num_segments(),
        }

        return info

    def get_segment_for_url(self, url):
        for segment in self.document.segments:
            if segment.uri == url:
                return segment

    def get_segment_index(self, seg: m3u8.model.Segment):
        return (
            self.document.segments.index(seg) if seg in self.document.segments else None
        )

    def extract_features(self) -> List[Dict]:
        """Extracts essential information from the HLS manifest"""
        arr = []
        index = 0

        if self.document.is_variant:
            for playlist in self.document.playlists:
                index += 1

                si = playlist.stream_info

                data = dict(
                    index=index,
                    type="variant",
                    # uri=playlist.uri,
                    # url=playlist.absolute_uri,
                    codecs=si.codecs,
                )

                # extract info from codecs
                cdc = CodecStringParser.parse_multi_codec_string(si.codecs)
                cdc_v = next((d for d in cdc if d.get("type") == "video"), None)
                cdc_a = next((d for d in cdc if d.get("type") == "audio"), None)

                if cdc_a:
                    data["codeca"] = cdc_a["cc"]
                if cdc_v:
                    data["codecv"] = cdc_v["cc"]
                    data["profilev"] = cdc_v["profile"]
                    data["levelv"] = cdc_v["level"]

                res = (
                    "{} x {}".format(
                        si.resolution[0],
                        si.resolution[1],
                    )
                    if si.resolution
                    else ""
                )
                data["resolution"] = res
                data["bandwidth"] = si.bandwidth

                data["uri_short"] = shorten_url(playlist.uri)

                arr.append(data)

            for media in self.document.media:
                if media.uri:
                    index += 1
                    data = dict(
                        index=index,
                        type="media",
                        uri=media.uri,
                        language=media.language,
                        # url=media.absolute_uri,
                        uri_short=shorten_url(media.uri),
                    )

                    arr.append(data)

        return arr

    def download(
        self,
        output_path: str = None,
        all_segments: bool = False,
        num_segments: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
    ):
        sub_mapping = {}

        if num_segments is not None and num_segments > 0:
            total_tasks = 1 + self.num_children() * (1 + num_segments)
        elif all_segments:
            # We assume that all playlists have the same number of segments
            total_tasks = 1 + self.num_children() * (1 + self.num_segments())
        else:
            total_tasks = 1 + self.num_children()

        logger.debug(f"Number of files to download: {total_tasks}")
        if progress_callback:
            progress_callback(
                f"Number of files to download: {total_tasks}", total=total_tasks
            )

        # Create the output path if it doesn't exist
        if output_path and not os.path.exists(output_path):
            os.makedirs(output_path)

        # Download the sub-playlists first
        for sub_playlist in self.sub_playlists():
            filename = self._download_sub_playlist(
                sub_playlist.uri,
                output_path,
                all_segments,
                num_segments,
                progress_callback,
            )
            sub_mapping[sub_playlist.uri] = filename

        main_filename = "main.m3u8"
        local_file_path = os.path.join(output_path, main_filename)
        with open(local_file_path, "wb") as f:
            f.write(self.content)

        message = f"Downloaded main playlist to {local_file_path}"
        logger.info(message)
        if progress_callback:
            progress_callback(message)

        return sub_mapping

    def _download_sub_playlist(
        self,
        playlist_uri: str,
        output_path: str,
        all_segments: bool = False,
        num_segments: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
    ):
        # extract the relative path from the URI
        # TODO - handle absolute paths
        if playlist_uri.startswith("http"):
            raise NotImplementedError(
                f"The URI {playlist_uri} is an absolute URL, not a relative path"
            )
        if playlist_uri.startswith("../"):
            raise NotImplementedError(
                f"The URI {playlist_uri} is a relative path, not an absolute path"
            )

        relative_path = os.path.dirname(playlist_uri)
        filename = os.path.basename(playlist_uri)

        local_path = os.path.join(output_path, relative_path)
        # Create the output path if it doesn't exist
        if not os.path.exists(local_path):
            os.makedirs(local_path, exist_ok=True)

        sub_handler = self.get_child_by_uri(playlist_uri)

        if all_segments:
            num_segments = sub_handler.num_segments()

        if num_segments > 0:
            for i in range(0, num_segments):
                # TODO - handle absolute URLs + modify the playlist to point to the local segments
                absolute_uri = sub_handler.document.segments[i].absolute_uri
                segment_uri = sub_handler.document.segments[i].uri
                if segment_uri.startswith("http"):
                    raise NotImplementedError(
                        f"The URI {segment_uri} is an absolute URL, not a relative path"
                    )
                if segment_uri.startswith("../"):
                    raise NotImplementedError(
                        f"The URI {segment_uri} is a relative path, not an absolute path"
                    )

                segment_filename = os.path.basename(segment_uri)
                segment_local_path = os.path.join(local_path, segment_filename)
                with open(segment_local_path, "wb") as f:
                    # make a request (using requests) to the segment URI and write the content to the file
                    # TODO - handle headers and redirects
                    f.write(requests.get(absolute_uri, headers=self.headers).content)

                    message = f"Downloaded segment to {segment_local_path}"
                    logger.info(message)
                    if progress_callback:
                        progress_callback(message)

        local_file_path = os.path.join(local_path, filename)
        with open(local_file_path, "wb") as f:
            f.write(sub_handler.content)

        message = f"Downloaded sub-playlist to {local_file_path}"
        logger.info(message)
        if progress_callback:
            progress_callback(message)

        return filename


def shorten_url(uri):
    u = urlparse(uri)
    shortened_url = u.path[-50:]
    if u.query:
        shortened_url += "?..."
    return shortened_url


def seconds_to_timecode(duration: float, with_milliseconds=False) -> str:
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)

    if with_milliseconds:
        return f"{int(hours)}:{int(minutes):02d}:{seconds:02d}.{milliseconds:03d}"
    else:
        return f"{int(hours)}:{int(minutes):02d}:{seconds:02d}"
