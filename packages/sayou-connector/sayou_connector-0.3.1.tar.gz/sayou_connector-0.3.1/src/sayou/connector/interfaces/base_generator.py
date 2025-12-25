from abc import abstractmethod
from typing import Iterator

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouPacket, SayouTask

from ..core.exceptions import GeneratorError


class BaseGenerator(BaseComponent):
    """
    (Tier 1) Abstract base class for all task generators.

    Generators are responsible for discovering resources (e.g., listing files,
    crawling links) and creating `SayouTask` objects for the Fetcher.
    """

    component_name = "BaseGenerator"
    SUPPORTED_TYPES = []

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
        return 0.0

    @measure_time
    def generate(self) -> Iterator[SayouTask]:
        """
        Execute the generation strategy and yield tasks one by one.

        This method handles the lifecycle of the generation process, including
        logging and error boundary protection.

        Yields:
            Iterator[SayouTask]: An iterator of tasks to be processed by Fetchers.
        """
        self._emit("on_start", input_data={"component": self.component_name})
        self._log(f"Starting generation strategy: {self.component_name}")
        count = 0
        try:
            for task in self._do_generate():
                count += 1
                yield task
            self._emit("on_finish", result_data={"total_tasks": count}, success=True)
        except Exception as e:
            wrapped_error = GeneratorError(
                f"[{self.component_name}] Strategy crashed: {str(e)}"
            )
            self.logger.error(wrapped_error, exc_info=True)
            self._emit("on_error", error=wrapped_error)
            raise wrapped_error
        finally:
            self._log(f"Generator finished. Total tasks yielded: {count}")

    @abstractmethod
    def _do_generate(self) -> Iterator[SayouTask]:
        """
        [Abstract Hook] Implement the logic to discover resources.

        Yields:
            SayouTask: A task object representing a unit of work.
        """
        raise NotImplementedError

    def feedback(self, packet: SayouPacket):
        """
        Receive feedback from the execution result of a task.

        This allows the generator to adjust its strategy dynamically
        (e.g., adding new links found in a crawled page).

        Args:
            packet (SayouPacket): The result packet from the Fetcher.
        """
        self._do_feedback(packet)

    def _do_feedback(self, packet: SayouPacket):
        """
        [Optional Hook] Override this to handle feedback logic.
        """
        pass
