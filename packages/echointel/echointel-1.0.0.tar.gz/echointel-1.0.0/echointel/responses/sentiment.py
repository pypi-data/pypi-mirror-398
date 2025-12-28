"""Sentiment response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class SentimentDetail(EchoIntelResponse):
    """Detailed sentiment analysis result."""

    sentiment: str
    score: float
    confidence: float
    aspects: list[dict[str, Any]]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.sentiment = data.get("sentiment", "")
        self.score = float(data.get("score", 0))
        self.confidence = float(data.get("confidence", 0))
        self.aspects = data.get("aspects", [])


class SentimentKpiBlock(EchoIntelResponse):
    """KPI-level sentiment metrics."""

    kpi_name: str
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_score: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.kpi_name = data.get("kpi_name", "")
        self.positive_count = int(data.get("positive_count", 0))
        self.negative_count = int(data.get("negative_count", 0))
        self.neutral_count = int(data.get("neutral_count", 0))
        self.avg_score = float(data.get("avg_score", 0))


class ReportResponse(EchoIntelResponse):
    """Response for sentiment report endpoint."""

    period: str
    total_analyzed: int
    overall_sentiment: str
    overall_score: float
    kpi_breakdown: list[SentimentKpiBlock]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.period = data.get("period", "")
        self.total_analyzed = int(data.get("total_analyzed", 0))
        self.overall_sentiment = data.get("overall_sentiment", "")
        self.overall_score = float(data.get("overall_score", 0))
        self.kpi_breakdown = [
            SentimentKpiBlock.from_dict(item)
            for item in data.get("kpi_breakdown", [])
        ]


class RealtimeResponse(EchoIntelResponse):
    """Response for realtime sentiment endpoint."""

    analysis: SentimentDetail
    interpretation: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.analysis = SentimentDetail.from_dict(data.get("analysis", {}))
        self.interpretation = data.get("interpretation", "")
