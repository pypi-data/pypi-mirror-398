"""Deals resource."""
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseResource
from ..models import Deal


class DealsResource(BaseResource):
    """
    Resource for managing deals/opportunities.
    """

    def create(
        self,
        name: str,
        amount: Decimal,
        contact_id: Optional[str] = None,
        contact_external_id: Optional[str] = None,
        contact_email: Optional[str] = None,
        pipeline: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs,
    ) -> Deal:
        """
        Create a deal with flexible contact identification.

        This is a convenience method that uses the SDK endpoint for flexible
        contact identification. For maximum control, use create_with_sdk().

        Args:
            name: Deal name
            amount: Deal amount
            contact_id: Contact UUID
            contact_external_id: Contact external_id
            contact_email: Contact email
            pipeline: Pipeline name or UUID (optional, uses default if not provided)
            stage: Stage name or UUID (optional, uses first stage if not provided)
            **kwargs: Additional deal fields (currency, priority, tags, etc.)

        Returns:
            Created deal

        Example:
            >>> deal = client.deals.create(
            ...     name="Premium Subscription",
            ...     amount=Decimal("999.99"),
            ...     contact_external_id="user_123",
            ...     currency="USD",
            ...     priority="HIGH"
            ... )
        """
        data = {
            "name": name,
            "amount": str(amount),
            "contact_id": contact_id,
            "contact_external_id": contact_external_id,
            "contact_email": contact_email,
            "pipeline": pipeline,
            "stage": stage,
            **kwargs,
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self.http.post("/api/v1/deals/sdk-create/", data=data)
        return Deal.from_dict(response)

    def get(self, deal_id: str) -> Deal:
        """
        Get a deal by ID.

        Args:
            deal_id: Deal UUID

        Returns:
            Deal with full details

        Example:
            >>> deal = client.deals.get("deal-uuid")
        """
        response = self.http.get(f"/api/v1/deals/{deal_id}/")
        return Deal.from_dict(response)

    def update(self, deal_id: str, **kwargs) -> Deal:
        """
        Update a deal.

        Args:
            deal_id: Deal UUID
            **kwargs: Fields to update

        Returns:
            Updated deal

        Example:
            >>> deal = client.deals.update(
            ...     "deal-uuid",
            ...     amount=Decimal("1499.99"),
            ...     priority="URGENT"
            ... )
        """
        # Convert Decimal to string for amount
        if "amount" in kwargs and isinstance(kwargs["amount"], Decimal):
            kwargs["amount"] = str(kwargs["amount"])

        response = self.http.patch(f"/api/v1/deals/{deal_id}/", data=kwargs)
        return Deal.from_dict(response)

    def delete(self, deal_id: str) -> None:
        """
        Delete a deal.

        Args:
            deal_id: Deal UUID

        Example:
            >>> client.deals.delete("deal-uuid")
        """
        self.http.delete(f"/api/v1/deals/{deal_id}/")

    def list(self, **filters) -> List[Deal]:
        """
        List deals with optional filters.

        Args:
            **filters: Filter parameters (pipeline, stage, status, owner, etc.)

        Returns:
            List of deals

        Example:
            >>> deals = client.deals.list(status="OPEN", priority="HIGH")
        """
        response = self.http.get("/api/v1/deals/", params=filters)
        results = response.get("results", [])
        return [Deal.from_dict(item) for item in results]

    def move_stage(self, deal_id: str, stage_id: str, notes: str = "") -> Deal:
        """
        Move deal to a new stage.

        Args:
            deal_id: Deal UUID
            stage_id: Stage UUID to move to
            notes: Optional notes about the stage change

        Returns:
            Updated deal

        Example:
            >>> deal = client.deals.move_stage(
            ...     "deal-uuid",
            ...     "stage-uuid",
            ...     notes="Customer requested demo"
            ... )
        """
        data = {"stage": stage_id, "notes": notes}
        response = self.http.post(f"/api/v1/deals/{deal_id}/move_stage/", data=data)
        return Deal.from_dict(response)

    def get_history(self, deal_id: str) -> List[Dict[str, Any]]:
        """
        Get stage history for a deal.

        Args:
            deal_id: Deal UUID

        Returns:
            List of history entries

        Example:
            >>> history = client.deals.get_history("deal-uuid")
        """
        response = self.http.get(f"/api/v1/deals/{deal_id}/history/")
        return response

    def by_stage(self, pipeline_id: str, **filters) -> List[Dict[str, Any]]:
        """
        Get deals grouped by stage for kanban view.

        Args:
            pipeline_id: Pipeline UUID
            **filters: Additional filters (status, owner, etc.)

        Returns:
            List of stages with deals

        Example:
            >>> stages = client.deals.by_stage("pipeline-uuid", status="OPEN")
        """
        params = {"pipeline": pipeline_id, **filters}
        response = self.http.get("/api/v1/deals/by_stage/", params=params)
        return response
