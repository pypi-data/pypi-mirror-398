"""Recommendation response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class ModelInfo(EchoIntelResponse):
    """Information about the recommendation model."""

    algorithm: str
    version: str
    last_trained: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.algorithm = data.get("algorithm", "")
        self.version = data.get("version", "")
        self.last_trained = data.get("last_trained", "")


class RecommendationOut(EchoIntelResponse):
    """Individual recommendation item."""

    item_id: str
    score: float
    rank: int

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.item_id = data.get("item_id", "")
        self.score = float(data.get("score", 0))
        self.rank = int(data.get("rank", 0))


class RecResponse(EchoIntelResponse):
    """Response for recommendation endpoints."""

    recommendations: list[RecommendationOut]
    model_info: ModelInfo

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.recommendations = [
            RecommendationOut.from_dict(item)
            for item in data.get("recommendations", [])
        ]
        self.model_info = ModelInfo.from_dict(data.get("model_info", {}))
