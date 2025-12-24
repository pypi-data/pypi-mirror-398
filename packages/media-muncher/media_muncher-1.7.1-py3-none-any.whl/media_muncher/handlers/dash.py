import os
from datetime import datetime, timedelta
from typing import Callable, Dict, List

from loguru import logger
from lxml import etree
from mpd_inspector import MPDInspector, MPDParser
from mpd_inspector.parser.mpd_tags import MPD, PresentationType

from media_muncher.format import MediaFormat

from .xml import XMLHandler


class DASHHandler(XMLHandler):
    media_format = MediaFormat.DASH
    content_types = ["application/dash+xml"]

    uri_attributes = ["initialization", "media"]
    uri_elements = ["BaseURL"]

    def __init__(self, url, content: bytes | None = None, **kwargs):
        super().__init__(url, content, **kwargs)
        self._document: MPD = None

    @property
    def document(self) -> MPD:
        if not self._document:
            try:
                self._document = MPDParser.from_string(self.content.decode())
            except Exception as e:
                logger.error(f"Error parsing DASH document: {e}")
                raise e
        return self._document
        # return Parser.from_string(self.content.decode())

    @property
    def xml_document(self) -> etree._Element:
        return etree.fromstring(self.content)

    @property
    def inspector(self) -> MPDInspector:
        return MPDInspector(self.document)

    def read(self):
        return "Handling DASH file."

    @staticmethod
    def is_supported_content(content):
        try:
            root = etree.fromstring(content)
            if root.tag == "{urn:mpeg:dash:schema:mpd:2011}MPD":
                return True
        except etree.XMLSyntaxError as e:
            logger.error(f"Error parsing DASH document: {e}")
            pass
        return False

    def is_live(self):
        if self.document.type == PresentationType.DYNAMIC:
            return True
        else:
            return False

    def get_duration(self) -> float:
        """Extract duration from the MPD if it's for a VOD

        Returns:
            float: duration in seconds
        """
        if self.is_live():
            return -1
        else:
            return self.document.media_presentation_duration.total_seconds()

    def first_segment_url(self) -> str | None:
        urls = (
            self.inspector.periods[0]
            .adaptation_sets[0]
            .representations[0]
            .segment_information.full_urls("media")
        )
        if urls:
            return urls[0]

    def extract_info(self) -> Dict:
        info = {
            "format": "DASH",
            "type": "Live (dynamic)" if self.is_live() else "VOD (static)",
            "duration (in sec)": "N/A" if self.is_live() else self.get_duration(),
        }

        return info

    def extract_timeline(self):
        timeline = []

        for i, period in enumerate(self.inspector.periods):
            duration = period.duration
            if not duration and len(self.inspector.periods) > i + 1:
                duration = calculate_effective_duration(
                    period.start, self.inspector.periods[i + 1].start
                )

            info = {
                "period": period.id,
                "start": period_start_time(
                    self.document.availability_start_time, period.start
                ),
                "duration": duration,
                "baseUrl": period.base_urls[0].text if len(period.base_urls) else "",
            }
            timeline.append(info)

        return timeline

    def extract_features(self) -> List[Dict] | None:
        features = []

        for period in self.document.periods:
            for adaptation_set in period.adaptation_sets:
                for representation in adaptation_set.representations:
                    res = (
                        "{} x {}".format(
                            representation.width,
                            representation.height,
                        )
                        if representation.width
                        else ""
                    )

                    features.append(
                        {
                            "period": period.id,
                            "adaptation_set": adaptation_set.id,
                            "type": adaptation_set.content_type,
                            "bandwidth": representation.bandwidth,
                            "codecs": representation.codecs or adaptation_set.codecs,
                            "resolution": res,
                            "language": adaptation_set.lang,
                        }
                    )

        return features

    def get_update_interval(self) -> int | None:
        updateInterval = self.document.minimum_update_period
        return float(updateInterval.replace("PT", "").replace("S", ""))

    def download(
        self,
        output_path: str,
        num_segments: int,
        progress_callback: Callable[[str, int], None] | None = None,
    ):
        # Create the output path if it doesn't exist
        if output_path and not os.path.exists(output_path):
            os.makedirs(output_path)

        if num_segments > 0:
            raise NotImplementedError(
                "Downloading segments is not yet implemented for DASH"
            )

        # TODO - download segments
        total_tasks = 1
        if progress_callback:
            progress_callback(
                f"Number of files to download: {total_tasks}", total=total_tasks
            )

        main_filename = "main.mpd"
        local_file_path = os.path.join(output_path, main_filename)
        with open(local_file_path, "wb") as f:
            f.write(self.content)

        message = f"Downloaded MPD manifest to {local_file_path}"
        logger.info(message)
        if progress_callback:
            progress_callback(message)


def period_start_time(availability_start_time: str, start: str) -> str:
    if availability_start_time:
        availability_start_time_dt = datetime.fromisoformat(
            availability_start_time.replace("Z", "+00:00")
        )
        start_duration = float(start.replace("PT", "").replace("S", ""))
        start_time_dt = availability_start_time_dt + timedelta(seconds=start_duration)
        return start_time_dt.strftime("%Y-%m-%d %H:%M:%S")


def calculate_effective_duration(start_time, next_start_time):
    current_start = float(start_time.replace("PT", "").replace("S", ""))
    next_start = float(next_start_time.replace("PT", "").replace("S", ""))
    return next_start - current_start
