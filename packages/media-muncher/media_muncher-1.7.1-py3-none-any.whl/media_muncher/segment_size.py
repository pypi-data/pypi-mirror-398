import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

from media_muncher.framerate import FrameRate
from media_muncher.gop_size import GopSizeCalculator


@dataclass
class SegmentSizer:
    """
    Represents the optimal segment size for video packaging based on target duration and frame rate.
    """

    # Public Attributes (Configurations)
    denominator_start: int = 1000
    denominator_end: int = 10000
    step: int = 1000
    target_duration: float = None

    # Calculated Attributes
    num_frames: int = field(init=False, default=0)
    actual_duration: float = field(init=False, default=0.0)
    difference: float = field(init=False, default=float("inf"))
    numerator: int = field(init=False, default=0)
    denominator: int = field(init=False, default=1)
    optimal_denominator: int = field(init=False, default=0)
    optimal_numerator: int = field(init=False, default=1)

    # Private Internal Fields
    _framerate: FrameRate = field(init=False, repr=False)
    _samplerate: int = None

    def __init__(self, framerate: FrameRate, samplerate: Optional[int] = None):
        """
        Initializes the SegmentSize object with reference frame rate.
        """
        self._framerate = framerate
        self._samplerate = samplerate

    @property
    def framerate(self) -> FrameRate:
        """
        Gets the reference frame rate.
        """
        return self._framerate

    @framerate.setter
    def framerate(self, value: FrameRate):
        """
        Sets the reference frame rate and recalculates the optimal segment.
        """
        if (
            value.numerator != self._framerate.numerator
            or value.denominator != self._framerate.denominator
        ):
            self._framerate = value

            # recalculate the optimal segment
            if self.target_duration:
                self._calculate_optimal_segment()

    @property
    def samplerate(self) -> int:
        """
        Gets the reference audio sample rate.
        """
        return self._samplerate

    @samplerate.setter
    def samplerate(self, value: int):
        """
        Sets the reference audio sample rate and recalculates the optimal segment.
        """
        if value != self._samplerate:
            self._samplerate = value

            # recalculate the optimal segment
            if self.target_duration:
                self._calculate_optimal_segment()

    @property
    def fraction(self) -> str:
        """
        Returns the fraction representation of the segment duration.
        """
        return f"{self.optimal_numerator}/{self.optimal_denominator}"

    @property
    def simplified_fraction(self) -> str:
        """
        Returns the simplified fraction representation of the segment duration.
        """
        return f"{self.numerator}/{self.denominator}"

    def to_obj(self) -> dict:
        """
        Returns a dictionary representation of the segment size properties.
        """
        return {
            "num": self.numerator,
            "den": self.denominator,
        }

    def set_target_duration(self, value: float, ignore_audio: bool = False):
        """
        Sets the target segment duration and calculates the optimal segment. This is the main function to trigger calculation
        """
        self.target_duration = value

        # if an audio sample rate was provided, we use it to find a compatible duration first
        if ignore_audio is False and self.samplerate is not None:
            num_frames, matching_duration = GopSizeCalculator(
                video_frame_rate=self.framerate,
                audio_sample_rate=self.samplerate,
            ).for_target_duration(value)
            if matching_duration is not None:
                self.target_duration = matching_duration

        self._calculate_optimal_segment()
        return self

    def _calculate_optimal_segment(self):
        """
        Calculates the optimal number of frames and denominator that minimizes the difference
        between the actual segment duration and the target duration.

        The method performs the following steps:
            1. Resets previous calculation results.
            2. Computes the actual frame rate and frame duration.
            3. Determines the ideal (non-integer) number of frames for the target duration.
            4. Iterates through a range of denominators to find the optimal combination.
            5. For each denominator:
                a. Calculates the Greatest Common Divisor (GCD) between (frame_rate_denominator * D) and frame_rate_numerator.
                b. Determines the required multiple for the number of frames.
                c. Calculates the nearest multiple to the ideal number of frames.
                d. Validates that the number of frames is positive and that 'k' is an integer.
                e. Computes the actual segment duration based on 'k' and 'D'.
                f. Calculates the difference between the actual and target durations.
                g. Updates the optimal segment details if a smaller difference is found.
                h. Breaks early if an exact match is achieved.
        """
        # Reset previous calculations
        self.num_frames = 0
        self.actual_duration = 0.0
        self.difference = float("inf")
        self.numerator = 0
        self.denominator = 1
        self.optimal_denominator = 0
        self.optimal_numerator = 1

        # Calculate frame rate and frame duration
        frame_rate_value = self.framerate.numerator / self.framerate.denominator
        frame_duration = self.framerate.denominator / self.framerate.numerator

        # Calculate ideal number of frames
        N_ideal = self.target_duration * frame_rate_value

        # Iterate through the desired denominator range
        for D in range(self.denominator_start, self.denominator_end + 1, self.step):
            # Calculate GCD to find the required multiple for N
            gcd_val = math.gcd(self.framerate.denominator * D, self.framerate.numerator)
            multiple = self.framerate.numerator // gcd_val

            # Find the nearest multiple to N_ideal
            N_candidate = multiple * round(N_ideal / multiple)

            if N_candidate <= 0:
                continue  # Skip invalid frame counts

            # Compute k
            numerator_k = self.framerate.denominator * N_candidate * D
            denominator_k = self.framerate.numerator

            if numerator_k % denominator_k != 0:
                continue  # k must be an integer

            k = numerator_k // denominator_k

            # Compute actual segment duration
            T = k / D

            # Compute difference from target
            diff = abs(T - self.target_duration)

            # Update optimal result if this is better
            if diff < self.difference:
                simplified_fraction = Fraction(k, D).limit_denominator()
                self.optimal_numerator = k
                self.optimal_denominator = D
                self.num_frames = N_candidate
                self.actual_duration = T
                self.numerator = simplified_fraction.numerator
                self.denominator = simplified_fraction.denominator
                self.difference = diff

                # Early exit if exact match is found
                if diff == 0:
                    break

    def compute_gop_size(self, target_duration: float) -> int:
        """
        Computes the GOP size nearest to the target duration,
        but such that the segment size contains a whole number of frames.
        """

        # Find divisors of the total number of frames
        divisors = [
            i for i in range(1, self.num_frames + 1) if self.num_frames % i == 0
        ]

        # For each divisor, calculate the corresponding GOP duration and determine how close it is to the target duration
        candidates = []
        for divisor in divisors:
            gop_duration = 1 / self.framerate.fps * divisor
            delta = abs(gop_duration - target_duration)
            candidates.append((divisor, gop_duration, delta))

        # Sort candidates by delta
        candidates.sort(key=lambda x: x[2])

        # Return the first candidate
        return candidates[0][0]
