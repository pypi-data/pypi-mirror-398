import logging
from typing import IO, Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)


class ProtectedFileSystemStorage(FileSystemStorage):
    """
    Custom storage class for protected files.

    Overrides location and base_url with the custom settings.
    """

    def __init__(self, *args, **kwargs):
        kwargs["location"] = settings.PROTECTED_MEDIA_ROOT
        kwargs["base_url"] = settings.PROTECTED_MEDIA_URL
        super().__init__(*args, **kwargs)

    def get_valid_name(self, name):
        return super().get_valid_name(name)

    def save(self, name: str | None, content: IO[Any], max_length: int | None = None):
        content_length = (
            getattr(content, "size", None) if hasattr(content, "size") else "unknown"
        )
        logger.debug(
            f"ProtectedFileSystemStorage: Saving file: {name} with content length: "
            f"{content_length} bytes"
        )
        return super().save(name, content, max_length)

    def path(self, name):
        # Check if the full path is correct
        logger.debug(f"ProtectedFileSystemStorage: Path requested: {name}")
        return super().path(name)
