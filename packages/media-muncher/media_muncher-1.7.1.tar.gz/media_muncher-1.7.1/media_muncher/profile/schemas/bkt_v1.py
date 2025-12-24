import math

from media_muncher.messages import InfoMessage, WarningMessage
from media_muncher.profile.schemas.base import BaseSchemaGenerator


class BktV1ProfileSchemaGenerator(BaseSchemaGenerator):
    schema_name = "bkt-v1"

    def generate(self, renditions, packaging, name: str = ""):
        common = {
            "codecv": "h264",
            "preset": self.config["preset"],
        }

        video_frame_rate = None
        audio_sample_rate = None

        jobs = []
        for r in renditions:
            if r["type"] == "video":
                video_frame_rate = r["framerate"]
                jobs.append(
                    {
                        "level": str(r["level"]),
                        "scale": f"-2:{r['resolution'][1]}",
                        "bitratev": str(r["bitrate"]),
                        "profilev": r["profile"],
                        "frameratev": str(r["framerate"]) if r["framerate"] else "",
                    }
                )

            if r["type"] == "audio":
                audio_sample_rate = 48000
                audio_spec = {
                    "codeca": "aac",
                    "frameratea": "48000",
                    "bitratea": str(r["bitrate"]),
                    "loudnorm": "I=-23:TP=-1",
                }

                common.update(audio_spec)

        target_segment_duration = packaging.get("segment_duration", 4)
        if float(target_segment_duration) == int(target_segment_duration):
            target_segment_duration = int(target_segment_duration)

        muxed_audio = packaging.get("muxed_audio")
        container = packaging.get("container")
        if (container == "MPEG-TS" and not muxed_audio) or container == "ISOBMFF":
            self.messages.append(
                WarningMessage(
                    "Since audio renditions are separate from video, you should ensure that your segment size is compatible between audio rate and video frame rate"
                )
            )

        if video_frame_rate:
            if float(video_frame_rate) == int(video_frame_rate):
                video_frame_rate = int(video_frame_rate)

            if not isinstance(video_frame_rate, int):
                self.messages.append(
                    WarningMessage(
                        "Using fractional frame rates is not recommended, as it prevents perfect alignment of audio and video segments"
                    )
                )
            else:
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
                    dur_strings = "\n - " + "\n - ".join(
                        [
                            f'"{s}" (= {g} frames = {d:.3f}s)'
                            for g, d, s in candidate_durations
                        ]
                    )
                    self.messages.append(
                        InfoMessage(
                            f"The target segment duration (of {target_segment_duration}s) will cause audio and video segments to not align perfectly, which could cause issues during manifest manipulation.\n"
                            f"For this video frame rate and audio sample rate, it is recommended to create video segments with a GOP multiple of {min_gop_size}.\n"
                            f'I have therefore selected "{selected_duration[2]}" (ie. {selected_duration[1]:.3f}s)\n'
                            f"Other compatible segment durations are: {dur_strings}"
                        )
                    )
                    target_segment_duration = selected_duration[2]

                    common["gop_size"] = str(selected_duration[0])
                    common["keyint_min"] = str(selected_duration[0])

        packaging_options = {}
        packaging_options["--hls.client_manifest_version="] = str(
            packaging.get("version", "3") or "3"
        )
        packaging_options["--hls.minimum_fragment_length="] = str(
            target_segment_duration
        )
        if not packaging.get("audio_only"):
            packaging_options["--hls.no_audio_only"] = ""

        if packaging.get("container") == "ISOBMFF":
            packaging_options["--hls.fmp4"] = ""
        else:
            if not packaging.get("muxed_audio"):
                packaging_options["--hls.no_multiplex"] = ""

        profile = {
            "packaging": packaging_options,
            "servicetype": "offline_transcoding",
            "transcoding": {
                "jobs": jobs,
                "common": common,
            },
        }

        return profile


# Common utility methods
def calculate_min_gop_size(frame_rate, sample_rate, frames_per_packet=1024):
    gop_size = (
        frame_rate
        * frames_per_packet
        / math.gcd(int(frame_rate * frames_per_packet), sample_rate)
    )
    return int(gop_size)


def calculate_recommended_durations(frame_rate, gop_size, target_duration):
    candidate_durations = []
    dur = 0
    i = 1
    selected_duration = None
    while dur < 12:
        dur = int(gop_size * i) / frame_rate
        t = (gop_size * i, dur, f"{int(gop_size * i)}/{int(frame_rate)}")
        candidate_durations.append(t)

        if dur <= target_duration:
            selected_duration = t

        i += 1
    return (
        selected_duration,
        candidate_durations,
    )
