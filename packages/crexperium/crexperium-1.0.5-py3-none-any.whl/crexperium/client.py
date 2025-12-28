"""
Main CRM client.
"""
from typing import Optional

from .config import Config, CREXPERIUM_API_TOKEN_ENV
from .utils.http import HTTPClient
from .resources import ContactsResource, DealsResource, ActivitiesResource, EventsResource


class CRMClient:
    """
    Main client for Crexperium CRM API.

    This is the entry point for all SDK operations. It provides access to all
    resource endpoints through convenient properties.

    Example:
        >>> from crexperium import CRMClient
        >>> client = CRMClient(
        ...     api_token="your-api-token"
        ... )
        >>>
        >>> # Identify/create a contact
        >>> contact, created = client.contacts.identify(
        ...     external_id="user_123",
        ...     email="user@example.com"
        ... )
        >>>
        >>> # Create a deal
        >>> deal = client.deals.create(
        ...     name="Premium Subscription",
        ...     amount=Decimal("999.99"),
        ...     contact_external_id="user_123"
        ... )
        >>>
        >>> # Log an activity
        >>> activity = client.activities.log(
        ...     title="User completed onboarding",
        ...     user_id="user_123"
        ... )
        >>>
        >>> # Track an event
        >>> event = client.events.track(
        ...     event_key="purchase",
        ...     visitor_id="user_123",
        ...     event_data={"value": 99.99, "currency": "USD"}
        ... )
        >>>
        >>> # Don't forget to close when done
        >>> client.close()
        >>>
        >>> # Or use as context manager
        >>> with CRMClient(api_token="token") as client:
        ...     contact, _ = client.contacts.identify(...)
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize CRM client.

        The API token is automatically read from the CREXPERIUM_API_TOKEN environment variable
        if not provided. The API endpoint is fixed to the production URL.

        Args:
            api_token: API token for authentication (optional, reads from env if not provided)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1)
            verify_ssl: Whether to verify SSL certificates (default: True)

        Raises:
            ValueError: If api_token is not provided and CREXPERIUM_API_TOKEN env var is not set

        Example:
            # Option 1: Set environment variable
            $ export CREXPERIUM_API_TOKEN="your-api-token"
            $ python
            >>> from crexperium import CRMClient
            >>> client = CRMClient()  # Automatically uses env var

            # Option 2: Pass token directly
            >>> client = CRMClient(api_token="your-api-token")
        """
        # Create configuration (will auto-load from env if api_token not provided)
        self.config = Config(
            api_token=api_token,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            verify_ssl=verify_ssl,
        )

        # Initialize HTTP client
        self._http = HTTPClient(self.config)

        # Initialize resources
        self._contacts = ContactsResource(self._http)
        self._deals = DealsResource(self._http)
        self._activities = ActivitiesResource(self._http)
        self._events = EventsResource(self._http)

    @property
    def contacts(self) -> ContactsResource:
        """
        Access contacts resource.

        Returns:
            ContactsResource instance

        Example:
            >>> contact = client.contacts.get("contact-uuid")
        """
        return self._contacts

    @property
    def deals(self) -> DealsResource:
        """
        Access deals resource.

        Returns:
            DealsResource instance

        Example:
            >>> deal = client.deals.get("deal-uuid")
        """
        return self._deals

    @property
    def activities(self) -> ActivitiesResource:
        """
        Access activities resource.

        Returns:
            ActivitiesResource instance

        Example:
            >>> activity = client.activities.get("activity-uuid")
        """
        return self._activities

    @property
    def events(self) -> EventsResource:
        """
        Access events resource.

        Returns:
            EventsResource instance

        Example:
            >>> event = client.events.track("purchase", visitor_id="user_123")
        """
        return self._events

    def close(self):
        """
        Close the HTTP session.

        Always call this when you're done with the client to properly close
        connections. Alternatively, use the client as a context manager.

        Example:
            >>> client = CRMClient(api_token="token")
            >>> # ... use client ...
            >>> client.close()
        """
        self._http.close()

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close()
        return False

    def __repr__(self):
        """String representation."""
        return f"CRMClient(api_url='{self.config.base_url}')"
