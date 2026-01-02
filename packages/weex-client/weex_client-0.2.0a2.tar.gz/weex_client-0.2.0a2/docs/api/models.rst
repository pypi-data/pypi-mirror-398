Data Models API
================

The weex-client uses Pydantic models for type-safe data validation and serialization.

.. autoclass:: weex_client.models.PlaceOrderRequest
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: weex_client.models.ApiResponse
   :members:
   :undoc-members:
   :show-inheritance:

Order Models
------------

PlaceOrderRequest
~~~~~~~~~~~~~~~~~

The ``PlaceOrderRequest`` model validates all order parameters before submission:

.. code-block:: python

   from weex_client.models import PlaceOrderRequest

   # Valid order creation
   order = PlaceOrderRequest(
       symbol="BTCUSDT",
       client_oid="my_order_001",
       size="0.001",
       type="1",          # Open position
       order_type="1",     # Limit order
       match_price="0",    # Use specified price
       price="50000.0",    # Limit price
       preset_stop_loss_price="48000.0"  # Optional stop loss
   )

Order Type Reference
~~~~~~~~~~~~~~~~~~~

.. list-table:: Order Types
   :header-rows: 1

   * - Type
     - Description
     - Use Case
   * - ``"1"``
     - Open position
     - Enter new trade
   * - ``"2"``
     - Close position
     - Exit existing trade
   * - ``"3"``
     - Reduce position
     - Partial position reduction
   * - ``"4"``
     - ADL (Auto-Deleveraging)
     - Liquidation scenarios

Match Price Options
~~~~~~~~~~~~~~~~~~

.. list-table:: Match Price Options
   :header-rows: 1

   * - Option
     - Description
     - Price Source
   * - ``"0"``
     - Limit order
     - Use ``price`` field
   * - ``"1"``
     - Market order
     - Use current market price

Safety Examples
~~~~~~~~~~~~~~~

.. code-block:: python

   def create_safe_order(symbol: str, balance: float, risk_percent: float = 0.01):
       """Create order with built-in safety validation"""
       
       # Calculate position size (1% of balance)
       max_risk = balance * risk_percent
       
       # Get current market price (mock example)
       current_price = 50000.0  # Replace with API call
       
       # Calculate safe position size
       safe_size = max_risk / current_price
       
       # Create order with validation
       order = PlaceOrderRequest(
           symbol=symbol,
           client_oid=f"safe_{int(time.time())}",
           size=str(safe_size),
           type="1",
           order_type="0",  # Market order for immediate fill
           match_price="1"  # Use market price
       )
       
       # Pydantic automatically validates
       print(f"✅ Safe order created: {safe_size:.6f} {symbol}")
       return order

   # Usage
   try:
       order = create_safe_order("BTCUSDT", 1000.0)  # 1% of $1000
   except Exception as e:
       print(f"❌ Order creation failed: {e}")

Response Models
---------------

ApiResponse Structure
~~~~~~~~~~~~~~~~~~~~

All API responses follow the ``ApiResponse`` structure:

.. code-block:: python

   from weex_client.models import ApiResponse

   # Response example structure
   response = ApiResponse(
       code=0,                    # 0 = success, non-zero = error
       message="success",
       data={"key": "value"},      # Actual response data
       timestamp="2024-01-01T00:00:00Z"
   )

   # Access pattern
   if response.code == 0:
       data = response.data
       print(f"Success: {data}")
   else:
       print(f"Error {response.code}: {response.message}")

Type Aliases
------------

The client provides type aliases for better code clarity:

Trading Types
~~~~~~~~~~~~~

.. code-block:: python

   from weex_client.types import (
       Symbol, OrderId, ClientOrderId, Size, Price,
       OrderType, Side, TimeInForce
   )

   # Type annotations improve code clarity
   def place_order_safe(
       symbol: Symbol,
       size: Size,
       order_type: OrderType,
       price: Price | None = None
   ) -> ClientOrderId:
       """Type-safe order placement"""
       # Implementation
       pass

   # Usage with type hints
   order_id: ClientOrderId = place_order_safe(
       symbol="BTCUSDT",
       size="0.001",
       order_type="1",
       price="50000.0"
   )

API Types
~~~~~~~~~

.. code-block:: python

   from weex_client.types import (
       ErrorCode, Headers, Timeout, ResponseData
   )

   # Error handling with type safety
   def handle_error(error: ErrorCode, message: str):
       """Type-safe error handling"""
       match error:
           case 40001:
               print(f"🔐 Authentication error: {message}")
           case 40029:
               print(f"⏱️ Rate limit error: {message}")
           case _:
               print(f"❌ Unknown error {error}: {message}")

