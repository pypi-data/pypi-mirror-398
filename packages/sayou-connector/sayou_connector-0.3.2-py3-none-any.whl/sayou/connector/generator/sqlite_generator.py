import os
from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouPacket, SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class SqliteGenerator(BaseGenerator):
    """
    Concrete implementation of BaseGenerator for SQL pagination.

    Generates a sequence of database query tasks using LIMIT and OFFSET strategies.
    It continues to yield tasks by incrementing the offset until the Fetcher returns
    an empty result or a partial batch, indicating the end of the dataset.
    """

    component_name = "SqliteGenerator"
    SUPPORTED_TYPES = ["sqlite"]

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
        s = source.strip()

        if s.lower().startswith("sqlite:///"):
            return 1.0

        if any(s.lower().endswith(ext) for ext in [".db", ".sqlite", ".sqlite3"]):
            if os.path.isfile(s):
                return 1.0
            return 0.9

        return 0.0

    def initialize(
        self,
        source: str,
        query: str = None,
        batch_size: int = 1000,
        **kwargs,
    ):
        """
        Configure the SQL scanning strategy with pagination.

        Args:
            source (str): The database connection string or file path.
            query (str): The base SQL query (without LIMIT/OFFSET).
            batch_size (int): Number of rows to fetch per task.
            **kwargs: Ignored additional arguments.
        """
        self.conn_str = self._clean_source(source)
        self.base_query = (
            query.strip().rstrip(";")
            if query
            else "SELECT name FROM sqlite_master WHERE type='table'"
        )
        self.batch_size = batch_size
        self.current_offset = 0
        self.stop_flag = False

    def _clean_source(self, source: str) -> str:
        """
        Extracts the actual file path from a source URI.

        Removes prefixes like 'sqlite:///' or 'sqlite://' from the source string
        to return a clean file path compatible with the standard `sqlite3` connect method.

        Args:
            source (str): The input source string (e.g., 'sqlite:///data/test.db').

        Returns:
            str: The cleaned file path (e.g., '/data/test.db').
        """
        s = source.strip()
        if s.lower().startswith("sqlite:///"):
            return s[10:]
        elif s.lower().startswith("sqlite://"):
            return s[9:]
        return s

    def _do_generate(self) -> Iterator[SayouTask]:
        """
        Yield pagination tasks until the stop flag is set.

        Yields:
            Iterator[SayouTask]: Tasks with `source_type='sqlite'` and pagination params.
        """
        while not self.stop_flag:
            paginated_query = f"{self.base_query} LIMIT {self.batch_size} OFFSET {self.current_offset}"

            task = SayouTask(
                source_type="sqlite",
                uri=self.conn_str,
                params={"query": paginated_query},
                meta={"offset": self.current_offset, "batch": self.batch_size},
            )

            yield task

            self.current_offset += self.batch_size

    def _do_feedback(self, result: SayouPacket):
        """
        Determine if pagination should stop based on the fetch result.

        If the number of fetched rows is less than `batch_size` or if the fetch failed,
        the generator stops producing tasks.

        Args:
            result (SayouPacket): The result from the Fetcher.
        """
        # 1. 실패했거나 데이터가 없으면 종료
        if not result.success or not result.data:
            self._log("No data returned or fetch failed. Stopping.", level="warning")
            self.stop_flag = True
            return

        # 2. 가져온 데이터가 배치 사이즈보다 작으면 '마지막 페이지'임
        rows = result.data
        if isinstance(rows, list) and len(rows) < self.batch_size:
            self._log(
                f"Reached end of records (Fetched {len(rows)} < Batch {self.batch_size})."
            )
            self.stop_flag = True
