"""Admin response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class CustomerOut(EchoIntelResponse):
    """Response for admin customer operations."""

    customer_api_id: str
    secret: str
    enabled: bool
    ts_create: str
    ts_update: str
    allowed_routes: list[str]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_api_id = data.get("customer_api_id", "")
        self.secret = data.get("secret", "")
        self.enabled = bool(data.get("enabled", False))
        self.ts_create = data.get("ts_create", "")
        self.ts_update = data.get("ts_update", "")
        self.allowed_routes = data.get("allowed_routes", [])
