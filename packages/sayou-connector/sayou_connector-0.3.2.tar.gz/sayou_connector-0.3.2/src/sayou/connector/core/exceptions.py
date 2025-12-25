from sayou.core.exceptions import SayouCoreError


class ConnectorError(SayouCoreError):
    """
    Base exception for all errors within the sayou-connector toolkit.

    All specific exceptions in this module should inherit from this class
    to allow catching connector-specific issues globally.
    """

    pass


class FetcherError(ConnectorError):
    """
    Exception raised when a Fetcher fails to retrieve data.

    Examples:
        - File not found on disk.
        - HTTP connection timeout or 404/500 errors.
        - Database connection failure.
    """

    pass


class GeneratorError(ConnectorError):
    """
    Exception raised when a Generator fails to produce tasks.

    Examples:
        - Invalid start path or configuration.
        - Failure to parse a sitemap or initial seed page.
        - Logic errors in the generation strategy.
    """

    pass
