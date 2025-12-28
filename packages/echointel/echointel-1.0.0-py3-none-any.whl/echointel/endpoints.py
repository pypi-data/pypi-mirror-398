"""API endpoint constants for EchoIntel SDK."""

from __future__ import annotations


class Endpoints:
    """API endpoint constants organized by category."""

    BASE_URL = "https://ai.echosistema.live"

    # System
    HEALTH = "/health"

    # Forecasting
    FORECAST_REVENUE = "/api/forecast_revenue"
    FORECAST_COST = "/api/forecast_cost"
    FORECAST_COST_IMPROVED = "/api/forecast_cost_improved"
    FORECAST_UNITS = "/api/forecast_units"
    FORECAST_COST_TOTUS = "/api/forecast_cost_totus"

    # Inventory
    INVENTORY_OPTIMIZATION = "/api/inventory_optimization"
    INVENTORY_HISTORY_IMPROVED = "/api/inventory_history_improved"

    # Customer Analytics
    CUSTOMER_SEGMENTATION = "/api/customer_segmentation"
    CUSTOMER_FEATURES = "/api/customer_features"
    CUSTOMER_LOYALTY = "/api/customer_loyalty"
    CUSTOMER_RFM = "/api/customer_rfm"
    CUSTOMER_CLV_FEATURES = "/api/customer_clv_features"
    CUSTOMER_CLV_FORECAST = "/api/customer_clv_forecast"

    # Churn
    CHURN_RISK = "/api/churn_risk"
    CHURN_LABEL = "/api/churn_label"

    # NPS
    NPS = "/api/nps"

    # Propensity
    PROPENSITY_BUY_PRODUCT = "/api/propensity_buy_product"
    PROPENSITY_RESPOND_CAMPAIGN = "/api/propensity_respond_campaign"
    PROPENSITY_UPGRADE_PLAN = "/api/propensity_upgrade_plan"

    # Recommendations
    RECOMMEND_USER_ITEMS = "/api/recommend_user_items"
    RECOMMEND_SIMILAR_ITEMS = "/api/recommend_similar_items"

    # Cross-Sell & Upsell
    CROSS_SELL_MATRIX = "/api/cross_sell_matrix"
    UPSELL_SUGGESTIONS = "/api/upsell_suggestions"

    # Dynamic Pricing
    DYNAMIC_PRICING_RECOMMEND = "/api/dynamic_pricing_recommend"

    # Sentiment
    SENTIMENT_REPORT = "/api/sentiment_report"
    SENTIMENT_REALTIME = "/api/sentiment_realtime"

    # Anomaly Detection
    ANOMALY_TRANSACTIONS = "/api/anomaly_transactions"
    ANOMALY_ACCOUNTS = "/api/anomaly_accounts"
    ANOMALY_GRAPH = "/api/anomaly_graph"

    # Credit Risk
    CREDIT_RISK_SCORE = "/api/credit_risk_score"
    CREDIT_RISK_EXPLAIN = "/api/credit_risk_explain"

    # Marketing Attribution
    CHANNEL_ATTRIBUTION = "/api/channel_attribution"
    UPLIFT_MODEL = "/api/uplift_model"

    # Customer Journey
    JOURNEY_MARKOV = "/api/journey_markov"
    JOURNEY_SEQUENCES = "/api/journey_sequences"

    # NLP
    NLP_ANALYSIS = "/api/nlp_analisys"
    NLP_ANALYSIS_EN = "/api/nlp_analisys_en"
    NLP_EXCESS_INVENTORY_REPORT = "/api/nlp_openai_excess_inventory_report"
    SANITIZE_TEXT = "/api/sanitize_text"

    # Advanced Segmentation (Admin)
    PURCHASING_SEGMENTATION = "/api/purchasing_segmentation"
    PURCHASING_SEGMENTATION_DENDROGRAM = "/api/purchasing_segmentation_dendrogram"
    SEGMENT_HIERARCHY_CHART = "/api/segment_hierarchy_chart"
    SEGMENT_SUBSEGMENT_EXPLORE = "/api/segment_subsegment_explore"
    SEGMENT_CLUSTER_PROFILES = "/api/segment_cluster_profiles"

    # Reporting (Admin)
    SEGMENTATION_REPORT = "/api/segmentation_report"
    SEGMENTATION_REPORT_I18N = "/api/segmentation_report_i18n"
    SEGMENTATION_REPORT_JSON = "/api/segmentation_report_json"

    # Admin
    ADMIN_CUSTOMERS = "/admin/customers"

    @classmethod
    def all(cls) -> dict[str, dict[str, str]]:
        """Get all endpoints grouped by category.

        Returns:
            Dictionary with category names as keys and endpoint dictionaries as values.
        """
        return {
            "system": {
                "health": cls.HEALTH,
            },
            "forecasting": {
                "revenue": cls.FORECAST_REVENUE,
                "cost": cls.FORECAST_COST,
                "cost_improved": cls.FORECAST_COST_IMPROVED,
                "units": cls.FORECAST_UNITS,
                "cost_totus": cls.FORECAST_COST_TOTUS,
            },
            "inventory": {
                "optimization": cls.INVENTORY_OPTIMIZATION,
                "history_improved": cls.INVENTORY_HISTORY_IMPROVED,
            },
            "customer": {
                "segmentation": cls.CUSTOMER_SEGMENTATION,
                "features": cls.CUSTOMER_FEATURES,
                "loyalty": cls.CUSTOMER_LOYALTY,
                "rfm": cls.CUSTOMER_RFM,
                "clv_features": cls.CUSTOMER_CLV_FEATURES,
                "clv_forecast": cls.CUSTOMER_CLV_FORECAST,
            },
            "churn": {
                "risk": cls.CHURN_RISK,
                "label": cls.CHURN_LABEL,
            },
            "nps": {
                "calculate": cls.NPS,
            },
            "propensity": {
                "buy_product": cls.PROPENSITY_BUY_PRODUCT,
                "respond_campaign": cls.PROPENSITY_RESPOND_CAMPAIGN,
                "upgrade_plan": cls.PROPENSITY_UPGRADE_PLAN,
            },
            "recommendations": {
                "user_items": cls.RECOMMEND_USER_ITEMS,
                "similar_items": cls.RECOMMEND_SIMILAR_ITEMS,
            },
            "cross_sell": {
                "matrix": cls.CROSS_SELL_MATRIX,
                "upsell": cls.UPSELL_SUGGESTIONS,
            },
            "pricing": {
                "dynamic": cls.DYNAMIC_PRICING_RECOMMEND,
            },
            "sentiment": {
                "report": cls.SENTIMENT_REPORT,
                "realtime": cls.SENTIMENT_REALTIME,
            },
            "anomaly": {
                "transactions": cls.ANOMALY_TRANSACTIONS,
                "accounts": cls.ANOMALY_ACCOUNTS,
                "graph": cls.ANOMALY_GRAPH,
            },
            "credit_risk": {
                "score": cls.CREDIT_RISK_SCORE,
                "explain": cls.CREDIT_RISK_EXPLAIN,
            },
            "attribution": {
                "channel": cls.CHANNEL_ATTRIBUTION,
                "uplift": cls.UPLIFT_MODEL,
            },
            "journey": {
                "markov": cls.JOURNEY_MARKOV,
                "sequences": cls.JOURNEY_SEQUENCES,
            },
            "nlp": {
                "analysis": cls.NLP_ANALYSIS,
                "analysis_en": cls.NLP_ANALYSIS_EN,
                "excess_inventory": cls.NLP_EXCESS_INVENTORY_REPORT,
                "sanitize": cls.SANITIZE_TEXT,
            },
            "segmentation_admin": {
                "purchasing": cls.PURCHASING_SEGMENTATION,
                "dendrogram": cls.PURCHASING_SEGMENTATION_DENDROGRAM,
                "hierarchy": cls.SEGMENT_HIERARCHY_CHART,
                "subsegment": cls.SEGMENT_SUBSEGMENT_EXPLORE,
                "profiles": cls.SEGMENT_CLUSTER_PROFILES,
            },
            "reporting_admin": {
                "report": cls.SEGMENTATION_REPORT,
                "report_i18n": cls.SEGMENTATION_REPORT_I18N,
                "report_json": cls.SEGMENTATION_REPORT_JSON,
            },
            "admin": {
                "customers": cls.ADMIN_CUSTOMERS,
            },
        }
