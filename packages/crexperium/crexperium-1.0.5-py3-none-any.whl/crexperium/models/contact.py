"""Contact model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Contact:
    """
    Represents a contact in the CRM.

    Attributes:
        id: Contact UUID
        email: Contact email address
        first_name: First name
        last_name: Last name
        full_name: Full name (computed)
        phone: Phone number
        external_id: External identifier from third-party systems
        company: Company UUID
        company_name: Company name
        title: Job title
        department: Department
        linkedin_url: LinkedIn profile URL
        avatar: Avatar URL
        address_line1: Address line 1
        address_line2: Address line 2
        city: City
        state: State/Province
        postal_code: Postal code
        country: Country
        status: Contact status (LEAD, PROSPECT, CUSTOMER, etc.)
        description: Description
        tags: List of tags
        custom_fields: Custom fields dictionary
        last_contacted: Last contacted timestamp
        created_by: Creator UUID
        created_at: Creation timestamp
        updated_at: Update timestamp
    """

    id: str
    email: str
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    phone: str = ""
    external_id: Optional[str] = None
    company: Optional[str] = None
    company_name: Optional[str] = None
    title: str = ""
    department: str = ""
    linkedin_url: str = ""
    avatar: Optional[str] = None
    address_line1: str = ""
    address_line2: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    status: str = "LEAD"
    description: str = ""
    tags: List[str] = None
    custom_fields: Dict[str, Any] = None
    last_contacted: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.tags is None:
            self.tags = []
        if self.custom_fields is None:
            self.custom_fields = {}

        # Parse datetime strings
        if isinstance(self.last_contacted, str):
            self.last_contacted = datetime.fromisoformat(
                self.last_contacted.replace("Z", "+00:00")
            )
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(
                self.created_at.replace("Z", "+00:00")
            )
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(
                self.updated_at.replace("Z", "+00:00")
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        """
        Create Contact from API response dictionary.

        Args:
            data: Contact data from API

        Returns:
            Contact instance
        """
        return cls(
            id=data.get("id"),
            email=data.get("email", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            full_name=data.get("full_name", ""),
            phone=data.get("phone", ""),
            external_id=data.get("external_id"),
            company=data.get("company"),
            company_name=data.get("company_name"),
            title=data.get("title", ""),
            department=data.get("department", ""),
            linkedin_url=data.get("linkedin_url", ""),
            avatar=data.get("avatar"),
            address_line1=data.get("address_line1", ""),
            address_line2=data.get("address_line2", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            postal_code=data.get("postal_code", ""),
            country=data.get("country", ""),
            status=data.get("status", "LEAD"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
            last_contacted=data.get("last_contacted"),
            created_by=data.get("created_by"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Contact to dictionary for API requests.

        Returns:
            Dictionary representation
        """
        data = {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "external_id": self.external_id,
            "company": self.company,
            "title": self.title,
            "department": self.department,
            "linkedin_url": self.linkedin_url,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "status": self.status,
            "description": self.description,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
        }
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
