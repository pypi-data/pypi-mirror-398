"""Activity model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Activity:
    """
    Represents an activity/event in the CRM.

    Attributes:
        id: Activity UUID
        activity_type: Type of activity
        title: Activity title
        description: Description
        related_to_type: Type of related entity (contact, deal, etc.)
        related_to_id: UUID of related entity
        metadata: Additional metadata
        occurred_at: When the activity occurred
        created_by: Creator UUID
        created_by_name: Creator name
        created_at: Creation timestamp
    """

    id: str
    activity_type: str
    title: str
    description: str = ""
    related_to_type: Optional[str] = None
    related_to_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    occurred_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.metadata is None:
            self.metadata = {}

        # Parse datetime strings
        if isinstance(self.occurred_at, str):
            self.occurred_at = datetime.fromisoformat(
                self.occurred_at.replace("Z", "+00:00")
            )
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(
                self.created_at.replace("Z", "+00:00")
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Activity":
        """
        Create Activity from API response dictionary.

        Args:
            data: Activity data from API

        Returns:
            Activity instance
        """
        return cls(
            id=data.get("id"),
            activity_type=data.get("activity_type", "CUSTOM"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            related_to_type=data.get("related_to_type"),
            related_to_id=data.get("related_to_id"),
            metadata=data.get("metadata", {}),
            occurred_at=data.get("occurred_at"),
            created_by=data.get("created_by"),
            created_by_name=data.get("created_by_name"),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Activity to dictionary for API requests.

        Returns:
            Dictionary representation
        """
        data = {
            "activity_type": self.activity_type,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata,
        }
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
