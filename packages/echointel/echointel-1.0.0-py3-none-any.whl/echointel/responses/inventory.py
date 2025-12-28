"""Inventory response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class DailyInventoryRecord(EchoIntelResponse):
    """Daily inventory record with stock levels."""

    date: str
    quantity: int
    value: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.date = data.get("date", "")
        self.quantity = int(data.get("quantity", 0))
        self.value = float(data.get("value", 0))


class ProductDetails(EchoIntelResponse):
    """Product details for inventory analysis."""

    product_code: str
    product_name: str
    category: str
    unit_cost: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.product_code = data.get("product_code", "")
        self.product_name = data.get("product_name", "")
        self.category = data.get("category", "")
        self.unit_cost = float(data.get("unit_cost", 0))


class ProcessingInfo(EchoIntelResponse):
    """Processing metadata for inventory analysis."""

    start_date: str
    end_date: str
    total_records: int
    processing_time_seconds: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.start_date = data.get("start_date", "")
        self.end_date = data.get("end_date", "")
        self.total_records = int(data.get("total_records", 0))
        self.processing_time_seconds = float(data.get("processing_time_seconds", 0))


class InventoryHistoryResponse(EchoIntelResponse):
    """Response for inventory history analysis endpoint."""

    daily_inventory: list[DailyInventoryRecord]
    inventory_analysis: dict[str, Any]
    inventory_aging: dict[str, Any]
    product_details: ProductDetails
    processing_info: ProcessingInfo

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.daily_inventory = [
            DailyInventoryRecord.from_dict(item)
            for item in data.get("daily_inventory", [])
        ]
        self.inventory_analysis = data.get("inventory_analysis", {})
        self.inventory_aging = data.get("inventory_aging", {})
        self.product_details = ProductDetails.from_dict(data.get("product_details", {}))
        self.processing_info = ProcessingInfo.from_dict(data.get("processing_info", {}))
