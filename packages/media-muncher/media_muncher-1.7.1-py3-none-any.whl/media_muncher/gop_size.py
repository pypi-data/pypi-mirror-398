import math

from media_muncher.framerate import FrameRate


class GopSizeCalculator(object):
    def __init__(
        self,
        video_frame_rate: FrameRate,
        audio_sample_rate: int = None,
        audio_frames_per_packet: int = 1024,
    ):
        # Input data
        self.video_frame_rate: FrameRate = video_frame_rate
        self.audio_sample_rate: int = audio_sample_rate
        self.audio_frames_per_packet: int = audio_frames_per_packet

        self.smallest_recommended_gop_size: int = None
        if self.audio_sample_rate is not None:
            self.smallest_recommended_gop_size = self._calculate_compatible_gop_size()

        # If no audio sample rate is provided, the smallest recommended GOP size is the
        # number of frames in about one second of video
        if self.smallest_recommended_gop_size is None:
            self.smallest_recommended_gop_size = round(self.video_frame_rate.fps)

    def _calculate_compatible_gop_size(self):
        """
        Calculate a GOP size compatible between the video frame rate and audio sample rate.
        """

        # Not possible with ATSC frame rates
        if not self.video_frame_rate.is_integer():
            return None

        vrate = int(float(self.video_frame_rate))
        return (
            vrate
            * self.audio_frames_per_packet
            / math.gcd(vrate * self.audio_frames_per_packet, self.audio_sample_rate)
        )

    def for_target_duration(
        self,
        max_duration: float,
        max_frames: int = None,  # Imposes upper limit on the number of frames in the GOP
        return_max_duration_if_no_compatible_gop_size: bool = False,
    ) -> float:
        # Calculate the nearest duration to the target duration that is compatible
        # between video frame rate and audio sample rate

        if self.smallest_recommended_gop_size is None:
            return None, None

        candidate_durations = []
        candidate_num_frames = []
        dur = 0
        i = 1
        selected_duration = None
        selected_num_frames = None

        while dur < 12:  # max reasonable duration in seconds
            dur = self.smallest_recommended_gop_size * i / self.video_frame_rate.fps
            candidate_durations.append(dur)

            num_frames = self.smallest_recommended_gop_size * i
            candidate_num_frames.append(num_frames)

            if max_frames is not None and num_frames > max_frames:
                break

            if dur <= max_duration:
                selected_duration = dur
                selected_num_frames = num_frames
            i += 1

        if return_max_duration_if_no_compatible_gop_size and selected_duration is None:
            return max_duration * self.video_frame_rate.fps, max_duration

        return selected_num_frames, selected_duration