WebSocket Types
~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client.types import (
       WebSocketMessage, SubscriptionType, Channel
   )

   def process_websocket_message(message: WebSocketMessage):
       """Process WebSocket message with type safety"""
       data = message.data
       channel = message.channel
       timestamp = message.timestamp
       
       match channel:
           case "ticker":
               process_ticker_data(data)
           case "order_book":
               process_order_book_data(data)
           case "trade":
               process_trade_data(data)
           case _:
               print(f"Unknown channel: {channel}")

Custom Model Extensions
----------------------

Creating Custom Models
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pydantic import BaseModel, Field
   from weex_client.types import Symbol, Size, Price

   class TradingStrategy(BaseModel):
       """Custom model for trading strategies"""
       name: str = Field(..., description="Strategy name")
       symbol: Symbol = Field(..., description="Trading symbol")
       max_position_size: Size = Field(..., description="Maximum position size")
       stop_loss_percent: float = Field(0.02, description="Stop loss percentage")
       take_profit_percent: float = Field(0.05, description="Take profit percentage")
       enabled: bool = Field(True, description="Strategy enabled")

   # Usage
   strategy = TradingStrategy(
       name="MA Crossover",
       symbol="BTCUSDT",
       max_position_size="0.01"
   )

Model Validation
~~~~~~~~~~~~~~~

.. code-block:: python

   from pydantic import ValidationError

   def validate_order_parameters(params: dict) -> PlaceOrderRequest:
       """Validate and create order from parameters"""
       try:
           order = PlaceOrderRequest(**params)
           return order
       except ValidationError as e:
           print(f"❌ Validation errors:")
           for error in e.errors():
               field = error["loc"][0]
               msg = error["msg"]
               print(f"   {field}: {msg}")
           raise

   # Usage
   params = {
       "symbol": "BTCUSDT",
       "client_oid": "test_order",
       "size": "0.001",
       "type": "1",
       "order_type": "1",
       "match_price": "0",
       "price": "50000.0"
   }

   try:
       order = validate_order_parameters(params)
       print("✅ Order validation passed")
   except ValidationError:
       print("❌ Order validation failed")

Data Transformation
------------------

Model Serialization
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Convert to dictionary for API calls
   order = PlaceOrderRequest(
       symbol="BTCUSDT",
       client_oid="test_order",
       size="0.001",
       type="1",
       order_type="0",
       match_price="0",
       price="50000.0"
   )

   # Convert to dict for HTTP request
   order_dict = order.model_dump()
   print(f"API payload: {order_dict}")

   # Convert to JSON
   order_json = order.model_dump_json()
   print(f"JSON payload: {order_json}")

   # Exclude certain fields
   order_without_stop_loss = order.model_dump(exclude={"preset_stop_loss_price"})

Model Deserialization
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create model from API response
   response_data = {
       "symbol": "BTCUSDT",
       "client_oid": "test_order",
       "size": "0.001",
       "type": "1",
       "order_type": "0",
       "match_price": "0",
       "price": "50000.0"
   }

   # Recreate model from response
   order = PlaceOrderRequest.model_validate(response_data)
   print(f"Recreated order: {order}")

Advanced Patterns
-----------------

Model Inheritance
~~~~~~~~~~~~~~~~

.. code-block:: python

   class BaseOrderRequest(BaseModel):
       """Base class for all order requests"""
       symbol: Symbol
       client_oid: ClientOrderId
       size: Size

   class MarketOrderRequest(BaseOrderRequest):
       """Market order specific fields"""
       type: OrderType = "1"
       order_type: str = "0"  # Market order
       match_price: str = "1"  # Use market price

   class LimitOrderRequest(BaseOrderRequest):
       """Limit order specific fields"""
       type: OrderType = "1"
       order_type: str = "1"  # Limit order
       match_price: str = "0"  # Use specified price
       price: Price

   # Usage
   market_order = MarketOrderRequest(
       symbol="BTCUSDT",
       client_oid="market_001",
       size="0.001"
   )

   limit_order = LimitOrderRequest(
       symbol="BTCUSDT",
       client_oid="limit_001", 
       size="0.001",
       price="50000.0"
   )

Model Composition
~~~~~~~~~~~~~~~~

