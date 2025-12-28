"""Deal model."""
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class Deal:
    """
    Represents a deal/opportunity in the CRM.

    Attributes:
        id: Deal UUID
        name: Deal name
        description: Description
        contact: Contact UUID
        company: Company UUID
        owner: Owner user UUID
        pipeline: Pipeline UUID
        stage: Stage UUID
        amount: Deal amount
        currency: Currency code (e.g., USD)
        expected_close_date: Expected close date
        closed_date: Actual close date
        status: Deal status (OPEN, WON, LOST)
        priority: Priority (LOW, MEDIUM, HIGH, URGENT)
        tags: List of tags
        custom_fields: Custom fields dictionary
        created_by: Creator UUID
        created_at: Creation timestamp
        updated_at: Update timestamp
    """

    id: str
    name: str
    amount: Decimal
    contact: str
    owner: str
    pipeline: str
    stage: str
    description: str = ""
    company: Optional[str] = None
    currency: str = "USD"
    expected_close_date: Optional[date] = None
    closed_date: Optional[date] = None
    status: str = "OPEN"
    priority: str = "MEDIUM"
    tags: List[str] = None
    custom_fields: Dict[str, Any] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.tags is None:
            self.tags = []
        if self.custom_fields is None:
            self.custom_fields = {}

        # Convert amount to Decimal
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))

        # Parse date strings
        if isinstance(self.expected_close_date, str):
            self.expected_close_date = date.fromisoformat(self.expected_close_date)
        if isinstance(self.closed_date, str):
            self.closed_date = date.fromisoformat(self.closed_date)

        # Parse datetime strings
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(
                self.created_at.replace("Z", "+00:00")
            )
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(
                self.updated_at.replace("Z", "+00:00")
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Deal":
        """
        Create Deal from API response dictionary.

        Args:
            data: Deal data from API

        Returns:
            Deal instance
        """
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            contact=data.get("contact"),
            company=data.get("company"),
            owner=data.get("owner"),
            pipeline=data.get("pipeline"),
            stage=data.get("stage"),
            amount=data.get("amount", "0"),
            currency=data.get("currency", "USD"),
            expected_close_date=data.get("expected_close_date"),
            closed_date=data.get("closed_date"),
            status=data.get("status", "OPEN"),
            priority=data.get("priority", "MEDIUM"),
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
            created_by=data.get("created_by"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Deal to dictionary for API requests.

        Returns:
            Dictionary representation
        """
        data = {
            "name": self.name,
            "description": self.description,
            "contact": self.contact,
            "company": self.company,
            "owner": self.owner,
            "pipeline": self.pipeline,
            "stage": self.stage,
            "amount": str(self.amount),
            "currency": self.currency,
            "expected_close_date": (
                self.expected_close_date.isoformat()
                if self.expected_close_date
                else None
            ),
            "priority": self.priority,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
        }
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
