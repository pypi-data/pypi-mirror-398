"""Pricing response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class PriceOutcome(EchoIntelResponse):
    """Individual pricing recommendation."""

    product_id: str
    current_price: float
    recommended_price: float
    expected_demand_change: float
    expected_revenue_change: float
    confidence: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.product_id = data.get("product_id", "")
        self.current_price = float(data.get("current_price", 0))
        self.recommended_price = float(data.get("recommended_price", 0))
        self.expected_demand_change = float(data.get("expected_demand_change", 0))
        self.expected_revenue_change = float(data.get("expected_revenue_change", 0))
        self.confidence = float(data.get("confidence", 0))


class PricingResponse(EchoIntelResponse):
    """Response for dynamic pricing endpoint."""

    recommendations: list[PriceOutcome]
    optimization_objective: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.recommendations = [
            PriceOutcome.from_dict(item) for item in data.get("recommendations", [])
        ]
        self.optimization_objective = data.get("optimization_objective", "")
