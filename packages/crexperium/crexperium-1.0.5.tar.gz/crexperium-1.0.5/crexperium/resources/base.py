"""Base resource class."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..utils.http import HTTPClient


class BaseResource:
    """
    Base class for all resource classes.
    """

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize resource.

        Args:
            http_client: HTTP client instance
        """
        self.http = http_client
