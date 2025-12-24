from typing import Dict, List

from lxml import etree
from media_muncher.exceptions import MediaHandlerError
from media_muncher.handlers.vast import VASTHandler

from .xml import XMLHandler


class VMAPHandler(XMLHandler):
    content_types = []
    file_extensions = [".vmap"]

    uri_elements = ["vmap:AdTagURI"]

    def __init__(self, url, content: bytes | None = None, **kwargs):
        super().__init__(url, content, **kwargs)
        self._document: etree._Element = None

    @property
    def document(self) -> etree._Element:
        if self._document is None:
            self._document = etree.fromstring(self.content)
        return self._document

    def read(self):
        return "Handling VMAP file."

    @staticmethod
    def is_supported_content(content):
        try:
            root = etree.fromstring(content)
            if root.tag in [
                "{http://www.iab.net/videosuite/vmap}VMAP",
                "{http://www.iab.net/vmap-1.0}VMAP",
            ]:
                return True
        except etree.XMLSyntaxError:
            pass
        return False

    def has_children(self) -> bool:
        return len(self.extract_features()) > 0

    def get_child(self, index: int, **kwargs) -> "VASTHandler":
        features = self.extract_features()
        try:
            return VASTHandler(
                url=features[index - 1]["AdTagURI"], headers=self.headers
            )
        except IndexError as e:
            raise MediaHandlerError(
                message=f"The VMAP only has {len(features)} ad breaks.",
                original_message=e.args[0],
            )

    def extract_features(self) -> List[Dict]:
        ad_breaks = []

        # Extract the timeOffset, breakId, and AdTagURI
        for ad_break in self.document.xpath("//*[local-name() = 'AdBreak']"):
            nsmap = ad_break.nsmap
            time_offset = ad_break.get("timeOffset")
            break_id = ad_break.get("breakId")
            ad_tag_uri = ad_break.findtext(
                "vmap:AdSource/vmap:AdTagURI", namespaces=nsmap
            ).strip()

            ad_breaks.append(
                {"timeOffset": time_offset, "breakId": break_id, "AdTagURI": ad_tag_uri}
            )

        return ad_breaks
