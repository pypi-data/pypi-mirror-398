"""Churn response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class ChurnLabelResponse(EchoIntelResponse):
    """Response for churn label endpoint."""

    customer_id: str
    snapshot_date: str
    churned: int

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.snapshot_date = data.get("snapshot_date", "")
        self.churned = int(data.get("churned", 0))

    @property
    def is_churned(self) -> bool:
        """Check if the customer has churned.

        Returns:
            True if the customer has churned, False otherwise.
        """
        return self.churned == 1
