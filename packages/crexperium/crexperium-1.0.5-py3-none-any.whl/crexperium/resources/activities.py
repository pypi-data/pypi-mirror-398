"""Activities resource."""
from typing import Any, Dict, List, Optional

from .base import BaseResource
from ..models import Activity


class ActivitiesResource(BaseResource):
    """
    Resource for managing activities and events.
    """

    def log(
        self,
        title: str,
        activity_type: str = "CUSTOM",
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Activity:
        """
        Log an activity from your backend system.

        This endpoint identifies contacts by user_id (external_id) or email and
        automatically links the activity to the found contact.

        Args:
            title: Activity title
            activity_type: Type of activity (default: CUSTOM)
            user_id: User's external_id in your system
            email: User's email address
            description: Activity description
            metadata: Additional metadata dictionary

        Returns:
            Created activity

        Example:
            >>> activity = client.activities.log(
            ...     title="User completed onboarding",
            ...     activity_type="USER_ACTION",
            ...     user_id="user_123",
            ...     metadata={"steps": 5, "time_spent": 120}
            ... )
        """
        data = {
            "title": title,
            "activity_type": activity_type,
            "user_id": user_id,
            "email": email,
            "description": description,
            "metadata": metadata or {},
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self.http.post("/api/v1/activities/log/", data=data)
        return Activity.from_dict(response)

    def create(
        self,
        title: str,
        activity_type: str = "CUSTOM",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Activity:
        """
        Create an activity (generic endpoint).

        Args:
            title: Activity title
            activity_type: Type of activity
            description: Description
            metadata: Additional metadata

        Returns:
            Created activity

        Example:
            >>> activity = client.activities.create(
            ...     title="Meeting scheduled",
            ...     activity_type="MEETING"
            ... )
        """
        data = {
            "title": title,
            "activity_type": activity_type,
            "description": description,
            "metadata": metadata or {},
        }
        response = self.http.post("/api/v1/activities/", data=data)
        return Activity.from_dict(response)

    def get(self, activity_id: str) -> Activity:
        """
        Get an activity by ID.

        Args:
            activity_id: Activity UUID

        Returns:
            Activity

        Example:
            >>> activity = client.activities.get("activity-uuid")
        """
        response = self.http.get(f"/api/v1/activities/{activity_id}/")
        return Activity.from_dict(response)

    def list(self, **filters) -> List[Activity]:
        """
        List activities with optional filters.

        Args:
            **filters: Filter parameters (activity_type, related_to_type, etc.)

        Returns:
            List of activities

        Example:
            >>> activities = client.activities.list(activity_type="USER_ACTION")
        """
        response = self.http.get("/api/v1/activities/", params=filters)
        results = response.get("results", [])
        return [Activity.from_dict(item) for item in results]

    def timeline(
        self, related_to_type: str, related_to_id: str
    ) -> List[Activity]:
        """
        Get activity timeline for a specific entity.

        Args:
            related_to_type: Type of entity (contact, company, deal)
            related_to_id: UUID of the entity

        Returns:
            List of activities

        Example:
            >>> timeline = client.activities.timeline("contact", "contact-uuid")
        """
        params = {"related_to_type": related_to_type, "related_to_id": related_to_id}
        response = self.http.get("/api/v1/activities/timeline/", params=params)
        return [Activity.from_dict(item) for item in response]

    def recent(self, activity_type: Optional[str] = None) -> List[Activity]:
        """
        Get recent activities (last 30 days).

        Args:
            activity_type: Filter by activity type (optional)

        Returns:
            List of recent activities

        Example:
            >>> recent = client.activities.recent(activity_type="DEAL_CREATED")
        """
        params = {}
        if activity_type:
            params["activity_type"] = activity_type

        response = self.http.get("/api/v1/activities/recent/", params=params)
        results = response.get("results", [])
        return [Activity.from_dict(item) for item in results]
