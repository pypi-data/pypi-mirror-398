"""EchoIntel SDK response classes."""

from __future__ import annotations

# Base
from echointel.responses.base import EchoIntelResponse

# Forecast
from echointel.responses.forecast import (
    ForecastValue,
    ForecastEvaluationMetrics,
    ForecastData,
    ForecastAlgorithmResult,
    ForecastUnitsResponse,
)

# Inventory
from echointel.responses.inventory import (
    DailyInventoryRecord,
    ProductDetails,
    ProcessingInfo,
    InventoryHistoryResponse,
)

# Customer
from echointel.responses.customer import (
    AlgorithmMetrics,
    ClusterDetail,
    CustomerLabel,
    SegmentationResponse,
    FeaturesObject,
    BuildFeaturesResponse,
    CustomerScore,
    LoyaltySummary,
    LoyaltyResponse,
    RfmCustomerOut,
    RfmResponse,
    ClvFeatureOut,
    ClvFeaturesResponse,
    ClvForecastCustomer,
    ClvForecastResponse,
)

# Churn
from echointel.responses.churn import ChurnLabelResponse

# Propensity
from echointel.responses.propensity import PropensityResponse

# Recommendation
from echointel.responses.recommendation import (
    ModelInfo,
    RecommendationOut,
    RecResponse,
)

# Cross-Sell
from echointel.responses.cross_sell import (
    CrossSellResponse,
    UpsellPair,
    UpsellResponse,
)

# Pricing
from echointel.responses.pricing import (
    PriceOutcome,
    PricingResponse,
)

# Sentiment
from echointel.responses.sentiment import (
    SentimentDetail,
    SentimentKpiBlock,
    ReportResponse,
    RealtimeResponse,
)

# Anomaly
from echointel.responses.anomaly import (
    AnomalyDetail,
    AnomalyKpiBlock,
    TabularResponse,
    GraphDetail,
    GraphResponse,
)

# Credit Risk
from echointel.responses.credit_risk import (
    Prediction,
    ScoreResponse,
    ExplainResponse,
)

# Attribution
from echointel.responses.attribution import (
    ChannelContribution,
    AttributionResponse,
    DecileSummary,
    UpliftDetail,
    UpliftResponse,
)

# Journey
from echointel.responses.journey import (
    Transition,
    MarkovResponse,
    Path,
    SequenceResponse,
)

# Admin
from echointel.responses.admin import CustomerOut

__all__ = [
    # Base
    "EchoIntelResponse",
    # Forecast
    "ForecastValue",
    "ForecastEvaluationMetrics",
    "ForecastData",
    "ForecastAlgorithmResult",
    "ForecastUnitsResponse",
    # Inventory
    "DailyInventoryRecord",
    "ProductDetails",
    "ProcessingInfo",
    "InventoryHistoryResponse",
    # Customer
    "AlgorithmMetrics",
    "ClusterDetail",
    "CustomerLabel",
    "SegmentationResponse",
    "FeaturesObject",
    "BuildFeaturesResponse",
    "CustomerScore",
    "LoyaltySummary",
    "LoyaltyResponse",
    "RfmCustomerOut",
    "RfmResponse",
    "ClvFeatureOut",
    "ClvFeaturesResponse",
    "ClvForecastCustomer",
    "ClvForecastResponse",
    # Churn
    "ChurnLabelResponse",
    # Propensity
    "PropensityResponse",
    # Recommendation
    "ModelInfo",
    "RecommendationOut",
    "RecResponse",
    # Cross-Sell
    "CrossSellResponse",
    "UpsellPair",
    "UpsellResponse",
    # Pricing
    "PriceOutcome",
    "PricingResponse",
    # Sentiment
    "SentimentDetail",
    "SentimentKpiBlock",
    "ReportResponse",
    "RealtimeResponse",
    # Anomaly
    "AnomalyDetail",
    "AnomalyKpiBlock",
    "TabularResponse",
    "GraphDetail",
    "GraphResponse",
    # Credit Risk
    "Prediction",
    "ScoreResponse",
    "ExplainResponse",
    # Attribution
    "ChannelContribution",
    "AttributionResponse",
    "DecileSummary",
    "UpliftDetail",
    "UpliftResponse",
    # Journey
    "Transition",
    "MarkovResponse",
    "Path",
    "SequenceResponse",
    # Admin
    "CustomerOut",
]
