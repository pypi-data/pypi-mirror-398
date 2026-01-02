Async Client API
=================

The ``WeexAsyncClient`` is the main interface for interacting with the Weex API using async/await patterns.

.. autoclass:: weex_client.client.WeexAsyncClient
   :members:
   :undoc-members:
   :show-inheritance:

Account Management
------------------

.. automethod:: weex_client.client.WeexAsyncClient.get_account_balance
.. automethod:: weex_client.client.WeexAsyncClient.get_all_positions
.. automethod:: weex_client.client.WeexAsyncClient.get_position
.. automethod:: weex_client.client.WeexAsyncClient.get_multiple_positions

Order Management
----------------

.. automethod:: weex_client.client.WeexAsyncClient.place_order
.. automethod:: weex_client.client.WeexAsyncClient.cancel_order
.. automethod:: weex_client.client.WeexAsyncClient.get_order
.. automethod:: weex_client.client.WeexAsyncClient.get_all_orders

Market Data
-----------

.. automethod:: weex_client.client.WeexAsyncClient.get_ticker
.. automethod:: weex_client.client.WeexAsyncClient.get_all_tickers
.. automethod:: weex_client.client.WeexAsyncClient.get_order_book
.. automethod:: weex_client.client.WeexAsyncClient.get_trades
.. automethod:: weex_client.client.WeexAsyncClient.get_contracts

Advanced Features
-----------------

.. automethod:: weex_client.client.WeexAsyncClient.get_market_overview
.. automethod:: weex_client.client.WeexAsyncClient.stream_tickers

Context Manager
---------------

The client implements the async context manager protocol for proper resource management:

.. code-block:: python

   import asyncio
   from weex_client import WeexAsyncClient, WeexConfig

   async def trading_example():
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           # Client resources are automatically managed
           balance = await client.get_account_balance()
           print(f"Balance: {balance}")
           
           # Client is automatically closed when exiting the context

Error Handling
--------------

The client uses Python 3.14 pattern matching for error handling:

.. code-block:: python

   import asyncio
   from weex_client import WeexAsyncClient, WeexConfig
   from weex_client.exceptions import (
       WEEXAuthenticationError,
       WEEXRateLimitError,
       WEEXError
   )

   async def robust_trading():
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           try:
               balance = await client.get_account_balance()
               return balance
           except WEEXError as e:
               match e:
                   case WEEXAuthenticationError(code=code):
                       print(f"🔐 Authentication failed: {code}")
                       # Handle authentication issues
                   case WEEXRateLimitError(retry_after=delay):
                       print(f"⏱️ Rate limited: retry after {delay}s")
                       # Implement retry logic
                   case _:
                       print(f"❌ General error: {e}")
                       # Handle other errors

Basic Usage Examples
---------------------

Get Account Balance
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def check_balance():
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           balance_data = await client.get_account_balance()
           available_balance = float(balance_data["data"]["balance"])
           print(f"Available balance: ${available_balance:.2f}")

Safe Order Placement (1% Rule)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def place_safe_order(symbol: str, order_type: str = "1"):
       """Place order with 1% risk management"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           # Get current balance
           balance_data = await client.get_account_balance()
           available_balance = float(balance_data["data"]["balance"])
           
           # Calculate 1% position size
           max_risk_amount = available_balance * 0.01
           ticker_data = await client.get_ticker(symbol)
           current_price = float(ticker_data["data"]["last"])
           
           # Calculate safe position size
           safe_size = max_risk_amount / current_price
           
           # Place order with safety
           from weex_client.models import PlaceOrderRequest
           order = PlaceOrderRequest(
               symbol=symbol,
               client_oid=f"safe_order_{int(time.time())}",
               size=str(safe_size),
               type=order_type,
               order_type="1",  # Market order
               match_price="1"   # Use current price
           )
           
           result = await client.place_order(order)
           print(f"✅ Safe order placed: {result}")
           return result

Multiple Operations with TaskGroup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def get_trading_overview(symbols: list[str]):
       """Get concurrent market data for multiple symbols"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           try:
               async with asyncio.TaskGroup() as tg:
                   tasks = []
                   for symbol in symbols:
                       # Start concurrent requests
                       ticker_task = tg.create_task(
                           client.get_ticker(symbol)
                       )
                       position_task = tg.create_task(
                           client.get_position(symbol)
                       )
                       tasks.append((symbol, ticker_task, position_task))
                   
                   results = {}
                   for symbol, ticker_task, position_task in tasks:
                       ticker_result = await ticker_task
                       position_result = await position_task
                       
                       results[symbol] = {
                           "ticker": ticker_result,
                           "position": position_result
                       }
                   
                   return results
                   
           except* Exception as eg:
               # Handle multiple concurrent errors
               for exc in eg.exceptions:
                   print(f"Error in concurrent operation: {exc}")

