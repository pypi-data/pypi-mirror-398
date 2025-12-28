"""Event model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Event:
    """
    Represents a tracked event in the CRM.

    Attributes:
        id: Event UUID
        event_definition: Event definition UUID
        event_name: Event name (e.g., "Purchase", "CompleteRegistration")
        event_key: Event key (e.g., "purchase", "complete_registration")
        visitor_id: Visitor/user identifier (should match external_id in contacts)
        contact: Contact UUID (if event is linked to a contact)
        contact_name: Contact full name
        user_properties: User properties (email, phone, name, etc.)
        event_data: Event-specific data (e.g., product_id, value, currency)
        page_url: Page URL where event occurred
        page_title: Page title
        referrer: Referrer URL
        ip_address: Client IP address
        user_agent: User agent string
        device_type: Device type (desktop, mobile, tablet)
        browser: Browser name
        os: Operating system
        country: Country
        city: City
        event_time: When the event occurred
        created_at: When the event was created in the system
        sdk_version: SDK version that sent the event
        source: Event source (web, mobile, server, etc.)
    """

    id: str
    event_definition: str
    event_name: str
    event_key: str
    event_time: datetime
    visitor_id: Optional[str] = None
    contact: Optional[str] = None
    contact_name: Optional[str] = None
    user_properties: Dict[str, Any] = None
    event_data: Dict[str, Any] = None
    page_url: Optional[str] = None
    page_title: str = ""
    referrer: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: str = ""
    device_type: str = ""
    browser: str = ""
    os: str = ""
    country: str = ""
    city: str = ""
    created_at: Optional[datetime] = None
    sdk_version: str = ""
    source: str = "web"

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.user_properties is None:
            self.user_properties = {}
        if self.event_data is None:
            self.event_data = {}

        # Parse datetime strings
        if isinstance(self.event_time, str):
            self.event_time = datetime.fromisoformat(
                self.event_time.replace("Z", "+00:00")
            )
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(
                self.created_at.replace("Z", "+00:00")
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """
        Create Event from API response dictionary.

        Args:
            data: Event data from API

        Returns:
            Event instance
        """
        return cls(
            id=data.get("id"),
            event_definition=data.get("event_definition"),
            event_name=data.get("event_name", ""),
            event_key=data.get("event_key", ""),
            visitor_id=data.get("visitor_id"),
            contact=data.get("contact"),
            contact_name=data.get("contact_name"),
            user_properties=data.get("user_properties", {}),
            event_data=data.get("event_data", {}),
            page_url=data.get("page_url"),
            page_title=data.get("page_title", ""),
            referrer=data.get("referrer"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent", ""),
            device_type=data.get("device_type", ""),
            browser=data.get("browser", ""),
            os=data.get("os", ""),
            country=data.get("country", ""),
            city=data.get("city", ""),
            event_time=data.get("event_time"),
            created_at=data.get("created_at"),
            sdk_version=data.get("sdk_version", ""),
            source=data.get("source", "web"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Event to dictionary for API requests.

        Returns:
            Dictionary representation
        """
        data = {
            "event_key": self.event_key,
            "visitor_id": self.visitor_id,
            "user_properties": self.user_properties,
            "event_data": self.event_data,
            "page_url": self.page_url,
            "page_title": self.page_title,
            "referrer": self.referrer,
            "user_agent": self.user_agent,
            "device_type": self.device_type,
            "browser": self.browser,
            "os": self.os,
            "country": self.country,
            "city": self.city,
            "event_time": self.event_time.isoformat() if isinstance(self.event_time, datetime) else self.event_time,
            "sdk_version": self.sdk_version,
            "source": self.source,
        }
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
