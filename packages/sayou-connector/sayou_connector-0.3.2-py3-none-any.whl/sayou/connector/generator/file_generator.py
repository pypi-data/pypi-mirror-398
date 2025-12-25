import fnmatch
import os
from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class FileGenerator(BaseGenerator):
    """
    Concrete implementation of BaseGenerator for file system traversal.

    Scans a directory tree starting from a source path. It yields `SayouTask`s
    for files that match specific criteria, such as file extensions or name patterns.
    Supports both recursive and flat directory scanning.
    """

    component_name = "FileGenerator"
    SUPPORTED_TYPES = ["file"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        """
        Evaluates whether this generator can handle the given source.

        Analyzes the source string to determine if it matches the pattern or format
        supported by this generator. Returns a confidence score between 0.0 and 1.0.

        Args:
            source (str): The input source string to evaluate.

        Returns:
            float: A confidence score where 1.0 means full confidence,
                    0.0 means the source is incompatible, and intermediate values
                    indicate partial matches or heuristics.
        """
        if os.path.exists(source):
            return 1.0
        if source.startswith("/") or source.startswith("./") or ":\\" in source:
            return 0.8
        return 0.0

    def initialize(
        self,
        source: str,
        recursive: bool = True,
        extensions: list = None,
        name_pattern: str = "*",
        **kwargs
    ):
        """
        Configure the file scanning strategy.

        Args:
            source (str): The root directory or file path to start scanning.
            recursive (bool): If True, scan subdirectories recursively.
            extensions (Optional[List[str]]): List of allowed extensions (e.g., ['.pdf', '.txt']).
            name_pattern (str): Glob pattern for filename matching (e.g., '*report*').
            **kwargs: Ignored additional arguments.
        """
        self.root_path = os.path.abspath(source)
        self.recursive = recursive
        self.extensions = [e.lower() for e in extensions] if extensions else None
        self.name_pattern = name_pattern

    def _do_generate(self) -> Iterator[SayouTask]:
        """
        Walk through the file system and yield tasks for valid files.

        Yields:
            Iterator[SayouTask]: Tasks with `source_type='file'`.
        """
        if os.path.isfile(self.root_path):
            if self._is_valid(self.root_path):
                yield self._create_task(self.root_path)
            return

        walker = (
            os.walk(self.root_path)
            if self.recursive
            else [(self.root_path, [], os.listdir(self.root_path))]
        )

        for root, _, files in walker:
            for file in files:
                full_path = os.path.join(root, file)
                if self._is_valid(file):
                    yield self._create_task(full_path)

    def _is_valid(self, filename: str) -> bool:
        """
        Check if a file matches the extension and name pattern criteria.

        Args:
            filename (str): The name of the file to check.

        Returns:
            bool: True if the file should be processed, False otherwise.
        """
        if not fnmatch.fnmatch(filename, self.name_pattern):
            return False
        if (
            self.extensions
            and os.path.splitext(filename)[1].lower() not in self.extensions
        ):
            return False
        return True

    def _create_task(self, path: str) -> SayouTask:
        """
        Create a SayouTask for a valid file path.

        Args:
            path (str): The absolute path to the file.

        Returns:
            SayouTask: The configured task object.
        """
        return SayouTask(
            source_type="file", uri=path, meta={"filename": os.path.basename(path)}
        )
