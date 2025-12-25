import os

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class FileFetcher(BaseFetcher):
    """
    Concrete implementation of BaseFetcher for local file systems.

    This fetcher reads binary data directly from the path specified in `task.uri`.
    It handles basic file I/O operations and raises wrapped exceptions if the file
    is inaccessible or missing.
    """

    component_name = "FileFetcher"
    SUPPORTED_TYPES = ["file"]

    def _do_fetch(self, task: SayouTask) -> bytes:
        """
        Read a file from the local file system.

        Args:
            task (SayouTask): The task containing the file path in `task.uri`.

        Returns:
            bytes: The raw binary content of the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be read.
        """
        file_path = task.uri

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            return f.read()
