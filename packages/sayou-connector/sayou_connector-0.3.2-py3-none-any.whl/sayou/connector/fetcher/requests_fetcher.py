from urllib.parse import urljoin

import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class RequestsFetcher(BaseFetcher):
    """
    Concrete implementation of BaseFetcher for static web pages.

    Retrieves HTML content via HTTP requests. It supports optional CSS selector
    extraction (via `task.params['selectors']`) and automatically discovers
    hyperlinks on the page to support the `WebCrawlGenerator` feedback loop.
    """

    component_name = "RequestsFetcher"
    SUPPORTED_TYPES = ["requests"]

    def _do_fetch(self, task: SayouTask) -> dict:
        """
        Fetch a web page and extract data/links.

        Args:
            task (SayouTask): The task containing the URL in `task.uri`.
                            `task.params` may contain 'selectors'.

        Returns:
            dict: A dictionary containing extracted text, raw preview,
                and found links under '__found_links__'.

        Raises:
            requests.RequestException: For network-related errors.
            ImportError: If BeautifulSoup is not installed.
        """
        if not BeautifulSoup:
            raise ImportError("BeautifulSoup4 not installed.")

        headers = {"User-Agent": "Sayou-Connector/0.1.0"}
        resp = requests.get(task.uri, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        extracted_data = {}

        # 1. Selectors logic
        selectors = task.params.get("selectors", {})
        if selectors:
            for key, sel in selectors.items():
                el = soup.select(sel)
                if el:
                    extracted_data[key] = "\n".join(
                        [e.get_text(strip=True) for e in el]
                    )

        if not extracted_data:
            extracted_data["_raw_preview"] = resp.text[:200]

        # 2. Link extraction logic
        found_links = set()
        for a in soup.find_all("a", href=True):
            abs_link = urljoin(task.uri, a["href"])
            if abs_link.startswith("http"):
                found_links.add(abs_link)

        extracted_data["__found_links__"] = list(found_links)

        return extracted_data