.. code-block:: python

   class OrderConstraints(BaseModel):
       """Model for order constraints"""
       min_size: Size = Field("0.001", description="Minimum order size")
       max_size: Size = Field("100", description="Maximum order size")
       price_precision: int = Field(8, description="Price decimal places")
       size_precision: int = Field(8, description="Size decimal places")

   class TradingInstrument(BaseModel):
       """Complete trading instrument model"""
       symbol: Symbol
       base_asset: str
       quote_asset: str
       constraints: OrderConstraints
       is_active: bool = True

   # Create with nested validation
   instrument = TradingInstrument(
       symbol="BTCUSDT",
       base_asset="BTC",
       quote_asset="USDT",
       constraints=OrderConstraints(
           min_size="0.001",
           max_size="1000"
       )
   )

Dynamic Model Creation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pydantic import create_model
   from typing import Dict, Any

   def create_custom_response_model(response_schema: Dict[str, Any]):
       """Create Pydantic model from API schema"""
       
       model_fields = {}
       for field_name, field_config in response_schema.items():
           field_type = field_config.get("type", str)
           required = field_config.get("required", True)
           default = ... if required else None
           
           model_fields[field_name] = (field_type, default)
       
       # Dynamic model creation
       DynamicModel = create_model(
           "DynamicResponseModel",
           **model_fields
       )
       
       return DynamicModel

   # Usage with API schema
   ticker_schema = {
       "symbol": {"type": str, "required": True},
       "last": {"type": float, "required": True},
       "volume": {"type": float, "required": False, "default": 0.0}
   }

   TickerResponse = create_custom_response_model(ticker_schema)
   ticker = TickerResponse(symbol="BTCUSDT", last=50000.0)

Testing with Models
-------------------

Mock Data Creation
~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_mock_order(symbol: str = "BTCUSDT") -> PlaceOrderRequest:
       """Create mock order for testing"""
       import time
       
       return PlaceOrderRequest(
           symbol=symbol,
           client_oid=f"mock_{int(time.time())}",
           size="0.001",
           type="1",
           order_type="1",
           match_price="0",
           price="50000.0"
       )

   def create_mock_balance(balance: float = 1000.0) -> dict:
       """Create mock balance response"""
       return {
           "code": 0,
           "message": "success",
           "data": {
               "balance": str(balance),
               "available": str(balance * 0.95),  # 5% frozen
               "frozen": str(balance * 0.05)
           },
           "timestamp": "2024-01-01T00:00:00Z"
       }

Model Testing
~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from pydantic import ValidationError

   def test_order_validation():
       """Test order model validation"""
       
       # Valid order
       valid_order = PlaceOrderRequest(
           symbol="BTCUSDT",
           client_oid="test",
           size="0.001",
           type="1",
           order_type="1",
           match_price="0",
           price="50000.0"
       )
       assert valid_order.symbol == "BTCUSDT"
       
       # Invalid order - missing required field
       with pytest.raises(ValidationError):
           PlaceOrderRequest(
               symbol="BTCUSDT",
               # Missing client_oid
               size="0.001",
               type="1",
               order_type="1",
               match_price="0",
               price="50000.0"
           )

   def test_order_serialization():
       """Test order serialization"""
       order = PlaceOrderRequest(
           symbol="BTCUSDT",
           client_oid="test",
           size="0.001",
           type="1",
           order_type="1",
           match_price="0",
           price="50000.0"
       )
       
       # Test dictionary serialization
       order_dict = order.model_dump()
       assert order_dict["symbol"] == "BTCUSDT"
       assert "client_oid" in order_dict
       
       # Test JSON serialization
       order_json = order.model_dump_json()
       assert "BTCUSDT" in order_json

Best Practices
--------------

Model Design
~~~~~~~~~~~~

1. **Use descriptive field names** that match API documentation
2. **Include validation rules** in field definitions
3. **Add proper type hints** for better IDE support
4. **Use Field() for metadata** and descriptions
5. **Implement custom validation** for complex business rules

Performance
~~~~~~~~~~~~

1. **Use model_dump()** instead of dict() for serialization
2. **Exclude unnecessary fields** to reduce payload size
3. **Cache model instances** when appropriate
4. **Use model_validate()** for API response parsing

Error Handling
~~~~~~~~~~~~~~~

1. **Catch ValidationError** specifically for model errors
2. **Provide clear error messages** for validation failures
3. **Use model validation** at API boundaries
4. **Log validation errors** for debugging

.. code-block:: python

   def safe_create_order(order_data: dict) -> PlaceOrderRequest | None:
       """Create order with comprehensive error handling"""
       try:
           order = PlaceOrderRequest.model_validate(order_data)
           logger.info(f"Order created successfully: {order.client_oid}")
           return order
       except ValidationError as e:
           logger.error(f"Order validation failed: {e}")
           return None
       except Exception as e:
           logger.error(f"Unexpected error creating order: {e}")
           return None