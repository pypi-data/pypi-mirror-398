"""
Pydantic models for Weex API request/response validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

# Direct imports - pydantic should be available
from pydantic import BaseModel, Field, validator

# Type aliases for better type safety and readability
type Price = str
type Size = str
type Symbol = str
type OrderId = str
type ClientOrderId = str
type OrderType = Literal["1", "2", "3", "4"]
type ExecutionType = Literal["0", "1", "2", "3"]
type TimeInForce = Literal["0", "1", "2"]
type MarginMode = Literal["1", "3"]


class PlaceOrderRequest(BaseModel):
    """Request model for placing orders."""

    symbol: Symbol = Field(..., description="Trading symbol")
    client_oid: ClientOrderId = Field(..., description="Client order ID")
    size: Size = Field(..., description="Order size")
    type: OrderType = Field(..., description="Order type")
    order_type: OrderType = Field(..., description="Order type")
    match_price: Literal["0", "1"] = Field("0", description="Match price")
    price: Price | None = Field(None, description="Order price")
    preset_stop_loss_price: Price | None = Field(
        None, description="Preset stop loss price"
    )

    @validator("price")
    def validate_price(cls, v, values):
        """Price is required for limit orders."""
        if values.get("match_price") == "0" and v is None:
            raise ValueError("price is required for limit orders (match_price=0)")
        return v

    def dict(self, **kwargs) -> dict[str, Any]:
        """Return dict with None values filtered out."""
        data = super().dict(**kwargs)
        return {k: v for k, v in data.items() if v is not None}


class ApiResponse(BaseModel):
    """Generic API response model."""

    code: int | str = Field(..., description="Response code")
    message: str | None = Field(None, description="Response message")
    data: Any | None = Field(None, description="Response data")
    success: bool | None = Field(None, description="Success flag")
    timestamp: datetime | None = Field(None, description="Response timestamp")

    @validator("success", pre=True, always=True)
    def set_success_from_code(cls, v, values):
        """Set success flag based on code if not provided."""
        if v is not None:
            return v
        code = values.get("code", 0)
        return str(code) == "0" or code == 0
