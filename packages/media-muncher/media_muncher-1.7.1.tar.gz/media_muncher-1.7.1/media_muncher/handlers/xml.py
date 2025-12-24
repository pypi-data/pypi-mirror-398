from abc import abstractmethod

from lxml import etree

from .generic import ContentHandler


class XMLHandler(ContentHandler):
    content_types = []

    uri_attributes = []
    uri_elements = []

    def __init__(self, url, content: bytes | None = None, **kwargs):
        super().__init__(url, content, **kwargs)

    def read(self):
        return "Handling XML file."

    @property
    def document(self) -> etree._Element:
        if not self._document:
            self._document = etree.fromstring(self.content)
        return self._document

    @property
    def xml_document(self) -> etree._Element:
        return self.document

    @staticmethod
    def is_supported_content(content) -> bool:
        try:
            etree.fromstring(content)
            return True
        except etree.XMLSyntaxError:
            return False
