import re
from datetime import timedelta
from functools import lru_cache
from typing import TYPE_CHECKING, List

from media_muncher.models.timeline_models import TimelineSpan

if TYPE_CHECKING:
    from media_muncher.handlers.hls import HLSHandler

import m3u8
from pymediainfo import MediaInfo

from media_muncher.codecstrings import CodecStringParser
from media_muncher.messages import ErrorMessage, WarningMessage


class HlsAnalyser:
    def __init__(self, handler: "HLSHandler") -> None:
        self.handler = handler

        self.messages = []

    def extract_renditions(self):
        m3u8_obj: m3u8.M3U8 = self.handler.document

        # Get info about renditions
        audio_renditions = {}
        video_renditions = {}

        fallback_audio_codec = None

        for variant in m3u8_obj.playlists:
            resolution = variant.stream_info.resolution
            bandwidth = variant.stream_info.bandwidth
            frame_rate = variant.stream_info.frame_rate

            codecstrings = variant.stream_info.codecs
            codecs = CodecStringParser.parse_multi_codec_string(codecstrings)

            fallback_audio_codec = None
            for codec in codecs:
                video_profile = "main"
                if codec["type"] == "video":
                    video_profile = codec.get("profile")
                    codec["resolution"] = resolution or self.get_resolution(
                        variant.absolute_uri
                    )
                    codec["bitrate"] = self._get_bitrate_from_playlist_name(
                        variant.uri, "video", fallback=bandwidth
                    )
                    codec["framerate"] = frame_rate or self.get_framerate(
                        variant.absolute_uri
                    )
                    codec["audio-group"] = variant.stream_info.audio
                    video_renditions[variant.uri] = codec

                if codec["type"] == "audio":
                    fallback_audio_codec = codec
                    # If the variant playlist has no resolution, it's a proper audio playlist
                    if not variant.stream_info.resolution:
                        key = variant.uri
                        codec["bitrate"] = self._get_bitrate_from_playlist_name(
                            variant.uri, "audio", fallback=bandwidth
                        )
                        audio_renditions[key] = codec
                        # TODO - Probably more complex than this...
                    else:
                        # We find the audio playlist through the associate media
                        key = variant.stream_info.audio
                        # TODO - better mechanism to actually extract audio info when muxed in
                        # TODO - support multiple languages and multiple bitrates
                        # We attempt to extract the bitrate from the playlist name
                        codec["bitrate"] = self._get_bitrate_from_playlist_name(
                            variant.uri, "audio"
                        )
                        if codec["bitrate"] is None:
                            # otherwise, we make wild assumptions
                            if video_profile == "baseline":
                                codec["bitrate"] = 64000
                            else:
                                codec["bitrate"] = 128000

                        # extract all audio media
                        audio_media = [m for m in variant.media if m.type == "AUDIO"]

                        if any(m for m in audio_media if m.uri is None):
                            codec["muxed"] = True

                        for m in audio_media:
                            this_codec = codec.copy()
                            this_codec["language"] = m.language
                            audio_renditions[f"{key}-{m.language}"] = this_codec

                # TODO - when audio not muxed in (separate or adjoining streaminf),
                #  adjust bitrate of video to remove audio

                # TODO - extract audio bitrate and sample rate with ffprobe?

        # Still no audio rendition?  That's an old HLS without audio group.
        # We assume there is one, just not named.
        if not audio_renditions:
            if not fallback_audio_codec:
                self.messages.append(
                    ErrorMessage(
                        "No audio rendition information found in HLS manifest.",
                        topic="audio",
                    )
                )
                fallback_audio_codec = {"codec": "aac", "bitrate": 128000}
            else:
                audio_renditions["default_audio"] = fallback_audio_codec

        return [*video_renditions.values(), *audio_renditions.values()]

    @staticmethod
    def _get_bitrate_from_playlist_name(playlist_name, media_type, fallback=None):
        # Attempt to extract bitrate from playlist name

        # unified streaming, eg. FBNHD_AC3-audio_384482_eng=384000-video=730000.m3u8
        if media_type == "video":
            match = re.search(r"video=(\d+)", playlist_name)
            if match:
                return int(match.group(1))

        if media_type == "audio":
            match = re.search(r"audio(_[a-z0-9_]+)?=(\d+)", playlist_name)
            if match:
                return int(match.group(2))

        return fallback

    def extract_packaging_info(self):
        return {
            "packaging": "HLS",
            "version": self.handler.protocol_version(),
            "container": self.handler.container_format(),
            "segment_duration_max": self.handler.target_duration(),
            "segment_duration": self.handler.standard_segment_duration(),
            "audio_only": self.handler.has_audio_only(),
            "muxed_audio": self.handler.has_muxed_audio(),
        }

    @lru_cache()
    def _analyse_first_segment(self, playlist_url):
        sub = m3u8.load(playlist_url)
        if sub.segment_map:
            first_segment = sub.segment_map[0]
        else:
            first_segment = sub.segments[0]
        return MediaInfo.parse(first_segment.absolute_uri)

    def get_framerate(self, playlist_url):
        try:
            media_info = self._analyse_first_segment(playlist_url)
            for track in media_info.tracks:
                if track.track_type == "Video":
                    frame_rate = track.frame_rate
                    if not frame_rate:
                        if track.frame_rate_mode == "VFR":
                            self.messages.append(
                                WarningMessage(
                                    f"Variable frame rate found in segments in {playlist_url}"
                                )
                            )
                        else:
                            self.messages.append(
                                WarningMessage(
                                    f"No frame rate found in segments in {playlist_url}"
                                )
                            )
                    else:
                        return float(track.frame_rate)
        except Exception as e:
            self.messages.append(
                WarningMessage(message=f"Unable to analyze media: {e}")
            )
            return None

    def get_resolution(self, playlist_url):
        try:
            media_info = self._analyse_first_segment(playlist_url)
        except Exception as e:
            self.messages.append(WarningMessage(f"Unable to analyze media: {e}"))
            return None
        for track in media_info.tracks:
            if track.track_type == "Video":
                resolution = track.width, track.height
                if not resolution:
                    self.messages.append(
                        WarningMessage(
                            f"No resolution found in segments in {playlist_url}"
                        )
                    )
                else:
                    return resolution

    def get_timeline_spans(self) -> List[TimelineSpan]:
        m3u8_obj: m3u8.M3U8 = self.handler.document

        if self.handler.has_children():
            # pick the first playlist
            handler: HLSHandler = self.handler.get_child(0)
        else:
            handler: HLSHandler = self.handler

        m3u8_obj = handler.document

        spans = []

        def _determine_content_type(segment: m3u8.Segment) -> str:
            if segment.cue_out:
                return "ad"
            else:
                return "content"

        def _determine_trigger(segment: m3u8.Segment) -> str:
            if segment.cue_in:
                return "CUE-IN"
            if segment.cue_out_start:
                return "CUE-OUT"
            if segment.discontinuity:
                return "DISCONTINUITY"
            return ""

        def _starts_new_span(segment: m3u8.Segment) -> bool:
            if segment.discontinuity or segment.cue_in or segment.cue_out_start:
                return True
            return False

        current_span: TimelineSpan = TimelineSpan()

        # find all discontinuities
        segment: m3u8.Segment
        for i, segment in enumerate(m3u8_obj.segments):
            # new span at discontinuities or significant markers
            if _starts_new_span(segment):
                # close the current span
                if current_span.duration > timedelta(0):
                    current_span.end = (
                        segment.current_program_date_time or current_span.duration
                    )
                    spans.append(current_span)

                # and start a new one
                current_span = TimelineSpan()

            # new span need initialising
            if current_span.start is None:
                current_span.start = segment.current_program_date_time or timedelta(
                    seconds=0
                )
                current_span.span_type = _determine_content_type(segment)
                current_span.start_trigger = _determine_trigger(segment)
                current_span.duration = timedelta(seconds=segment.duration)
                current_span.num_segments = 1
            else:
                current_span.duration += timedelta(seconds=segment.duration)
                current_span.num_segments += 1

            # last segment: end of playlist
            if i == len(m3u8_obj.segments) - 1:
                current_span.end = (
                    segment.current_program_date_time or current_span.duration
                ) + timedelta(seconds=segment.duration)
                spans.append(current_span)

        return spans
