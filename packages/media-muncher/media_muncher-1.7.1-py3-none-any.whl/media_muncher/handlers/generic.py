from abc import ABC, abstractmethod
from importlib.metadata import version
from typing import Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import requests
from loguru import logger

from media_muncher.exceptions import MediaHandlerError

__version__ = version("media-muncher")
api_client = f"media-muncher/{__version__}"
# TODO: ensure that the bpkio-api can add its own api_client to the string sent


class ContentHandlerMeta(type):
    registry = []

    def __new__(cls, name, bases, attrs):
        new_cls = super().__new__(cls, name, bases, attrs)
        ContentHandlerMeta.registry.append(new_cls)
        return new_cls


class ContentHandler(metaclass=ContentHandlerMeta):
    content_types = []
    verify_ssl = True
    api_client = api_client

    _document = None
    document = None

    status = None

    @abstractmethod
    def __init__(
        self,
        url,
        content: Optional[bytes],
        headers: Optional[Dict] = {},
    ):
        if not headers:
            headers = {}

        self.url = url
        self.original_url = url
        self.headers = headers

        self.headers["x-api-client"] = self.api_client

        if content:
            self._content = content
        else:
            self._content = None

        # broadpeak session id (in case handler is for a bpk service)
        self.session_id = None
        self.service_id = None

    @property
    def content(self):
        if self._content is None:
            self._fetch_content()
        return self._content

    def _fetch_content(self) -> bytes:
        logger.debug(f"Fetching content from {self.url} with headers {self.headers}")

        response = requests.get(self.url, headers=self.headers, verify=self.verify_ssl)
        self.status = response.status_code
        self._content = response.content
        # clear the document, to force a reload
        self._document = None

        # overwrite the URL, in case of redirect
        self.url = response.url

        # check if a broadpeak.io session was started
        params = parse_qs(
            urlparse(self.url).query, keep_blank_values=True, strict_parsing=False
        )
        if "bpkio_sessionid" in params:
            self.session_id = params["bpkio_sessionid"][0]
            if "bpkio_serviceid" in params:
                self.service_id = params["bpkio_serviceid"][0]

            # with open(".last_session", "w") as f:
            #     f.write(self.session_id)
            #     f.write("\n")
            #     f.write(str(self.service_id))

        return self._content

    @staticmethod
    def fetch_content_with_size_limit(
        url, size_limit, headers, enforce_limit=True, timeout=5
    ):
        response = requests.get(
            url, stream=True, headers=headers, verify=ContentHandler.verify_ssl
        )  # , timeout=timeout)
        if response.status_code != 200:
            raise MediaHandlerError(
                message="Unable to fetch content - "
                + f"server response {response.status_code} for url {url}",
                original_message="",
            )

        content = b""
        for chunk in response.iter_content(chunk_size=1024):
            content += chunk
            if len(content) > size_limit:
                raise MediaHandlerError("Content too long to be parseable efficiently")
        return content

    def reload(self):
        self._fetch_content()

    @staticmethod
    @abstractmethod
    def is_supported_content(content) -> bool:
        pass

    def has_children(self) -> bool:
        return False

    def get_child(self, index: int, **kwargs) -> "ContentHandler | None":
        return None

    def num_children(self) -> int:
        return 0

    @abstractmethod
    def read(self):
        pass

    def extract_info(self) -> Dict | None:
        return None

    def extract_features(self) -> List[Dict] | None:
        return None

    def get_update_interval(self) -> int | None:
        return None

    def download(self, output_path: str, num_segments: int, progress_callback: Callable[[str, int], None] | None = None):
        raise NotImplementedError("Download is not implemented for this format")