Real-time Data Streaming
------------------------

.. code-block:: python

   async def monitor_market(symbol: str):
       """Monitor real-time market data"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           print(f"📊 Monitoring {symbol}...")
           
           async for ticker_message in client.stream_tickers([symbol]):
               price = ticker_message.data.get("last", "N/A")
               timestamp = ticker_message.timestamp
               
               print(f"{timestamp}: {symbol} = ${price}")
               
               # Add your trading logic here
               # await analyze_and_trade(price, timestamp)

Position Management
------------------

.. code-block:: python

   async def manage_positions():
       """Monitor and manage open positions"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           positions_data = await client.get_all_positions()
           
           if not positions_data.get("data"):
               print("📊 No open positions")
               return
           
           for position in positions_data["data"]:
               symbol = position.get("symbol")
               size = float(position.get("size", 0))
               side = position.get("side", "unknown")
               
               print(f"📈 {symbol}: {side} {size}")
               
               # Add position management logic
               if size > 0:
                   # Position exists, consider risk management
                   await manage_position_risk(client, symbol, position)

Performance Considerations
--------------------------

Connection Pooling
~~~~~~~~~~~~~~~~~~

The client automatically manages connection pooling for optimal performance:

.. code-block:: python

   # Configure for high-frequency operations
   config = WeexConfig(
       # ... other config
       connection=ConnectionConfig(
           max_connections=20,  # Increase for concurrent operations
           timeout=10          # Reduce timeout for faster responses
       )
   )

Rate Limiting
~~~~~~~~~~~~~

The client includes built-in rate limit detection:

.. code-block:: python

   async def rate_limited_trading():
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           try:
               # Operations will automatically respect rate limits
               results = await asyncio.gather(*[
                   client.get_ticker(f"BTCUSDT{i}")
                   for i in range(10)
               ])
               return results
               
           except WEEXRateLimitError as e:
               print(f"⏱️ Rate limited: {e.retry_after}s")
               await asyncio.sleep(e.retry_after)
               # Retry logic here

Memory Efficiency
~~~~~~~~~~~~~~~~

Use streaming for large datasets:

.. code-block:: python

   async def process_large_dataset():
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           # Stream instead of loading all data at once
           async for trade_data in client.stream_trades("BTCUSDT"):
               # Process each trade as it arrives
               await process_trade(trade_data)
               # Memory usage stays constant regardless of data volume

Common Patterns
---------------

Retry Logic
~~~~~~~~~~~

.. code-block:: python

   async def resilient_api_call(api_call, *args, max_retries=3):
       """Generic retry logic for API calls"""
       for attempt in range(max_retries):
           try:
               return await api_call(*args)
           except WEEXRateLimitError as e:
               if attempt < max_retries - 1:
                   await asyncio.sleep(e.retry_after)
                   continue
               raise
           except WEEXError as e:
               if attempt < max_retries - 1:
                   await asyncio.sleep(2 ** attempt)  # Exponential backoff
                   continue
               raise

Batch Operations
~~~~~~~~~~~~~~~

.. code-block:: python

   async def batch_order_management(order_requests: list[PlaceOrderRequest]):
       """Place multiple orders efficiently"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           # Process orders in batches to respect rate limits
           batch_size = 5
           for i in range(0, len(order_requests), batch_size):
               batch = order_requests[i:i + batch_size]
               
               results = await asyncio.gather(*[
                   client.place_order(order) for order in batch
               ], return_exceptions=True)
               
               for order, result in zip(batch, results):
                   if isinstance(result, Exception):
                       print(f"❌ Order failed: {order.client_oid} - {result}")
                   else:
                       print(f"✅ Order placed: {order.client_oid}")
               
               # Brief pause between batches
               if i + batch_size < len(order_requests):
                   await asyncio.sleep(0.5)