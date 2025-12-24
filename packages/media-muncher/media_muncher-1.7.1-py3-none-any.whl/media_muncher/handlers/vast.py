from typing import Dict, List

from lxml import etree

from .xml import XMLHandler


class VASTHandler(XMLHandler):
    content_types = []
    file_extensions = [".vast"]

    uri_elements = ["MediaFile"]

    def __init__(self, url, content: bytes | None = None, **kwargs):
        super().__init__(url, content, **kwargs)
        self._document: etree._Element = None

    @property
    def document(self) -> etree._Element:
        if not self._document:
            self._document = etree.fromstring(self.content)
        return self._document

    def read(self):
        return "Handling VAST file."

    @staticmethod
    def is_supported_content(content):
        try:
            root = etree.fromstring(content)
            if root.tag == "VAST":
                return True
        except etree.XMLSyntaxError:
            pass
        return False

    def extract_features(self) -> List[Dict]:
        ads = []

        # Extract the ad information
        for ad in self.document.xpath("//Ad"):
            ad_id = ad.get("id")
            sequence = ad.get("sequence")
            ad_title = ad.findtext(".//AdTitle")
            duration = ad.findtext(".//Duration")
            creative_adid = ad.xpath(".//Creative")[0].get("AdID")
            creative_id = ad.xpath(".//Creative")[0].get("id")

            media_files = []
            for media_file in ad.xpath(".//MediaFile"):
                media_url = media_file.text.strip()
                media_type = media_file.get("type")
                media_files.append("{}  [{}]".format(media_url, media_type))

            ads.append(
                {
                    "Ad@id": ad_id,
                    "Ad@sequence": sequence,
                    "AdTitle": ad_title,
                    "Creative@AdId": creative_adid,
                    "Creative@id": creative_id,
                    "Duration": duration,
                    "MediaFiles": "\n".join(media_files),
                }
            )

        return ads
