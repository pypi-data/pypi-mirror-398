"""Credit risk response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class Prediction(EchoIntelResponse):
    """Individual credit risk prediction."""

    customer_id: str
    risk_score: float
    risk_category: str
    probability_of_default: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.risk_score = float(data.get("risk_score", 0))
        self.risk_category = data.get("risk_category", "")
        self.probability_of_default = float(data.get("probability_of_default", 0))


class ScoreResponse(EchoIntelResponse):
    """Response for credit risk score endpoint."""

    predictions: list[Prediction]
    model_version: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.predictions = [
            Prediction.from_dict(item) for item in data.get("predictions", [])
        ]
        self.model_version = data.get("model_version", "")


class FeatureImportance(EchoIntelResponse):
    """Feature importance for credit risk explanation."""

    feature_name: str
    importance: float
    direction: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.feature_name = data.get("feature_name", "")
        self.importance = float(data.get("importance", 0))
        self.direction = data.get("direction", "")


class ExplainResponse(EchoIntelResponse):
    """Response for credit risk explain endpoint."""

    customer_id: str
    risk_score: float
    feature_importances: list[FeatureImportance]
    explanation_text: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.risk_score = float(data.get("risk_score", 0))
        self.feature_importances = [
            FeatureImportance.from_dict(item)
            for item in data.get("feature_importances", [])
        ]
        self.explanation_text = data.get("explanation_text", "")
