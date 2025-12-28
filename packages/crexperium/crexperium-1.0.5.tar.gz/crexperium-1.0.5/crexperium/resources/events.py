"""Events resource."""
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseResource
from ..models import Event


class EventsResource(BaseResource):
    """
    Resource for tracking events.

    This resource provides methods for tracking user events, which are automatically
    forwarded to configured providers (e.g., Meta Conversion API) if enabled.
    """

    def track(
        self,
        event_key: str,
        visitor_id: Optional[str] = None,
        user_properties: Optional[Dict[str, Any]] = None,
        event_data: Optional[Dict[str, Any]] = None,
        page_url: Optional[str] = None,
        page_title: str = "",
        referrer: Optional[str] = None,
        user_agent: str = "",
        device_type: str = "",
        browser: str = "",
        os: str = "",
        country: str = "",
        city: str = "",
        event_time: Optional[datetime] = None,
        source: str = "web",
        **kwargs
    ) -> Event:
        """
        Track a single event.

        Events are automatically linked to contacts if the visitor_id matches a
        contact's external_id, or if the email in user_properties matches a contact.

        Events are also automatically forwarded to configured providers like
        Meta Conversion API if the organization has them enabled.

        Args:
            event_key: Event identifier (e.g., "purchase", "complete_registration")
            visitor_id: Visitor/user identifier (should match contact's external_id)
            user_properties: User properties (email, phone, name, etc.)
            event_data: Event-specific data (e.g., {"value": 99.99, "currency": "USD"})
            page_url: Page URL where event occurred
            page_title: Page title
            referrer: Referrer URL
            user_agent: User agent string
            device_type: Device type (desktop, mobile, tablet)
            browser: Browser name
            os: Operating system
            country: Country code
            city: City name
            event_time: When the event occurred (defaults to now)
            source: Event source (web, mobile, server, etc.)

        Returns:
            Event instance with forwarding results if applicable

        Raises:
            ValidationError: If event_key is invalid or required fields are missing
            APIError: If the API request fails

        Example:
            >>> # Track a purchase event
            >>> event = client.events.track(
            ...     event_key="purchase",
            ...     visitor_id="user_123",
            ...     user_properties={
            ...         "email": "customer@example.com",
            ...         "first_name": "John"
            ...     },
            ...     event_data={
            ...         "value": 99.99,
            ...         "currency": "USD",
            ...         "product_id": "prod_456"
            ...     },
            ...     page_url="https://example.com/checkout/success"
            ... )
            >>> print(f"Event tracked: {event.id}")

            >>> # Track registration with minimal data
            >>> event = client.events.track(
            ...     event_key="complete_registration",
            ...     visitor_id="user_789",
            ...     user_properties={"email": "newuser@example.com"}
            ... )
        """
        data = {
            "event_key": event_key,
            "visitor_id": visitor_id,
            "user_properties": user_properties or {},
            "event_data": event_data or {},
            "page_url": page_url,
            "page_title": page_title,
            "referrer": referrer,
            "user_agent": user_agent,
            "device_type": device_type,
            "browser": browser,
            "os": os,
            "country": country,
            "city": city,
            "source": source,
        }

        # Add event_time if provided
        if event_time:
            data["event_time"] = event_time.isoformat() if isinstance(event_time, datetime) else event_time

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        # Use standard Bearer authentication (same as contacts)
        response = self.http.post("/api/v1/events/track/", data=data)
        return Event.from_dict(response)

    def track_batch(
        self,
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Track multiple events in a single batch request.

        This is more efficient than calling track() multiple times when you have
        multiple events to send at once.

        Args:
            events: List of event dictionaries, each containing event data

        Returns:
            Dictionary with batch results including:
                - success: Whether the batch succeeded
                - created: Number of events created
                - errors: List of any errors that occurred

        Raises:
            ValidationError: If events list is empty or contains invalid data
            APIError: If the API request fails

        Example:
            >>> # Track multiple events at once
            >>> results = client.events.track_batch([
            ...     {
            ...         "event_key": "page_view",
            ...         "visitor_id": "user_123",
            ...         "page_url": "https://example.com/home"
            ...     },
            ...     {
            ...         "event_key": "add_to_cart",
            ...         "visitor_id": "user_123",
            ...         "event_data": {"product_id": "prod_456"}
            ...     },
            ...     {
            ...         "event_key": "purchase",
            ...         "visitor_id": "user_123",
            ...         "event_data": {"value": 99.99, "currency": "USD"}
            ...     }
            ... ])
            >>> print(f"Created {results['created']} events")
        """
        data = {"events": events}

        # Use standard Bearer authentication (same as contacts)
        response = self.http.post("/api/v1/events/batch/", data=data)
        return response

    def get(self, event_id: str) -> Event:
        """
        Get an event by ID.

        Args:
            event_id: Event UUID

        Returns:
            Event instance

        Raises:
            ResourceNotFoundError: If event doesn't exist
            APIError: If the API request fails

        Example:
            >>> event = client.events.get("event-uuid-123")
            >>> print(f"Event: {event.event_name} at {event.event_time}")
        """
        response = self.http.get(f"/api/v1/events/{event_id}/")
        return Event.from_dict(response)

    def list(
        self,
        event_definition: Optional[str] = None,
        visitor_id: Optional[str] = None,
        contact: Optional[str] = None,
        device_type: Optional[str] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        **filters
    ) -> List[Event]:
        """
        List events with optional filters.

        Args:
            event_definition: Filter by event definition UUID
            visitor_id: Filter by visitor ID
            contact: Filter by contact UUID
            device_type: Filter by device type
            source: Filter by event source
            page: Page number (default: 1)
            page_size: Number of results per page (default: 20)
            **filters: Additional filter parameters

        Returns:
            List of Event instances

        Raises:
            APIError: If the API request fails

        Example:
            >>> # Get all purchase events
            >>> events = client.events.list(event_key="purchase")

            >>> # Get events for a specific user
            >>> events = client.events.list(visitor_id="user_123", page_size=50)

            >>> # Get mobile events
            >>> events = client.events.list(device_type="mobile", source="mobile")
        """
        params = {
            "page": page,
            "page_size": page_size,
            **filters
        }

        if event_definition:
            params["event_definition"] = event_definition
        if visitor_id:
            params["visitor_id"] = visitor_id
        if contact:
            params["contact"] = contact
        if device_type:
            params["device_type"] = device_type
        if source:
            params["source"] = source

        response = self.http.get("/api/v1/events/", params=params)
        results = response.get("results", [])
        return [Event.from_dict(item) for item in results]

    def stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get event statistics for the specified time period.

        Args:
            days: Number of days to include in statistics (default: 30)

        Returns:
            Dictionary containing:
                - total_events: Total number of events
                - unique_visitors: Number of unique visitors
                - unique_contacts: Number of unique contacts
                - events_by_type: List of events grouped by type
                - events_by_day: Daily event counts
                - date_range: The date range for the stats

        Raises:
            APIError: If the API request fails

        Example:
            >>> stats = client.events.stats(days=7)
            >>> print(f"Total events: {stats['total_events']}")
            >>> print(f"Unique visitors: {stats['unique_visitors']}")
            >>> for event_type in stats['events_by_type']:
            ...     print(f"{event_type['event_definition__name']}: {event_type['count']}")
        """
        params = {"days": days}
        response = self.http.get("/api/v1/events/stats/", params=params)
        return response
