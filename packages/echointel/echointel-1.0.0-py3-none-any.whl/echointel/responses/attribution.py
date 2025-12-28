"""Attribution response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class ChannelContribution(EchoIntelResponse):
    """Individual channel contribution in attribution analysis."""

    channel: str
    contribution: float
    conversions: int
    cost: float
    roi: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.channel = data.get("channel", "")
        self.contribution = float(data.get("contribution", 0))
        self.conversions = int(data.get("conversions", 0))
        self.cost = float(data.get("cost", 0))
        self.roi = float(data.get("roi", 0))


class AttributionResponse(EchoIntelResponse):
    """Response for channel attribution endpoint."""

    contributions: list[ChannelContribution]
    global_auc: float
    interpretation: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.contributions = [
            ChannelContribution.from_dict(item)
            for item in data.get("contributions", [])
        ]
        self.global_auc = float(data.get("global_auc", 0))
        self.interpretation = data.get("interpretation", "")


class DecileSummary(EchoIntelResponse):
    """Decile summary for uplift analysis."""

    decile: int
    avg_uplift: float
    count: int
    cumulative_uplift: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.decile = int(data.get("decile", 0))
        self.avg_uplift = float(data.get("avg_uplift", 0))
        self.count = int(data.get("count", 0))
        self.cumulative_uplift = float(data.get("cumulative_uplift", 0))


class UpliftDetail(EchoIntelResponse):
    """Individual uplift prediction detail."""

    customer_id: str
    uplift_score: float
    treatment_probability: float
    control_probability: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.uplift_score = float(data.get("uplift_score", 0))
        self.treatment_probability = float(data.get("treatment_probability", 0))
        self.control_probability = float(data.get("control_probability", 0))


class UpliftResponse(EchoIntelResponse):
    """Response for uplift model endpoint."""

    details: list[UpliftDetail]
    decile_summary: list[DecileSummary]
    model_auc: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.details = [
            UpliftDetail.from_dict(item) for item in data.get("details", [])
        ]
        self.decile_summary = [
            DecileSummary.from_dict(item) for item in data.get("decile_summary", [])
        ]
        self.model_auc = float(data.get("model_auc", 0))
