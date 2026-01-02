Sync Client API
===============

The ``WeexSyncClient`` provides a synchronous interface that internally manages the async operations, making it easier to integrate with existing synchronous code or for developers new to async programming.

.. autoclass:: weex_client.sync.WeexSyncClient
   :members:
   :undoc-members:
   :show-inheritance:

Account Management
------------------

.. automethod:: weex_client.sync.WeexSyncClient.get_account_balance
.. automethod:: weex_client.sync.WeexSyncClient.get_all_positions
.. automethod:: weex_client.sync.WeexSyncClient.get_position
.. automethod:: weex_client.sync.WeexSyncClient.get_multiple_positions

Order Management
----------------

.. automethod:: weex_client.sync.WeexSyncClient.place_order
.. automethod:: weex_client.sync.WeexSyncClient.cancel_order
.. automethod:: weex_client.sync.WeexSyncClient.get_order
.. automethod:: weex_client.sync.WeexSyncClient.get_all_orders

Market Data
-----------

.. automethod:: weex_client.sync.WeexSyncClient.get_ticker
.. automethod:: weex_client.sync.WeexSyncClient.get_all_tickers
.. automethod:: weex_client.sync.WeexSyncClient.get_order_book
.. automethod:: weex_client.sync.WeexSyncClient.get_trades
.. automethod:: weex_client.sync.WeexSyncClient.get_contracts

Context Manager
---------------

The sync client also implements context manager protocol for resource management:

.. code-block:: python

   from weex_client import WeexSyncClient, WeexConfig

   def sync_trading_example():
       config = WeexConfig.from_env()
       
       with WeexSyncClient(config) as client:
           # Client resources are automatically managed
           balance = client.get_account_balance()
           print(f"Balance: {balance}")
           
           # Client is automatically closed when exiting context

Quick Creation Function
-----------------------

.. autofunction:: weex_client.sync.create_sync_client

When to Use Sync vs Async
-------------------------

Use ``WeexSyncClient`` when:

* **Integrating with existing sync code** - No need to refactor existing applications
* **Simple scripts** - One-off operations or quick checks
* **Learning phase** - Easier for developers new to async programming
* **Data analysis** - Working with pandas, numpy, or other sync libraries

Use ``WeexAsyncClient`` when:

* **High performance needed** - Multiple concurrent API calls
* **Real-time applications** - WebSocket streaming or live trading
* **I/O bound operations** - Multiple API calls that can run in parallel
* **Modern Python applications** - Using FastAPI, asyncio, etc.

Basic Usage Examples
---------------------

Simple Balance Check
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client import WeexSyncClient, WeexConfig

   def check_balance():
       config = WeexConfig.from_env()
       
       with WeexSyncClient(config) as client:
           balance_data = client.get_account_balance()
           available_balance = float(balance_data["data"]["balance"])
           print(f"Available balance: ${available_balance:.2f}")
           
           return available_balance

Safe Order Placement
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client import WeexSyncClient, WeexConfig
   from weex_client.models import PlaceOrderRequest
   import time

   def place_safe_order(symbol: str, order_type: str = "1"):
       """Place order with 1% risk management (sync version)"""
       config = WeexConfig.from_env()
       
       with WeexSyncClient(config) as client:
           # Get current balance
           balance_data = client.get_account_balance()
           available_balance = float(balance_data["data"]["balance"])
           
           # Calculate 1% position size
           max_risk_amount = available_balance * 0.01
           ticker_data = client.get_ticker(symbol)
           current_price = float(ticker_data["data"]["last"])
           
           # Calculate safe position size
           safe_size = max_risk_amount / current_price
           
           # Place order with safety
           order = PlaceOrderRequest(
               symbol=symbol,
               client_oid=f"safe_sync_order_{int(time.time())}",
               size=str(safe_size),
               type=order_type,
               order_type="1",  # Market order
               match_price="1"   # Use current price
           )
           
           result = client.place_order(order)
           print(f"✅ Safe order placed: {result}")
           return result

Market Data Analysis
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   from weex_client import WeexSyncClient, WeexConfig

   def analyze_markets(symbols: list[str]):
       """Analyze multiple markets using pandas"""
       config = WeexConfig.from_env()
       
       with WeexSyncClient(config) as client:
           market_data = []
           
           for symbol in symbols:
               ticker_data = client.get_ticker(symbol)
               position_data = client.get_position(symbol)
               
               market_data.append({
                   "symbol": symbol,
                   "price": float(ticker_data["data"]["last"]),
                   "volume": float(ticker_data["data"]["volume"]),
                   "position_size": float(position_data["data"].get("size", 0))
               })
           
           # Convert to pandas DataFrame for analysis
           df = pd.DataFrame(market_data)
           
           # Calculate additional metrics
           df["position_value"] = df["price"] * df["position_size"]
           
           print("📊 Market Analysis:")
           print(df.to_string())
           
           return df

Thread Management
-----------------

The sync client manages background threads automatically:

.. code-block:: python

   from weex_client import create_sync_client

   def quick_trading():
       """Quick trading with automatic thread management"""
       
       # Creates and manages client automatically
       client = create_sync_client()
       
       try:
           balance = client.get_account_balance()
           print(f"Balance: {balance}")
           
           # Client is automatically cleaned up
       finally:
           # No need to manually close - handled automatically
           pass

Performance Considerations
--------------------------

Thread Pool Management
~~~~~~~~~~~~~~~~~~~~~~

The sync client uses a thread pool to run async operations:

