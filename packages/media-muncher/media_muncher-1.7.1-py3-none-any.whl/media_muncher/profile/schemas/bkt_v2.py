from fractions import Fraction
from importlib.metadata import version

from media_muncher.messages import InfoMessage, WarningMessage
from media_muncher.profile.schemas.base import BaseSchemaGenerator
from media_muncher.profile.schemas.bkt_v1 import (
    calculate_min_gop_size,
    calculate_recommended_durations,
)


class BktV2ProfileSchemaGenerator(BaseSchemaGenerator):
    schema_name = "bkt-v2"

    def generate(self, renditions, packaging, name: str = ""):
        video_renditions = [r for r in renditions if r["type"] == "video"]
        audio_renditions = [r for r in renditions if r["type"] == "audio"]
        video_ladder = {}
        audio_ladder = {}

        audio_sample_rate = 48000

        target_segment_duration = packaging.get("segment_duration", 4)
        if float(target_segment_duration) == int(target_segment_duration):
            target_segment_duration = int(target_segment_duration)

        if len(video_renditions):
            video_frame_rate = renditions[0]["framerate"]
            if isinstance(video_frame_rate, str):
                video_frame_rate = eval(video_frame_rate)

            if video_frame_rate is None:
                video_frame_rate = self.config.get("framerate")
                self.messages.append(
                    WarningMessage(
                        f"Default video framerate of {video_frame_rate} was selected, since it could not be detected in the source"
                    )
                )

            is_common_frame_rate = all(
                [r["framerate"] == video_frame_rate for r in video_renditions]
            )
            if not is_common_frame_rate:
                self.messages.append(
                    WarningMessage(
                        "The video frame rates are different for different renditions. The output of this tool may not be correct."
                    )
                )
            video_frame_rate_fraction = _to_fraction(video_frame_rate)
            framerate_repr = {
                "num": video_frame_rate_fraction.numerator,
                "den": video_frame_rate_fraction.denominator,
            }

            if video_frame_rate_fraction.denominator > 1:
                self.messages.append(
                    WarningMessage(
                        "Using fractional frame rates is not recommended, as it prevents perfect alignment of audio and video segments"
                    )
                )

            if video_frame_rate_fraction.denominator == 1 and not packaging.get(
                "muxed_audio"
            ):
                min_gop_size = calculate_min_gop_size(
                    video_frame_rate, audio_sample_rate
                )
                (
                    selected_duration,
                    candidate_durations,
                ) = calculate_recommended_durations(
                    video_frame_rate, min_gop_size, target_segment_duration
                )
                if not any(
                    d for d in candidate_durations if d[0] == target_segment_duration
                ):
                    idx = next(
                        (
                            i
                            for i, t in enumerate(candidate_durations)
                            if t[0] == selected_duration[0]
                        ),
                        None,
                    )
                    dur_strings = "\n - " + "\n - ".join(
                        [
                            f'"{s}" (= {g} frames = {d:.3f}s)'
                            for g, d, s in candidate_durations[idx - 1 : idx + 2]
                        ]
                    )
                    self.messages.append(
                        InfoMessage(
                            f"The target segment duration (of {target_segment_duration}s) will cause audio and video segments to not align perfectly, which could cause issues during manifest manipulation.\n"
                            f"For this video frame rate and audio sample rate, it is recommended to create video segments with a GOP with a size multiple of {min_gop_size} frames.\n"
                            f'I have therefore selected "{selected_duration[2]}" (ie. {selected_duration[1]:.3f}s)\n'
                            f"Other nearby segment durations are: {dur_strings}"
                        )
                    )
                    target_segment_duration = selected_duration[2]
            else:
                selected_duration = None

            video_ladder = {
                "common": {
                    "preset": self.config["preset"].upper(),
                    "framerate": framerate_repr,
                }
            }
            if "selected_duration" in locals() and selected_duration:
                video_ladder["common"]["gop_size"] = selected_duration[0]
                video_ladder["common"]["keyint_min"] = selected_duration[0]

            for i, r in enumerate(video_renditions):
                height = _make_even(r["resolution"][1])
                rung = {
                    "_codec_info": f"{r['codec']} {r['profile']} {r['level']}",
                    "codec_string": r["codecstring"],
                    "scale": {"width": -2, "height": height},
                    "bitrate": r["bitrate"],
                }

                video_ladder[f"video_{i}"] = rung

        # Audio rungs
        audio_ladder = {
            "common": {"sampling_rate": 48000, "loudnorm": {"i": -23, "tp": -1}}
        }

        for i, r in enumerate(audio_renditions):
            audio_ladder[f"audio_{i}"] = {
                "_codec_info": f"{r['codec']} {r['mode']}",
                "codec_string": r["codecstring"],
                "bitrate": r["bitrate"],
            }

        # Packaging options

        muxed_audio = packaging.get("muxed_audio")
        container = packaging.get("container")
        if (container == "MPEG-TS" and not muxed_audio) or container == "ISOBMFF":
            self.messages.append(
                WarningMessage(
                    "Since audio renditions are separate from video, you should ensure that your segment size is compatible between audio rate and video frame rate"
                )
            )

        packaging_options = {}
        packaging_options["hls_client_manifest_version"] = (
            packaging.get("version", 3) or 3
        )
        target_segment_duration_fraction = _to_fraction(target_segment_duration)
        packaging_options["hls_minimum_fragment_length"] = {
            "num": target_segment_duration_fraction.numerator,
            "den": target_segment_duration_fraction.denominator,
        }

        advanced_packaging_options = {}
        packaging_options["advanced"] = advanced_packaging_options
        if not packaging.get("audio_only"):
            advanced_packaging_options["--hls.no_audio_only"] = ""

        if packaging.get("container") == "ISOBMFF":
            advanced_packaging_options["--hls.fmp4"] = ""
        else:
            if not packaging.get("muxed_audio"):
                advanced_packaging_options["--hls.no_multiplex"] = ""

        profile = {
            "version": "02.00.00",
            "name": name,
            "type": "OFFLINE_TRANSCODING",
            "audios": audio_ladder,
            "videos": video_ladder,
            "packaging": packaging_options,
            "_generator": "bpkio-python-sdk/" + version("bpkio-python-sdk"),
        }

        return profile


def _make_even(n):
    return n if n % 2 == 0 else n - 1


def _to_fraction(s):
    if isinstance(s, str) and "/" in s:
        num, denom = s.split("/")
        return Fraction(int(float(num)), int(float(denom)))
    else:
        return Fraction(str(s))
