"""Forecast response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class ForecastValue(EchoIntelResponse):
    """Individual forecast value with date and prediction."""

    year_month: str
    value: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.year_month = data.get("yyyy-mm", "")
        self.value = float(data.get("value", 0))


class ForecastEvaluationMetrics(EchoIntelResponse):
    """Evaluation metrics for forecast quality assessment."""

    rmse: float | None
    mae: float | None
    r2: float | None
    average_daily_sales: float | None
    interpretation: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.rmse = float(data["RMSE"]) if "RMSE" in data else None
        self.mae = float(data["MAE"]) if "MAE" in data else None
        self.r2 = float(data["R2"]) if "R2" in data else None
        self.average_daily_sales = (
            float(data["average_daily_sales"])
            if "average_daily_sales" in data
            else None
        )
        self.interpretation = data.get("Interpretation", "")


class ForecastData(EchoIntelResponse):
    """Forecast data containing calendar and business day predictions."""

    calendar: list[ForecastValue]
    business: list[ForecastValue]

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.calendar = [
            ForecastValue.from_dict(item) for item in data.get("calendar", [])
        ]
        self.business = [
            ForecastValue.from_dict(item) for item in data.get("business", [])
        ]


class ForecastAlgorithmResult(EchoIntelResponse):
    """Result of a forecast algorithm for a specific product."""

    product_code: str
    best_algorithm: str
    evaluation_metrics: ForecastEvaluationMetrics
    forecast: ForecastData

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.product_code = data.get("product_code", "")
        self.best_algorithm = data.get("best_algorithm", "")
        self.evaluation_metrics = ForecastEvaluationMetrics.from_dict(
            data.get("evaluation_metrics", {})
        )
        self.forecast = ForecastData.from_dict(data.get("forecast", {}))


class ForecastUnitsResponse(EchoIntelResponse):
    """Response for forecast units endpoint."""

    forecast_period: int
    forecasts: list[ForecastAlgorithmResult]
    execution_time_seconds: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.forecast_period = int(data.get("forecast_period", 0))
        self.execution_time_seconds = float(data.get("execution_time_seconds", 0))
        self.forecasts = [
            ForecastAlgorithmResult.from_dict(item)
            for item in data.get("forecasts", [])
        ]