.. code-block:: python

   # The default thread pool is optimized for most use cases
   # You can customize it if needed:

   from weex_client.sync import WeexSyncClient
   import concurrent.futures

   def custom_thread_example():
       config = WeexConfig.from_env()
       
       # Custom thread pool for specific requirements
       with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
           with WeexSyncClient(config, executor=executor) as client:
               # Operations will use the custom thread pool
               result = client.get_account_balance()
               print(f"Result: {result}")

Blocking Operations
~~~~~~~~~~~~~~~~~~~

Remember that sync client operations are blocking:

.. code-block:: python

   import time
   from weex_client import WeexSyncClient, WeexConfig

   def timing_example():
       config = WeexConfig.from_env()
       
       with WeexSyncClient(config) as client:
           start_time = time.time()
           
           # Each operation blocks until complete
           balance = client.get_account_balance()
           ticker = client.get_ticker("BTCUSDT")
           position = client.get_position("BTCUSDT")
           
           end_time = time.time()
           print(f"Total time: {end_time - start_time:.2f}s")
           
           # For better performance, consider using async client
           # for multiple concurrent operations

Integration Examples
---------------------

Django Integration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # views.py
   from django.http import JsonResponse
   from weex_client import create_sync_client

   def account_balance_view(request):
       """Django view using sync client"""
       client = create_sync_client()
       
       try:
           balance_data = client.get_account_balance()
           return JsonResponse({
               "balance": balance_data["data"]["balance"],
               "status": "success"
           })
       except Exception as e:
           return JsonResponse({
               "error": str(e),
               "status": "error"
           }, status=500)

Flask Integration
~~~~~~~~~~~~~~~~

.. code-block:: python

   # app.py
   from flask import Flask, jsonify
   from weex_client import create_sync_client

   app = Flask(__name__)

   @app.route('/api/balance')
   def get_balance():
       """Flask route using sync client"""
       client = create_sync_client()
       
       try:
           balance_data = client.get_account_balance()
           return jsonify({
               "balance": balance_data["data"]["balance"]
           })
       except Exception as e:
           return jsonify({"error": str(e)}), 500

   @app.route('/api/ticker/<symbol>')
   def get_ticker(symbol):
       """Get ticker data for a symbol"""
       client = create_sync_client()
       
       try:
           ticker_data = client.get_ticker(symbol)
           return jsonify(ticker_data["data"])
       except Exception as e:
           return jsonify({"error": str(e)}), 500

Data Analysis with Jupyter
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # In Jupyter notebook
   import pandas as pd
   import matplotlib.pyplot as plt
   from weex_client import create_sync_client

   def market_analysis_notebook():
       """Analyze markets in Jupyter"""
       client = create_sync_client()
       
       symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
       
       # Collect data
       market_data = []
       for symbol in symbols:
           ticker = client.get_ticker(symbol)
           market_data.append({
               "symbol": symbol,
               "price": float(ticker["data"]["last"]),
               "volume_24h": float(ticker["data"]["volume"])
           })
       
       # Create DataFrame
       df = pd.DataFrame(market_data)
       
       # Visualize
       plt.figure(figsize=(10, 6))
       plt.bar(df["symbol"], df["price"])
       plt.title("Current Prices")
       plt.ylabel("Price (USD)")
       plt.show()
       
       return df

Script Integration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # trading_script.py
   #!/usr/bin/env python3

   import sys
   import argparse
   from weex_client import create_sync_client

   def main():
       parser = argparse.ArgumentParser(description="Simple trading CLI")
       parser.add_argument("command", choices=["balance", "ticker", "position"])
       parser.add_argument("--symbol", default="BTCUSDT")
       
       args = parser.parse_args()
       
       client = create_sync_client()
       
       try:
           if args.command == "balance":
               balance = client.get_account_balance()
               print(f"Balance: ${balance['data']['balance']}")
           
           elif args.command == "ticker":
               ticker = client.get_ticker(args.symbol)
               print(f"{args.symbol}: ${ticker['data']['last']}")
           
           elif args.command == "position":
               position = client.get_position(args.symbol)
               size = position['data'].get('size', 0)
               print(f"{args.symbol} position: {size}")
       
       except Exception as e:
           print(f"Error: {e}", file=sys.stderr)
           sys.exit(1)

   if __name__ == "__main__":
       main()

Common Patterns
---------------

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client import create_sync_client
   from weex_client.exceptions import WEEXError

   def safe_api_call(func, *args, **kwargs):
       """Safe wrapper for sync API calls"""
       client = create_sync_client()
       
       try:
           return func(client, *args, **kwargs)
       except WEEXError as e:
           print(f"API Error: {e}")
           return None
       except Exception as e:
           print(f"Unexpected error: {e}")
           return None
       finally:
           # Client is automatically cleaned up
           pass

   # Usage
   def get_balance_safe():
       return safe_api_call(lambda client: client.get_account_balance())

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   def process_multiple_symbols(symbols: list[str]):
       """Process multiple symbols sequentially"""
       client = create_sync_client()
       
       results = {}
       
       try:
           for symbol in symbols:
               print(f"Processing {symbol}...")
               
               ticker = client.get_ticker(symbol)
               position = client.get_position(symbol)
               
               results[symbol] = {
                   "ticker": ticker,
                   "position": position
               }
       
       except Exception as e:
           print(f"Error processing symbols: {e}")
       
       return results

   # Note: For better performance with many symbols, 
   # consider using the async client instead

Configuration
-------------

The sync client accepts the same configuration as the async client:

.. code-block:: python

   from weex_client import WeexSyncClient, WeexConfig

   def custom_config_example():
       config = WeexConfig(
           api_key="your_key",
           secret_key="your_secret",
           passphrase="your_passphrase",
           environment="development"
       )
       
       with WeexSyncClient(config) as client:
           # Client uses custom configuration
           balance = client.get_account_balance()
           print(f"Balance: {balance}")