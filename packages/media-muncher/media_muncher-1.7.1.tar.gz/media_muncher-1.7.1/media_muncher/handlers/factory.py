import importlib
import pkgutil

import requests
from loguru import logger
from media_muncher.exceptions import MediaHandlerError
from media_muncher.format import MediaFormat

from .generic import ContentHandler, ContentHandlerMeta

USER_AGENT_FOR_HANDLERS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"

# Timeout for HEAD
TIMEOUT = 2


def _import_all_handlers():
    """
    Dynamically imports all submodules in the handlers package to ensure that all handler classes are registered.
    """
    import media_muncher.handlers  # Adjust the import path based on your project structure
    handlers_package = media_muncher.handlers

    for _, module_name, is_pkg in pkgutil.iter_modules(handlers_package.__path__):
        if not is_pkg:
            importlib.import_module(f"{handlers_package.__name__}.{module_name}")
            logger.debug(f"Imported handler module: {module_name}")


# Registry for subclasses
_direct_registry = {}

def _populate_registry():
    global _direct_registry
    if _direct_registry:
        return

    # Populate registry for supported handlers
    for handler_cls in ContentHandlerMeta.registry:
        if hasattr(handler_cls, "media_format"):
            _direct_registry[handler_cls.media_format] = handler_cls
        if hasattr(handler_cls, "content_types"):
            for content_type in handler_cls.content_types:
                _direct_registry[content_type] = handler_cls
        if hasattr(handler_cls, "file_extensions"):
            for extension in handler_cls.file_extensions:
                _direct_registry[extension] = handler_cls


def create_handler(
    url,
    get_full_content=False,
    from_url_only=False,
    user_agent=None,
    explicit_headers=[],
):
    # First we ensure all handlers are imported and registered
    # this is only done once, as Python imports are idempotent
    _import_all_handlers()
    _populate_registry()

    url = str(url).strip()
    headers = {"User-Agent": user_agent or USER_AGENT_FOR_HANDLERS}

    if explicit_headers:
        for additional_header in explicit_headers:
            try:
                key, value = additional_header.split("=", 1)
            except ValueError:
                key, value = additional_header.split(":", 1)
            headers[key] = value.strip()

    try:
        # Extract content-type
        content_type = ""
        if not from_url_only:
            try:
                response = requests.head(
                    url,
                    allow_redirects=True,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=ContentHandler.verify_ssl,
                )
                content_type = response.headers.get("content-type")
            except requests.exceptions.Timeout:
                logger.debug(f"HTTP HEAD takes more than {TIMEOUT} seconds, skipping.")
                content_type = "Unknown"

        # Extract extension
        media_format = MediaFormat.guess_from_url(url)

        # Determine appropriate handler from content-type or media-format
        handler_cls = _direct_registry.get(content_type) or _direct_registry.get(media_format)

        # Otherwise, fallback to content analysis
        content = None
        if handler_cls is None:
            if from_url_only:
                raise ValueError(
                    "No information available in the URL to determine content type: "
                    f"{content_type} / {media_format}"
                )

            content = ContentHandler.fetch_content_with_size_limit(
                url=url,
                size_limit=200 * 1024,
                headers=headers,
                enforce_limit=(not get_full_content),
                timeout=TIMEOUT,
            )

            # Fallback: analyze content if handler is not found by content-type
            # or file extension
            candidate_handlers = []
            if content:
                for handler in ContentHandlerMeta.registry:
                    if handler.is_supported_content(content):                        
                        candidate_handlers.append(handler)
            
            # Choose the most specific one (based on inheritance)
            if candidate_handlers:
                handler_cls = max(candidate_handlers, key=lambda x: x.__mro__.index(ContentHandler))

        if handler_cls is None:
            raise ValueError(
                "Could not determine content type from content-type, file extension, or content of URL: "
                f"- TYPE: {content_type} \n- FORMAT: {media_format} \n- CONTENT: {content}"
            )

        return handler_cls(url, content, headers=headers)

    except Exception as e:
        raise MediaHandlerError(
            message=f"Unable to determine a usable handler for url {url}",
            original_message=(
                e.args[0] if len(e.args) else getattr(e, "description", None)
            ),
        )
