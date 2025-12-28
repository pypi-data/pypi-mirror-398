"""Async EchoIntel API client for Python."""

from __future__ import annotations

import os
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from echointel.endpoints import Endpoints
from echointel.exceptions import (
    EchoIntelAuthenticationException,
    EchoIntelException,
    EchoIntelValidationException,
)
from echointel.route_resolver import RouteResolver


class AsyncEchoIntelClient:
    """Asynchronous client for the EchoIntel API.

    This client provides async access to all EchoIntel AI endpoints including
    forecasting, customer segmentation, inventory optimization, and more.

    Example:
        ```python
        async with AsyncEchoIntelClient(
            customer_api_id="your-api-id",
            secret="your-secret"
        ) as client:
            result = await client.forecast_revenue({"sales": [...]})
        ```
    """

    def __init__(
        self,
        base_url: str | None = None,
        customer_api_id: str | None = None,
        secret: str | None = None,
        admin_secret: str | None = None,
        timeout: int | None = None,
        retry_attempts: int = 3,
        retry_delay: float = 0.1,
    ) -> None:
        """Initialize the async EchoIntel client.

        Args:
            base_url: API base URL. Defaults to ECHOINTEL_API_URL env var or
                     https://ai.echosistema.live
            customer_api_id: Customer API ID. Defaults to ECHOINTEL_CUSTOMER_API_ID env var.
            secret: API secret. Defaults to ECHOINTEL_SECRET env var.
            admin_secret: Admin secret for admin operations.
                         Defaults to ECHOINTEL_ADMIN_SECRET env var.
            timeout: Request timeout in seconds. Defaults to ECHOINTEL_TIMEOUT env var or 30.
            retry_attempts: Number of retry attempts for failed requests.
            retry_delay: Base delay in seconds between retries.
        """
        self.base_url = (
            base_url
            or os.getenv("ECHOINTEL_API_URL", Endpoints.BASE_URL)
        ).rstrip("/")
        self.customer_api_id = customer_api_id or os.getenv("ECHOINTEL_CUSTOMER_API_ID")
        self.secret = secret or os.getenv("ECHOINTEL_SECRET")
        self.admin_secret = admin_secret or os.getenv("ECHOINTEL_ADMIN_SECRET")
        self.timeout = timeout or int(os.getenv("ECHOINTEL_TIMEOUT", "30"))
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self) -> "AsyncEchoIntelClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    # =========================================================================
    # SYSTEM
    # =========================================================================

    async def health(self) -> dict[str, Any]:
        """Check API health status.

        Returns:
            Health status response.
        """
        return await self._request("GET", Endpoints.HEALTH)

    # =========================================================================
    # FORECASTING
    # =========================================================================

    async def forecast_revenue(self, data: dict[str, Any]) -> dict[str, Any]:
        """Forecast revenue based on historical data.

        Args:
            data: Historical revenue data.

        Returns:
            Revenue forecast results.
        """
        return await self._request("POST", Endpoints.FORECAST_REVENUE, data)

    async def forecast_cost(self, data: dict[str, Any]) -> dict[str, Any]:
        """Forecast cost based on historical data.

        Args:
            data: Historical cost data.

        Returns:
            Cost forecast results.
        """
        return await self._request("POST", Endpoints.FORECAST_COST, data)

    async def forecast_cost_improved(self, data: dict[str, Any]) -> dict[str, Any]:
        """Forecast cost using improved algorithms.

        Args:
            data: Historical cost data.

        Returns:
            Improved cost forecast results.
        """
        return await self._request("POST", Endpoints.FORECAST_COST_IMPROVED, data)

    async def forecast_units(self, data: dict[str, Any]) -> dict[str, Any]:
        """Forecast units/quantity based on historical data.

        Args:
            data: Historical units data.

        Returns:
            Units forecast results.
        """
        return await self._request("POST", Endpoints.FORECAST_UNITS, data)

    async def forecast_cost_totus(self, data: dict[str, Any]) -> dict[str, Any]:
        """Forecast cost using Totus algorithm.

        Args:
            data: Historical cost data.

        Returns:
            Cost forecast results using Totus.
        """
        return await self._request("POST", Endpoints.FORECAST_COST_TOTUS, data)

    # =========================================================================
    # INVENTORY
    # =========================================================================

    async def inventory_optimization(self, data: dict[str, Any]) -> dict[str, Any]:
        """Optimize inventory levels.

        Args:
            data: Inventory data for optimization.

        Returns:
            Inventory optimization recommendations.
        """
        return await self._request("POST", Endpoints.INVENTORY_OPTIMIZATION, data)

    async def inventory_history_improved(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze inventory history with improved algorithms.

        Args:
            data: Historical inventory data.

        Returns:
            Inventory analysis results.
        """
        return await self._request("POST", Endpoints.INVENTORY_HISTORY_IMPROVED, data)

    # =========================================================================
    # CUSTOMER ANALYTICS
    # =========================================================================

    async def customer_segmentation(self, data: dict[str, Any]) -> dict[str, Any]:
        """Segment customers based on behavior and attributes.

        Args:
            data: Customer data for segmentation.

        Returns:
            Segmentation results with clusters.
        """
        return await self._request("POST", Endpoints.CUSTOMER_SEGMENTATION, data)

    async def customer_features(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build customer features for analysis.

        Args:
            data: Customer transaction data.

        Returns:
            Extracted customer features.
        """
        return await self._request("POST", Endpoints.CUSTOMER_FEATURES, data)

    async def customer_loyalty(self, data: dict[str, Any]) -> dict[str, Any]:
        """Calculate customer loyalty scores.

        Args:
            data: Customer data for loyalty analysis.

        Returns:
            Loyalty scores and tiers.
        """
        return await self._request("POST", Endpoints.CUSTOMER_LOYALTY, data)

    async def customer_rfm(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform RFM (Recency, Frequency, Monetary) analysis.

        Args:
            data: Customer transaction data.

        Returns:
            RFM analysis results.
        """
        return await self._request("POST", Endpoints.CUSTOMER_RFM, data)

    async def customer_clv_features(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract CLV (Customer Lifetime Value) features.

        Args:
            data: Customer transaction data.

        Returns:
            CLV feature extraction results.
        """
        return await self._request("POST", Endpoints.CUSTOMER_CLV_FEATURES, data)

    async def customer_clv_forecast(self, data: dict[str, Any]) -> dict[str, Any]:
        """Forecast Customer Lifetime Value.

        Args:
            data: Customer data for CLV prediction.

        Returns:
            CLV forecast results.
        """
        return await self._request("POST", Endpoints.CUSTOMER_CLV_FORECAST, data)

    # =========================================================================
    # CHURN ANALYSIS
    # =========================================================================

    async def churn_risk(self, data: dict[str, Any]) -> dict[str, Any]:
        """Predict customer churn risk.

        Args:
            data: Customer data for churn prediction.

        Returns:
            Churn risk predictions.
        """
        return await self._request("POST", Endpoints.CHURN_RISK, data)

    async def churn_label(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate churn labels for customers.

        Args:
            data: Customer data for churn labeling.

        Returns:
            Churn label results.
        """
        return await self._request("POST", Endpoints.CHURN_LABEL, data)

    # =========================================================================
    # NPS
    # =========================================================================

    async def nps(self, data: dict[str, Any]) -> dict[str, Any]:
        """Calculate Net Promoter Score.

        Args:
            data: Survey data for NPS calculation.

        Returns:
            NPS analysis results.
        """
        return await self._request("POST", Endpoints.NPS, data)

    # =========================================================================
    # PROPENSITY MODELING
    # =========================================================================

    async def propensity_buy_product(self, data: dict[str, Any]) -> dict[str, Any]:
        """Predict propensity to buy a product.

        Args:
            data: Customer and product data.

        Returns:
            Purchase propensity predictions.
        """
        return await self._request("POST", Endpoints.PROPENSITY_BUY_PRODUCT, data)

    async def propensity_respond_campaign(self, data: dict[str, Any]) -> dict[str, Any]:
        """Predict propensity to respond to a campaign.

        Args:
            data: Customer and campaign data.

        Returns:
            Campaign response propensity predictions.
        """
        return await self._request("POST", Endpoints.PROPENSITY_RESPOND_CAMPAIGN, data)

    async def propensity_upgrade_plan(self, data: dict[str, Any]) -> dict[str, Any]:
        """Predict propensity to upgrade plan.

        Args:
            data: Customer and plan data.

        Returns:
            Upgrade propensity predictions.
        """
        return await self._request("POST", Endpoints.PROPENSITY_UPGRADE_PLAN, data)

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================

    async def recommend_user_items(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get personalized item recommendations for users.

        Args:
            data: User and item interaction data.

        Returns:
            Item recommendations for users.
        """
        return await self._request("POST", Endpoints.RECOMMEND_USER_ITEMS, data)

    async def recommend_similar_items(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get similar item recommendations.

        Args:
            data: Item data for similarity matching.

        Returns:
            Similar item recommendations.
        """
        return await self._request("POST", Endpoints.RECOMMEND_SIMILAR_ITEMS, data)

    # =========================================================================
    # CROSS-SELL & UPSELL
    # =========================================================================

    async def cross_sell_matrix(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate cross-sell opportunity matrix.

        Args:
            data: Transaction data for cross-sell analysis.

        Returns:
            Cross-sell matrix results.
        """
        return await self._request("POST", Endpoints.CROSS_SELL_MATRIX, data)

    async def upsell_suggestions(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate upsell suggestions.

        Args:
            data: Product and customer data.

        Returns:
            Upsell suggestions.
        """
        return await self._request("POST", Endpoints.UPSELL_SUGGESTIONS, data)

    # =========================================================================
    # DYNAMIC PRICING
    # =========================================================================

    async def dynamic_pricing_recommend(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get dynamic pricing recommendations.

        Args:
            data: Product and market data.

        Returns:
            Pricing recommendations.
        """
        return await self._request("POST", Endpoints.DYNAMIC_PRICING_RECOMMEND, data)

    # =========================================================================
    # SENTIMENT ANALYSIS
    # =========================================================================

    async def sentiment_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate sentiment analysis report.

        Args:
            data: Text data for sentiment analysis.

        Returns:
            Sentiment report results.
        """
        return await self._request("POST", Endpoints.SENTIMENT_REPORT, data)

    async def sentiment_realtime(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze sentiment in real-time.

        Args:
            data: Text data for real-time analysis.

        Returns:
            Real-time sentiment results.
        """
        return await self._request("POST", Endpoints.SENTIMENT_REALTIME, data)

    # =========================================================================
    # ANOMALY DETECTION
    # =========================================================================

    async def anomaly_transactions(self, data: dict[str, Any]) -> dict[str, Any]:
        """Detect anomalies in transactions.

        Args:
            data: Transaction data for anomaly detection.

        Returns:
            Transaction anomaly results.
        """
        return await self._request("POST", Endpoints.ANOMALY_TRANSACTIONS, data)

    async def anomaly_accounts(self, data: dict[str, Any]) -> dict[str, Any]:
        """Detect anomalies in accounts.

        Args:
            data: Account data for anomaly detection.

        Returns:
            Account anomaly results.
        """
        return await self._request("POST", Endpoints.ANOMALY_ACCOUNTS, data)

    async def anomaly_graph(self, data: dict[str, Any]) -> dict[str, Any]:
        """Detect anomalies using graph-based methods.

        Args:
            data: Graph data for anomaly detection.

        Returns:
            Graph anomaly results.
        """
        return await self._request("POST", Endpoints.ANOMALY_GRAPH, data)

    # =========================================================================
    # CREDIT RISK
    # =========================================================================

    async def credit_risk_score(self, data: dict[str, Any]) -> dict[str, Any]:
        """Calculate credit risk scores.

        Args:
            data: Customer financial data.

        Returns:
            Credit risk scores.
        """
        return await self._request("POST", Endpoints.CREDIT_RISK_SCORE, data)

    async def credit_risk_explain(self, data: dict[str, Any]) -> dict[str, Any]:
        """Explain credit risk predictions.

        Args:
            data: Customer data for explanation.

        Returns:
            Credit risk explanation.
        """
        return await self._request("POST", Endpoints.CREDIT_RISK_EXPLAIN, data)

    # =========================================================================
    # MARKETING ATTRIBUTION
    # =========================================================================

    async def channel_attribution(self, data: dict[str, Any]) -> dict[str, Any]:
        """Calculate marketing channel attribution.

        Args:
            data: Marketing channel data.

        Returns:
            Channel attribution results.
        """
        return await self._request("POST", Endpoints.CHANNEL_ATTRIBUTION, data)

    async def uplift_model(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build uplift model for campaign targeting.

        Args:
            data: Campaign and customer data.

        Returns:
            Uplift model results.
        """
        return await self._request("POST", Endpoints.UPLIFT_MODEL, data)

    # =========================================================================
    # CUSTOMER JOURNEY
    # =========================================================================

    async def journey_markov(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze customer journey using Markov chains.

        Args:
            data: Customer journey data.

        Returns:
            Markov chain analysis results.
        """
        return await self._request("POST", Endpoints.JOURNEY_MARKOV, data)

    async def journey_sequences(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze customer journey sequences.

        Args:
            data: Customer journey data.

        Returns:
            Journey sequence analysis results.
        """
        return await self._request("POST", Endpoints.JOURNEY_SEQUENCES, data)

    # =========================================================================
    # NLP & TEXT PROCESSING
    # =========================================================================

    async def nlp_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform NLP analysis on Portuguese text.

        Args:
            data: Text data for NLP analysis.

        Returns:
            NLP analysis results.
        """
        return await self._request("POST", Endpoints.NLP_ANALYSIS, data)

    async def nlp_analysis_en(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform NLP analysis on English text.

        Args:
            data: Text data for NLP analysis.

        Returns:
            NLP analysis results.
        """
        return await self._request("POST", Endpoints.NLP_ANALYSIS_EN, data)

    async def nlp_excess_inventory_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate excess inventory report using NLP.

        Args:
            data: Inventory data for analysis.

        Returns:
            Excess inventory report.
        """
        return await self._request("POST", Endpoints.NLP_EXCESS_INVENTORY_REPORT, data)

    async def sanitize_text(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize and clean text data.

        Args:
            data: Text data for sanitization.

        Returns:
            Sanitized text results.
        """
        return await self._request("POST", Endpoints.SANITIZE_TEXT, data)

    # =========================================================================
    # ADVANCED SEGMENTATION (ADMIN)
    # =========================================================================

    async def purchasing_segmentation(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform purchasing-based segmentation.

        Args:
            data: Purchase data for segmentation.

        Returns:
            Purchasing segmentation results.
        """
        return await self._request(
            "POST", Endpoints.PURCHASING_SEGMENTATION, data, with_auth=True
        )

    async def purchasing_segmentation_dendrogram(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate dendrogram for purchasing segmentation.

        Args:
            data: Purchase data for dendrogram.

        Returns:
            Dendrogram visualization data.
        """
        return await self._request(
            "POST", Endpoints.PURCHASING_SEGMENTATION_DENDROGRAM, data, with_auth=True
        )

    async def segment_hierarchy_chart(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate segment hierarchy chart.

        Args:
            data: Segmentation data.

        Returns:
            Hierarchy chart data.
        """
        return await self._request(
            "POST", Endpoints.SEGMENT_HIERARCHY_CHART, data, with_auth=True
        )

    async def segment_subsegment_explore(self, data: dict[str, Any]) -> dict[str, Any]:
        """Explore segment and subsegment relationships.

        Args:
            data: Segmentation data.

        Returns:
            Subsegment exploration results.
        """
        return await self._request(
            "POST", Endpoints.SEGMENT_SUBSEGMENT_EXPLORE, data, with_auth=True
        )

    async def segment_cluster_profiles(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate cluster profiles for segments.

        Args:
            data: Segmentation data.

        Returns:
            Cluster profile data.
        """
        return await self._request(
            "POST", Endpoints.SEGMENT_CLUSTER_PROFILES, data, with_auth=True
        )

    # =========================================================================
    # REPORTING (ADMIN)
    # =========================================================================

    async def segmentation_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate segmentation report.

        Args:
            data: Segmentation data for report.

        Returns:
            Segmentation report.
        """
        return await self._request(
            "POST", Endpoints.SEGMENTATION_REPORT, data, with_auth=True
        )

    async def segmentation_report_i18n(
        self, data: dict[str, Any], lang: str = "pt"
    ) -> dict[str, Any]:
        """Generate internationalized segmentation report.

        Args:
            data: Segmentation data for report.
            lang: Language code (pt, es).

        Returns:
            Localized segmentation report.
        """
        endpoint = f"{Endpoints.SEGMENTATION_REPORT_I18N}?lang={lang}"
        return await self._request("POST", endpoint, data, with_auth=True)

    async def segmentation_report_json(
        self, data: dict[str, Any], lang: str = "en"
    ) -> dict[str, Any]:
        """Generate JSON segmentation report.

        Args:
            data: Segmentation data for report.
            lang: Language code (pt, es, en).

        Returns:
            JSON segmentation report.
        """
        endpoint = f"{Endpoints.SEGMENTATION_REPORT_JSON}?lang={lang}"
        return await self._request("POST", endpoint, data, with_auth=True)

    # =========================================================================
    # ADMIN OPERATIONS
    # =========================================================================

    async def create_customer(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new customer.

        Args:
            data: Customer data including allowed_routes.

        Returns:
            Created customer details.
        """
        if "allowed_routes" in data:
            data["allowed_routes"] = RouteResolver.resolve(data["allowed_routes"])

        return await self._request_admin("POST", Endpoints.ADMIN_CUSTOMERS, data)

    async def list_customers(self, include_disabled: bool = False) -> dict[str, Any]:
        """List all customers.

        Args:
            include_disabled: Include disabled customers in response.

        Returns:
            List of customers.
        """
        query = "?include_disabled=true" if include_disabled else ""
        return await self._request_admin("GET", f"{Endpoints.ADMIN_CUSTOMERS}{query}")

    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        """Get customer details.

        Args:
            customer_id: Customer API ID.

        Returns:
            Customer details.
        """
        return await self._request_admin(
            "GET", f"{Endpoints.ADMIN_CUSTOMERS}/{customer_id}"
        )

    async def update_customer(
        self, customer_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update customer details.

        Args:
            customer_id: Customer API ID.
            data: Updated customer data.

        Returns:
            Updated customer details.
        """
        if "allowed_routes" in data:
            data["allowed_routes"] = RouteResolver.resolve(data["allowed_routes"])

        return await self._request_admin(
            "PUT", f"{Endpoints.ADMIN_CUSTOMERS}/{customer_id}", data
        )

    async def delete_customer(self, customer_id: str) -> dict[str, Any]:
        """Delete a customer.

        Args:
            customer_id: Customer API ID.

        Returns:
            Deletion confirmation.
        """
        return await self._request_admin(
            "DELETE", f"{Endpoints.ADMIN_CUSTOMERS}/{customer_id}"
        )

    # =========================================================================
    # HTTP METHODS
    # =========================================================================

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        with_auth: bool = False,
    ) -> dict[str, Any]:
        """Make an async API request.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            data: Request data.
            with_auth: Include authentication headers.

        Returns:
            API response data.
        """
        headers = self._get_auth_headers() if with_auth else {}
        return await self._execute_request(method, endpoint, data, headers)

    async def _request_admin(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an async admin API request.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            data: Request data.

        Returns:
            API response data.
        """
        headers = {"X-ADMIN-SECRET": self.admin_secret or ""}
        return await self._execute_request(method, endpoint, data, headers)

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers.

        Returns:
            Dictionary of auth headers.
        """
        return {
            "X-ADMIN-SECRET": self.admin_secret or "",
            "X-Customer-Api-Id": self.customer_api_id or "",
            "X-Secret": self.secret or "",
        }

    async def _execute_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute async HTTP request with retry logic.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            data: Request data.
            headers: Additional headers.

        Returns:
            API response data.

        Raises:
            EchoIntelAuthenticationException: On auth errors.
            EchoIntelValidationException: On validation errors.
            EchoIntelException: On other API errors.
        """

        @retry(
            stop=stop_after_attempt(self.retry_attempts),
            wait=wait_exponential(multiplier=self.retry_delay),
            reraise=True,
        )
        async def _do_request() -> dict[str, Any]:
            try:
                response = await self._client.request(
                    method=method,
                    url=endpoint,
                    json=data if data else None,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                self._handle_http_error(e)

        return await _do_request()

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and raise appropriate exceptions.

        Args:
            error: The HTTP error.

        Raises:
            EchoIntelAuthenticationException: On 401/403 errors.
            EchoIntelValidationException: On 422 errors.
            EchoIntelException: On other errors.
        """
        status_code = error.response.status_code
        try:
            body = error.response.json()
        except Exception:
            body = {}

        if status_code in (401, 403):
            raise EchoIntelAuthenticationException(
                message=body.get("detail", "Authentication failed"),
                status_code=status_code,
            ) from error

        if status_code == 422:
            raise EchoIntelValidationException(
                message=body.get("detail", "Validation failed"),
                errors=body.get("errors", {}),
                context=body,
            ) from error

        raise EchoIntelException(
            message=body.get("detail", str(error)),
            status_code=status_code,
            context=body,
        ) from error
