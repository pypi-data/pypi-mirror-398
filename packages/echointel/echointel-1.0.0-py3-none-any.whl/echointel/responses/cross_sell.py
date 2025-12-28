"""Cross-sell response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class CrossSellPair(EchoIntelResponse):
    """Cross-sell product pair with affinity score."""

    product_a: str
    product_b: str
    support: float
    confidence: float
    lift: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.product_a = data.get("product_a", "")
        self.product_b = data.get("product_b", "")
        self.support = float(data.get("support", 0))
        self.confidence = float(data.get("confidence", 0))
        self.lift = float(data.get("lift", 0))


class CrossSellResponse(EchoIntelResponse):
    """Response for cross-sell matrix endpoint."""

    pairs: list[CrossSellPair]
    total_transactions: int

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.pairs = [
            CrossSellPair.from_dict(item) for item in data.get("pairs", [])
        ]
        self.total_transactions = int(data.get("total_transactions", 0))


class UpsellPair(EchoIntelResponse):
    """Upsell product pair suggestion."""

    source_product: str
    target_product: str
    probability: float
    avg_revenue_increase: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.source_product = data.get("source_product", "")
        self.target_product = data.get("target_product", "")
        self.probability = float(data.get("probability", 0))
        self.avg_revenue_increase = float(data.get("avg_revenue_increase", 0))


class UpsellResponse(EchoIntelResponse):
    """Response for upsell suggestions endpoint."""

    suggestions: list[UpsellPair]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.suggestions = [
            UpsellPair.from_dict(item) for item in data.get("suggestions", [])
        ]
