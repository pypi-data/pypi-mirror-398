"""Customer analytics response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class AlgorithmMetrics(EchoIntelResponse):
    """Metrics for a clustering algorithm."""

    algorithm: str
    params: dict[str, Any]
    silhouette: float | None
    davies_bouldin: float | None
    calinski_harabasz: float | None
    n_clusters: int | None

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.algorithm = data.get("algorithm", "")
        self.params = data.get("params", {})
        self.silhouette = float(data["silhouette"]) if "silhouette" in data else None
        self.davies_bouldin = (
            float(data["davies_bouldin"]) if "davies_bouldin" in data else None
        )
        self.calinski_harabasz = (
            float(data["calinski_harabasz"]) if "calinski_harabasz" in data else None
        )
        self.n_clusters = int(data["n_clusters"]) if "n_clusters" in data else None


class ClusterDetail(EchoIntelResponse):
    """Details about a customer cluster."""

    cluster_id: int
    size: int
    centroid: list[float]
    persona_label: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.cluster_id = int(data.get("cluster_id", 0))
        self.size = int(data.get("size", 0))
        self.centroid = data.get("centroid", [])
        self.persona_label = data.get("persona_label", "")


class CustomerLabel(EchoIntelResponse):
    """Customer segment label assignment."""

    customer_id: str
    cluster_id: int

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.cluster_id = int(data.get("cluster_id", 0))


class SegmentationResponse(EchoIntelResponse):
    """Response for customer segmentation endpoint."""

    best_algorithm: str
    evaluation_metrics: list[AlgorithmMetrics]
    clusters: list[ClusterDetail]
    customer_labels: list[CustomerLabel]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.best_algorithm = data.get("best_algorithm", "")
        self.evaluation_metrics = [
            AlgorithmMetrics.from_dict(item)
            for item in data.get("evaluation_metrics", [])
        ]
        self.clusters = [
            ClusterDetail.from_dict(item) for item in data.get("clusters", [])
        ]
        self.customer_labels = [
            CustomerLabel.from_dict(item) for item in data.get("customer_labels", [])
        ]


class FeaturesObject(EchoIntelResponse):
    """Container for customer features."""

    features: dict[str, Any]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.features = data.get("features", {})


class BuildFeaturesResponse(EchoIntelResponse):
    """Response for feature building endpoint."""

    customers: list[FeaturesObject]
    feature_names: list[str]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customers = [
            FeaturesObject.from_dict(item) for item in data.get("customers", [])
        ]
        self.feature_names = data.get("feature_names", [])


class CustomerScore(EchoIntelResponse):
    """Customer loyalty score."""

    customer_id: str
    loyalty_score: float
    tier: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.loyalty_score = float(data.get("loyalty_score", 0))
        self.tier = data.get("tier", "")


class LoyaltySummary(EchoIntelResponse):
    """Summary of loyalty analysis."""

    total_customers: int
    avg_loyalty_score: float
    tier_distribution: dict[str, int]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.total_customers = int(data.get("total_customers", 0))
        self.avg_loyalty_score = float(data.get("avg_loyalty_score", 0))
        self.tier_distribution = data.get("tier_distribution", {})


class LoyaltyResponse(EchoIntelResponse):
    """Response for customer loyalty endpoint."""

    customers: list[CustomerScore]
    summary: LoyaltySummary

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customers = [
            CustomerScore.from_dict(item) for item in data.get("customers", [])
        ]
        self.summary = LoyaltySummary.from_dict(data.get("summary", {}))


class RfmCustomerOut(EchoIntelResponse):
    """Customer RFM (Recency, Frequency, Monetary) data."""

    customer_id: str
    recency: int
    frequency: int
    monetary: float
    r_score: int
    f_score: int
    m_score: int
    rfm_score: str
    segment: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.recency = int(data.get("recency", 0))
        self.frequency = int(data.get("frequency", 0))
        self.monetary = float(data.get("monetary", 0))
        self.r_score = int(data.get("r_score", 0))
        self.f_score = int(data.get("f_score", 0))
        self.m_score = int(data.get("m_score", 0))
        self.rfm_score = data.get("rfm_score", "")
        self.segment = data.get("segment", "")


class RfmResponse(EchoIntelResponse):
    """Response for RFM analysis endpoint."""

    customers: list[RfmCustomerOut]
    segment_summary: dict[str, int]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customers = [
            RfmCustomerOut.from_dict(item) for item in data.get("customers", [])
        ]
        self.segment_summary = data.get("segment_summary", {})


class ClvFeatureOut(EchoIntelResponse):
    """Customer CLV (Customer Lifetime Value) features."""

    customer_id: str
    total_revenue: float
    avg_order_value: float
    order_count: int
    customer_age_days: int
    purchase_frequency: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.total_revenue = float(data.get("total_revenue", 0))
        self.avg_order_value = float(data.get("avg_order_value", 0))
        self.order_count = int(data.get("order_count", 0))
        self.customer_age_days = int(data.get("customer_age_days", 0))
        self.purchase_frequency = float(data.get("purchase_frequency", 0))


class ClvFeaturesResponse(EchoIntelResponse):
    """Response for CLV features endpoint."""

    customers: list[ClvFeatureOut]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customers = [
            ClvFeatureOut.from_dict(item) for item in data.get("customers", [])
        ]


class ClvForecastCustomer(EchoIntelResponse):
    """Customer CLV forecast."""

    customer_id: str
    predicted_clv: float
    confidence_lower: float
    confidence_upper: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.customer_id = data.get("customer_id", "")
        self.predicted_clv = float(data.get("predicted_clv", 0))
        self.confidence_lower = float(data.get("confidence_lower", 0))
        self.confidence_upper = float(data.get("confidence_upper", 0))


class ClvForecastResponse(EchoIntelResponse):
    """Response for CLV forecast endpoint."""

    best_algorithm: str
    horizon_months: int
    evaluation_mae: float
    customers: list[ClvForecastCustomer]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.best_algorithm = data.get("best_algorithm", "")
        self.horizon_months = int(data.get("horizon_months", 0))
        self.evaluation_mae = float(data.get("evaluation_mae", 0))
        self.customers = [
            ClvForecastCustomer.from_dict(item) for item in data.get("customers", [])
        ]
