import sqlite3
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class SqliteFetcher(BaseFetcher):
    """
    Concrete implementation of BaseFetcher for SQLite databases.

    Connects to the SQLite database file specified in `task.uri` and executes
    the SQL query provided in `task.params['query']`. It manages connection
    lifecycles using context managers and returns results as a list of dictionaries.
    """

    component_name = "SqliteFetcher"
    SUPPORTED_TYPES = ["sqlite"]

    def _do_fetch(self, task: SayouTask) -> List[Dict[str, Any]]:
        """
        Execute a SQL query against a SQLite database.

        Args:
            task (SayouTask): The task containing the DB path in `task.uri`
                                and the SQL query in `task.params['query']`.

        Returns:
            List[Dict[str, Any]]: A list of rows, where each row is a dictionary.

        Raises:
            sqlite3.Error: If the database connection or query execution fails.
        """
        db_path = task.uri
        query = task.params.get("query")

        if not query:
            raise ValueError("Query param is missing in SayouTask")

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            self._log(f"Executing query on {db_path}: {query[:50]}...", level="debug")

            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
