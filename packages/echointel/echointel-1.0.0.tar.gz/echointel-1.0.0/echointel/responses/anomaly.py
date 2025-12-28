"""Anomaly detection response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class AnomalyDetail(EchoIntelResponse):
    """Individual anomaly detection result."""

    record_id: str
    anomaly_score: float
    is_anomaly: bool
    features: dict[str, Any]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.record_id = data.get("record_id", "")
        self.anomaly_score = float(data.get("anomaly_score", 0))
        self.is_anomaly = bool(data.get("is_anomaly", False))
        self.features = data.get("features", {})


class AnomalyKpiBlock(EchoIntelResponse):
    """KPI-level anomaly metrics."""

    kpi_name: str
    anomaly_count: int
    normal_count: int
    anomaly_rate: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.kpi_name = data.get("kpi_name", "")
        self.anomaly_count = int(data.get("anomaly_count", 0))
        self.normal_count = int(data.get("normal_count", 0))
        self.anomaly_rate = float(data.get("anomaly_rate", 0))


class TabularResponse(EchoIntelResponse):
    """Response for tabular anomaly detection endpoints."""

    anomalies: list[AnomalyDetail]
    total_records: int
    anomaly_count: int
    kpi_breakdown: list[AnomalyKpiBlock]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.anomalies = [
            AnomalyDetail.from_dict(item) for item in data.get("anomalies", [])
        ]
        self.total_records = int(data.get("total_records", 0))
        self.anomaly_count = int(data.get("anomaly_count", 0))
        self.kpi_breakdown = [
            AnomalyKpiBlock.from_dict(item) for item in data.get("kpi_breakdown", [])
        ]


class GraphDetail(EchoIntelResponse):
    """Graph-based anomaly detection result."""

    node_id: str
    anomaly_score: float
    is_anomaly: bool
    connected_anomalies: list[str]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.node_id = data.get("node_id", "")
        self.anomaly_score = float(data.get("anomaly_score", 0))
        self.is_anomaly = bool(data.get("is_anomaly", False))
        self.connected_anomalies = data.get("connected_anomalies", [])


class GraphResponse(EchoIntelResponse):
    """Response for graph-based anomaly detection endpoint."""

    anomalies: list[GraphDetail]
    total_nodes: int
    anomaly_count: int

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.anomalies = [
            GraphDetail.from_dict(item) for item in data.get("anomalies", [])
        ]
        self.total_nodes = int(data.get("total_nodes", 0))
        self.anomaly_count = int(data.get("anomaly_count", 0))
