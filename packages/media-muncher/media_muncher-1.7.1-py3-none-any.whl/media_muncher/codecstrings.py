from typing import Dict, List


class CodecStringParser:
    @staticmethod
    def parse_multi_codec_string(string: str) -> List[Dict]:
        if (
            string.startswith(('"', "'"))
            and string.endswith(('"', "'"))
            and len(string) > 1
        ):
            string = string[1:-1]

        codecstrings = [c.strip() for c in string.split(",")]
        out = []
        for c in codecstrings:
            cinfo = CodecStringParser.parse_codec_string(c)
            out.append(cinfo)

        return out

    @staticmethod
    def parse_codec_string(codecstring: str) -> Dict:
        (codec, *codec_data) = codecstring.split(".")
        codec_info = None

        match codec:
            case "avc1" | "avc3":
                # Treatment of legacy codec strings
                if len(codec_data) == 2:
                    codec_info = CodecStringParser._parse_avc(
                        f"{codec_data[0]}.{codec_data[1]}", legacy=True
                    )
                else:
                    codec_info = CodecStringParser._parse_avc(codec_data[0])
            case "hvc1" | "hev1":
                codec_info = CodecStringParser._parse_hvc(codec_data)
            case "mp4a":
                codec_info = CodecStringParser._parse_aac(codec_data)
            case "ac-3":
                codec_info = CodecStringParser._parse_ac3()
            case _:
                raise Exception(f"Codec '{codec}' invalid or not yet implemented")

        codec_info["codecstring"] = codecstring
        return codec_info

    @staticmethod
    def _parse_avc(codec_data, legacy=False):
        H264ProfileLegacy = {"66": "Baseline", "77": "Main", "100": "High"}
        H264ProfileRFC6381 = {
            "42": "Baseline",
            "4D": "Main",
            "58": "Extended",
            "64": "High",
            "6E": "High 10",
            "7A": "High 4:2:2",
            "F4": "High 4:4:4",
            "2C": "CAVLC 4:4:4",
        }
        H264LevelRFC6381 = {
            "0A": "1",
            "0B": "1.1",
            "0C": "1.2",
            "0D": "1.3",
            "14": "2",
            "15": "2.1",
            "16": "2.2",
            "1E": "3",
            "1F": "3.1",
            "20": "3.2",
            "28": "4",
            "29": "4.1",
            "2A": "4.2",
            "32": "5",
            "33": "5.1",
            "34": "5.2",
            "3C": "6",
            "3D": "6.1",
            "3F": "6.2",
        }

        try:
            if legacy:
                profile, level = codec_data.split(".")
                pro = H264ProfileLegacy[profile]
                lev = f"{level[0]}.{level[1]}"
            else:
                profile, level = codec_data[:2].upper(), codec_data[4:6].upper()
                pro = H264ProfileRFC6381[profile]
                lev = H264LevelRFC6381[level]

            return dict(
                cc="H264",
                type="video",
                codec="AVC/H.264",
                profile=pro,
                level=lev,
            )
        except Exception:
            raise Exception(f"Invalid or unsupported H264 codec data: {codec_data}")

    @staticmethod
    def _parse_aac(codec_data):
        oti, mode = codec_data

        AAC_OTI = {
            "40": "MPEG-4 AAC",
            "66": "MPEG-2 AAC Main Profile",
            "67": "MPEG-2 AAC LC",
            "68": "MPEG-2 AAC Scalable Sampling Rate Profile",
            "69": "MPEG-2 Audio Part 3",
            "6B": "MPEG-1 Part 3",
        }
        AAC_MODE = {
            "1": "Main",
            "2": "AAC LC",
            "5": "HE-AAC v1 (AAC LC + SBR)",
            "29": "HE-AAC v2 (AAC LC + SBR + PS)",
        }

        try:
            return dict(
                cc="AAC", type="audio", codec=AAC_OTI[oti.upper()], mode=AAC_MODE[mode]
            )
        except Exception:
            raise Exception(f"Invalid or unsupported AAC codec data: {codec_data}")

    @staticmethod
    def _parse_ac3():
        return dict(cc="AC3", type="audio", codec="AC-3")

    @staticmethod
    def _parse_hvc(codec_data):
        HEVCProfiles = {
            "1": "Main",
            "2": "Main 10",
            "3": "Main Still Picture",
            "4": "Range Extensions",
            "5": "High Throughput",
            "6": "High Throughput 10",
        }
        HEVCTiers = {"L": "Main", "H": "High"}
        HEVCLevels = {
            "30": "1",
            "60": "2",
            "63": "2.1",
            "90": "3",
            "93": "3.1",
            "120": "4",
            "123": "4.1",
            "150": "5",
            "153": "5.1",
            "156": "5.2",
            "180": "6",
            "183": "6.1",
            "186": "6.2",
        }
        try:
            profile_space, profile, tier_info, constraints = codec_data
            pro = HEVCProfiles[profile]
            ti = HEVCTiers[tier_info[0].upper()]
            lev = HEVCLevels[tier_info[1:]]
            return dict(cc="HEVC", type="video", codec="H.265/HEVC", profile=pro, level=lev, tier=ti)
        except Exception:
            return dict(cc="HEVC", type="video", codec="H.265/HEVC")
