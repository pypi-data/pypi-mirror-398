from abc import abstractmethod
from typing import Any

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time, retry
from sayou.core.schemas import SayouPacket, SayouTask

from ..core.exceptions import FetcherError


class BaseFetcher(BaseComponent):
    """
    (Tier 1) Abstract base class for all data fetchers.

    This class implements the Template Method pattern. It handles common logic
    like logging, error wrapping, and retries in `fetch()`, while delegating
    the actual retrieval logic to `_do_fetch()`.
    """

    component_name = "BaseFetcher"
    SUPPORTED_TYPES = []

    @measure_time
    @retry(max_retries=3, delay=1.0)
    def fetch(self, task: SayouTask) -> SayouPacket:
        """
        Execute the fetching process for a given task.

        This method wraps the actual fetching logic with error handling and logging.
        It guarantees to return a SayouPacket, even if the operation fails.

        Args:
            task (SayouTask): The task definition containing the URI and parameters.

        Returns:
            SayouPacket: A packet containing the fetched data (on success)
                        or error details (on failure).
        """
        self._emit("on_start", input_data=task)
        self._log(f"Fetching: {task.uri} ({task.source_type})", level="debug")

        try:
            data = self._do_fetch(task)
            packet = SayouPacket(task=task, data=data, success=True)
            self._emit("on_finish", result_data=packet, success=True)
            return packet

        except Exception as e:
            self._emit("on_error", error=e)
            wrapped_error = FetcherError(
                f"[{self.component_name}] Failed to fetch: {str(e)}"
            )
            self.logger.error(wrapped_error, exc_info=True)

            return SayouPacket(
                task=task, data=None, success=False, error=str(wrapped_error)
            )

    @abstractmethod
    def _do_fetch(self, task: SayouTask) -> Any:
        """
        [Abstract Hook] Implement the actual data retrieval logic here.

        Args:
            task (SayouTask): The task containing source URI and params.

        Returns:
            Any: The raw data retrieved (e.g., bytes, str, list).

        Raises:
            Exception: Raise any exception if retrieval fails.
                        The parent `fetch` method will catch and wrap it.
        """
        raise NotImplementedError
