import re
from collections import deque
from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouPacket, SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class RequestsGenerator(BaseGenerator):
    """
    Concrete implementation of BaseGenerator for web crawling.

    Manages a frontier queue of URLs to visit. It starts from a seed URL and
    dynamically adds new targets based on links discovered by the Fetcher (Feedback),
    respecting maximum depth and URL pattern constraints.
    """

    component_name = "RequestsGenerator"
    SUPPORTED_TYPES = ["requests"]

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
        s = source.strip().lower()

        if s.startswith("http://") or s.startswith("https://"):
            return 1.0

        if s.startswith("www."):
            return 0.8

        return 0.0

    def initialize(
        self,
        source: str,
        link_pattern: str = ".*",
        selectors: dict = None,
        max_depth: int = 1,
        **kwargs,
    ):
        """
        Configure the web crawling strategy.

        Args:
            source (str): The seed URL to start crawling.
            link_pattern (str): Regex pattern to filter links to follow.
            selectors (Optional[dict]): CSS selectors to extract specific data from pages.
            max_depth (int): Maximum depth to traverse from the seed URL.
            **kwargs: Ignored additional arguments.
        """
        self.queue = deque([(source, 0)])
        self.visited = {source}
        self.link_regex = re.compile(link_pattern)
        self.selectors = selectors or {}
        self.max_depth = max_depth

    def _do_generate(self) -> Iterator[SayouTask]:
        """
        Yield tasks from the crawling queue.

        Yields:
            Iterator[SayouTask]: Tasks for URLs in the queue.
        """
        while self.queue:
            url, depth = self.queue.popleft()
            yield SayouTask(
                source_type="requests",
                uri=url,
                params={"selectors": self.selectors, "depth": depth},
            )

    def _do_feedback(self, result: SayouPacket):
        """
        Extract links from the fetched page and add them to the queue.

        Args:
            result (SayouPacket): The result containing extracted links ('__found_links__').
        """
        if not result.success or not result.data:
            return

        current_depth = result.task.params.get("depth", 0)
        if current_depth >= self.max_depth:
            return

        links = result.data.get("__found_links__", [])
        new_links = 0

        for link in links:
            if link not in self.visited and self.link_regex.search(link):
                self.visited.add(link)
                self.queue.append((link, current_depth + 1))
                new_links += 1

        if new_links > 0:
            self._log(f"Added {new_links} new links (Depth {current_depth+1})")
