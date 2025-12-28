"""Propensity response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class PropensityPrediction(EchoIntelResponse):
    """Individual propensity prediction."""

    customer_id: str
    probability: float
    score: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.probability = float(data.get("probability", 0))
        self.score = float(data.get("score", 0))


class PropensityModelInfo(EchoIntelResponse):
    """Model information for propensity predictions."""

    algorithm: str
    features_used: list[str]
    auc: float | None

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.algorithm = data.get("algorithm", "")
        self.features_used = data.get("features_used", [])
        self.auc = float(data["auc"]) if "auc" in data else None


class PropensityResponse(EchoIntelResponse):
    """Response for propensity endpoints."""

    predictions: list[PropensityPrediction]
    model_info: PropensityModelInfo

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.predictions = [
            PropensityPrediction.from_dict(item)
            for item in data.get("predictions", [])
        ]
        self.model_info = PropensityModelInfo.from_dict(data.get("model_info", {}))
