import math

from media_muncher.framerate import FrameRate
from media_muncher.resolution import Resolution

# MaxMBPS = max macroblocks per second
# MaxFS = max frame size (macroblocks)
# MaxBR = max video bitrate (in kbps)
H264_LEVELS = {
    "1": {"MaxMBPS": 1485, "MaxFS": 99, "MaxBR": 64},
    "1b": {"MaxMBPS": 1485, "MaxFS": 99, "MaxBR": 128},
    "1.1": {"MaxMBPS": 3000, "MaxFS": 396, "MaxBR": 192},
    "1.2": {"MaxMBPS": 6000, "MaxFS": 396, "MaxBR": 384},
    "1.3": {"MaxMBPS": 11880, "MaxFS": 396, "MaxBR": 768},
    "2": {"MaxMBPS": 11880, "MaxFS": 396, "MaxBR": 2000},
    "2.0": {"MaxMBPS": 11880, "MaxFS": 396, "MaxBR": 2000},
    "2.1": {"MaxMBPS": 19800, "MaxFS": 792, "MaxBR": 4000},
    "2.2": {"MaxMBPS": 20250, "MaxFS": 1620, "MaxBR": 4000},
    "3": {"MaxMBPS": 40500, "MaxFS": 1620, "MaxBR": 10000},
    "3.0": {"MaxMBPS": 40500, "MaxFS": 1620, "MaxBR": 10000},
    "3.1": {"MaxMBPS": 108000, "MaxFS": 3600, "MaxBR": 14000},
    "3.2": {"MaxMBPS": 216000, "MaxFS": 5120, "MaxBR": 20000},
    "4": {"MaxMBPS": 245760, "MaxFS": 8192, "MaxBR": 20000},
    "4.0": {"MaxMBPS": 245760, "MaxFS": 8192, "MaxBR": 20000},
    "4.1": {"MaxMBPS": 245760, "MaxFS": 8192, "MaxBR": 50000},
    "4.2": {"MaxMBPS": 522240, "MaxFS": 8704, "MaxBR": 50000},
    "5": {"MaxMBPS": 589824, "MaxFS": 22080, "MaxBR": 135000},
    "5.0": {"MaxMBPS": 589824, "MaxFS": 22080, "MaxBR": 135000},
    "5.1": {"MaxMBPS": 983040, "MaxFS": 36864, "MaxBR": 240000},
    "5.2": {"MaxMBPS": 2073600, "MaxFS": 36864, "MaxBR": 240000},
}


class H264LevelValidator:
    def __init__(self, level: str):
        if level not in H264_LEVELS:
            raise ValueError(f"Level {level} is not recognized.")
        self.level = level
        self.constraints = H264_LEVELS[level]
        self.messages = []

    @staticmethod
    def calculate_macroblocks_per_frame(resolution: Resolution) -> int:
        # Calculate Macroblocks per Frame
        mb_width = math.ceil(resolution.width / 16)
        mb_height = math.ceil(resolution.height / 16)
        return mb_width * mb_height

    def validate_frame_size(self, resolution: Resolution) -> bool:
        mbpf = self.calculate_macroblocks_per_frame(resolution)
        max_fs = self.constraints["MaxFS"]
        if mbpf > max_fs:
            self.messages.append(
                f"Invalid: Macroblocks per frame ({mbpf}) exceed MaxFS ({max_fs}) for level {self.level}."
            )
            return False
        return True

    def validate_macroblocks_per_second(
        self, resolution: Resolution, framerate: FrameRate
    ) -> bool:
        mbpf = self.calculate_macroblocks_per_frame(resolution)
        mbps = mbpf * framerate.fps
        max_mbps = self.constraints["MaxMBPS"]
        if mbps > max_mbps:
            self.messages.append(
                f"Invalid: Macroblocks per second ({mbps}) exceed MaxMBPS ({max_mbps}) for level {self.level}."
            )
            return False
        return True

    def validate_bitrate(self, bitrate: float) -> bool:
        bitrate_kbps = bitrate / 1000
        max_br = self.constraints["MaxBR"]  # Convert MaxBR to bps
        if bitrate_kbps > max_br:
            self.messages.append(
                f"Invalid: Bitrate ({bitrate_kbps} kbps) exceeds MaxBR ({max_br} kbps) for level {self.level}."
            )
            return False
        return True

    def validate(
        self, resolution: Resolution, framerate: FrameRate, bitrate: int
    ) -> bool:
        self.messages = []

        is_valid = True
        is_valid &= self.validate_frame_size(resolution)
        is_valid &= self.validate_macroblocks_per_second(resolution, framerate)
        is_valid &= self.validate_bitrate(bitrate)

        return is_valid

    def adjust_resolution(self, resolution: Resolution) -> Resolution:
        max_fs = self.constraints["MaxFS"]

        adjusted_resolution = resolution
        while True:
            mbpf = self.calculate_macroblocks_per_frame(adjusted_resolution)

            if mbpf <= max_fs:
                break

            scaling_factor = math.sqrt(max_fs / mbpf)
            new_width = int(adjusted_resolution.width * scaling_factor) // 2 * 2
            new_height = int(adjusted_resolution.height * scaling_factor) // 2 * 2
            adjusted_resolution = Resolution(width=new_width, height=new_height)
            self.messages.append(
                f"Adjusted resolution to {new_width}x{new_height} to meet MaxFS constraint."
            )

        return adjusted_resolution

    def adjust_bitrate(self, bitrate: int) -> int:
        max_br = self.constraints["MaxBR"]
        if bitrate / 1000 > max_br:
            self.messages.append(
                f"Adjusted bitrate to {max_br * 1000} bps to meet MaxBR constraint."
            )
        return min(bitrate, max_br * 1000)

    def adjust(self, resolution: Resolution, framerate: FrameRate, bitrate: int):
        """
        Handles validation and adjustment of resolution, framerate and bitrate based on H.264 level specifications.
        """
        # Validate first
        is_valid = self.validate(resolution, framerate, bitrate)
        if is_valid:
            return resolution, framerate, bitrate

        # Adjust resolution first to meet MaxFS
        adjusted_resolution = self.adjust_resolution(resolution)

        # Handle MaxMBPS constraint
        while True:
            # Calculate mbpf and mbps with adjusted resolution
            mbpf = self.calculate_macroblocks_per_frame(adjusted_resolution)
            mbps = mbpf * framerate.fps
            max_mbps = self.constraints["MaxMBPS"]

            if mbps <= max_mbps:
                break

            self.messages.append(
                f"Cannot meet MaxMBPS constraint ({max_mbps}) with adjusted resolution and given framerate."
            )
            # Since we prefer to keep the framerate constant, we might need to adjust resolution further
            # Adjust resolution again to meet MaxMBPS
            scaling_factor = math.sqrt((max_mbps / framerate.fps) / mbpf)
            new_width = int(adjusted_resolution.width * scaling_factor) // 2 * 2
            new_height = int(adjusted_resolution.height * scaling_factor) // 2 * 2
            adjusted_resolution = Resolution(width=new_width, height=new_height)
            self.messages.append(
                f"Further adjusted resolution to {new_width}x{new_height} to meet MaxMBPS constraint."
            )

        # Adjust bitrate
        adjusted_bitrate = self.adjust_bitrate(bitrate)

        return adjusted_resolution, framerate, adjusted_bitrate
