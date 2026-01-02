WebSocket API
=============

The ``WeexWebSocketClient`` provides real-time streaming capabilities for market data and private account updates, perfect for live trading and monitoring applications.

.. autoclass:: weex_client.websocket.WeexWebSocketClient
   :members:
   :undoc-members:
   :show-inheritance:

Public Channel Streaming
-----------------------

.. automethod:: weex_client.websocket.WeexWebSocketClient.stream_tickers
.. automethod:: weex_client.websocket.WeexWebSocketClient.stream_order_book
.. automethod:: weex_client.websocket.WeexWebSocketClient.stream_trades

Private Channel Streaming
------------------------

.. automethod:: weex_client.websocket.WeexWebSocketClient.stream_account
.. automethod:: weex_client.websocket.WeexWebSocketClient.stream_positions
.. automethod:: weex_client.websocket.WeexWebSocketClient.stream_orders

Connection Management
---------------------

.. automethod:: weex_client.websocket.WeexWebSocketClient.connect
.. automethod:: weex_client.websocket.WeexWebSocketClient.disconnect
.. automethod:: weex_client.websocket.WeexWebSocketClient.is_connected

Context Manager
---------------

The WebSocket client implements async context manager for automatic resource management:

.. code-block:: python

   import asyncio
   from weex_client import WeexWebSocketClient, WeexConfig

   async def websocket_example():
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           # Client automatically connects and manages resources
           async for message in ws_client.stream_tickers(["BTCUSDT"]):
               print(f"Ticker: {message.data}")
           
           # Client automatically disconnects when exiting context

Basic Usage Examples
---------------------

Real-time Market Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def monitor_market():
       """Monitor real-time market data"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("📊 Monitoring BTC/USDT...")
           
           async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
               data = ticker_message.data
               timestamp = ticker_message.timestamp
               
               price = data.get("last", "N/A")
               volume = data.get("volume", "N/A")
               change = data.get("change", "N/A")
               
               print(f"{timestamp}: BTC/USDT = ${price} | Volume: {volume} | Change: {change}%")

Order Book Monitoring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def monitor_order_book():
       """Monitor real-time order book"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("📈 Monitoring BTC/USDT order book...")
           
           async for book_message in ws_client.stream_order_book("BTCUSDT", level=5):
               data = book_message.data
               
               bids = data.get("bids", [])[:3]  # Top 3 bids
               asks = data.get("asks", [])[:3]  # Top 3 asks
               
               print(f"\n📊 Order Book Snapshot:")
               print("Bids:")
               for i, (price, size) in enumerate(bids, 1):
                   print(f"  {i}. ${price} - {size}")
               
               print("Asks:")
               for i, (price, size) in enumerate(asks, 1):
                   print(f"  {i}. ${price} - {size}")

Trade Stream Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def monitor_trades():
       """Monitor real-time trades"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("💰 Monitoring BTC/USDT trades...")
           
           async for trade_message in ws_client.stream_trades("BTCUSDT"):
               data = trade_message.data
               timestamp = trade_message.timestamp
               
               price = data.get("price", "N/A")
               size = data.get("size", "N/A")
               side = data.get("side", "N/A")
               
               side_emoji = "🟢" if side == "buy" else "🔴"
               print(f"{timestamp} {side_emoji} {size} BTC @ ${price}")

Private Data Streaming
---------------------

Account Updates
~~~~~~~~~~~~~~~

.. code-block:: python

   async def monitor_account():
       """Monitor real-time account updates"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("💼 Monitoring account updates...")
           
           async for account_message in ws_client.stream_account():
               data = account_message.data
               timestamp = account_message.timestamp
               
               balance = data.get("balance", "N/A")
               available = data.get("available", "N/A")
               frozen = data.get("frozen", "N/A")
               
               print(f"{timestamp}: Balance: {balance} | Available: {available} | Frozen: {frozen}")

Position Monitoring
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def monitor_positions():
       """Monitor real-time position updates"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("📊 Monitoring positions...")
           
           async for position_message in ws_client.stream_positions():
               data = position_message.data
               timestamp = position_message.timestamp
               
               symbol = data.get("symbol", "N/A")
               size = data.get("size", "N/A")
               side = data.get("side", "N/A")
               pnl = data.get("unrealized_pnl", "N/A")
               
               print(f"{timestamp}: {symbol} {side} {size} | PnL: {pnl}")

Order Updates
~~~~~~~~~~~~

.. code-block:: python

   async def monitor_orders():
       """Monitor real-time order updates"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("📋 Monitoring orders...")
           
           async for order_message in ws_client.stream_orders():
               data = order_message.data
               timestamp = order_message.timestamp
               
               order_id = data.get("order_id", "N/A")
               status = data.get("status", "N/A")
               symbol = data.get("symbol", "N/A")
               size = data.get("size", "N/A")
               
               status_emoji = {
                   "new": "🆕",
                   "partially_filled": "⚡",
                   "filled": "✅",
                   "canceled": "❌",
                   "rejected": "🚫"
               }.get(status, "❓")
               
               print(f"{timestamp} {status_emoji} Order {order_id}: {symbol} {size} ({status})")

Advanced Streaming Patterns
--------------------------

Multi-Symbol Monitoring
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def monitor_multiple_symbols():
       """Monitor multiple symbols simultaneously"""
       config = WeexConfig.from_env()
       symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
       
       async with WeexWebSocketClient(config) as ws_client:
           print(f"📊 Monitoring {symbols}...")
           
           # Create tasks for each symbol
           async with asyncio.TaskGroup() as tg:
               tasks = []
               for symbol in symbols:
                   task = tg.create_task(
                       monitor_symbol(ws_client, symbol)
                   )
                   tasks.append(task)
               
               # All symbol monitoring runs concurrently

   async def monitor_symbol(ws_client, symbol):
       """Monitor a single symbol"""
       async for ticker_message in ws_client.stream_tickers([symbol]):
           price = ticker_message.data.get("last", "N/A")
           print(f"{symbol}: ${price}")

Real-time Analysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def real_time_analysis():
       """Perform real-time analysis on stream data"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("📊 Starting real-time analysis...")
           
           price_history = []
           moving_avg_period = 20
           
           async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
               price = float(ticker_message.data.get("last", 0))
               timestamp = ticker_message.timestamp
               
               price_history.append(price)
               
               # Keep only recent history
               if len(price_history) > moving_avg_period:
                   price_history.pop(0)
               
               # Calculate moving average
               if len(price_history) >= moving_avg_period:
                   moving_avg = sum(price_history) / len(price_history)
                   
                   # Simple trading signal
                   if price > moving_avg * 1.02:  # 2% above MA
                       print(f"{timestamp}: 📈 BUY signal - Price: ${price:.2f}, MA: ${moving_avg:.2f}")
                   elif price < moving_avg * 0.98:  # 2% below MA
                       print(f"{timestamp}: 📉 SELL signal - Price: ${price:.2f}, MA: ${moving_avg:.2f}")
                   else:
                       print(f"{timestamp}: 📊 HOLD - Price: ${price:.2f}, MA: ${moving_avg:.2f}")

Risk Management Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def risk_monitored_trading():
       """Real-time risk monitoring with WebSocket"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("🛡️ Starting risk-monitored trading...")
           
           risk_limits = {
               "max_position_size": 1000,  # USD
               "max_daily_loss": 100,      # USD
               "max_drawdown": 0.1         # 10%
           }
           
           current_positions = {}
           daily_pnl = 0
           starting_balance = None
           
           # Monitor positions for risk breaches
           async for position_message in ws_client.stream_positions():
               data = position_message.data
               symbol = data.get("symbol")
               size = float(data.get("size", 0))
               pnl = float(data.get("unrealized_pnl", 0))
               
               current_positions[symbol] = {"size": size, "pnl": pnl}
               
               # Check position size limits
               current_exposure = sum(
                   abs(pos["size"]) * get_current_price(symbol) 
                   for symbol, pos in current_positions.items()
               )
               
               if current_exposure > risk_limits["max_position_size"]:
                   print(f"🚨 POSITION SIZE LIMIT BREACHED: ${current_exposure:.2f}")
                   await emergency_reduce_positions()
               
               # Check daily loss limits
               total_pnl = sum(pos["pnl"] for pos in current_positions.values())
               if total_pnl < -risk_limits["max_daily_loss"]:
                   print(f"🚨 DAILY LOSS LIMIT BREACHED: ${total_pnl:.2f}")
                   await emergency_close_all_positions()

Paper Trading with WebSocket
---------------------------

Paper Trading Engine
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class PaperTradingEngine:
       def __init__(self, initial_balance=10000):
           self.balance = initial_balance
           self.positions = {}
           self.orders = {}
           self.trades = []
           self.trade_id = 0
       
       async def simulate_trading(self, config):
           """Run paper trading simulation with real market data"""
           async with WeexWebSocketClient(config) as ws_client:
               print("🎯 Starting paper trading simulation...")
               
               async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
                   price = float(ticker_message.data.get("last", 0))
                   timestamp = ticker_message.timestamp
                   
                   # Simple trading logic
                   signal = self.generate_signal(price)
                   
                   if signal == "buy" and self.balance > 100:
                       # Buy 1% of balance
                       order_size = self.balance * 0.01 / price
                       await self.execute_buy(price, order_size, timestamp)
                   
                   elif signal == "sell" and self.has_position("BTCUSDT"):
                       # Sell all BTC
                       position_size = self.positions.get("BTCUSDT", 0)
                       await self.execute_sell(price, position_size, timestamp)
                   
                   # Print portfolio status
                   portfolio_value = self.calculate_portfolio_value(price)
                   print(f"{timestamp}: Portfolio: ${portfolio_value:.2f} | Balance: ${self.balance:.2f}")
       
       def generate_signal(self, price):
           """Simple trading signal generator"""
           # Implement your trading logic here
           # This is just a placeholder
           import random
           return random.choice(["buy", "sell", "hold"])
       
       async def execute_buy(self, price, size, timestamp):
           """Execute buy order in paper trading"""
           cost = price * size
           self.balance -= cost
           self.positions["BTCUSDT"] = self.positions.get("BTCUSDT", 0) + size
           
           self.trade_id += 1
           self.trades.append({
               "id": self.trade_id,
               "type": "buy",
               "price": price,
               "size": size,
               "cost": cost,
               "timestamp": timestamp
           })
           
           print(f"🟢 BUY: {size:.6f} BTC @ ${price:.2f} (Cost: ${cost:.2f})")
       
       async def execute_sell(self, price, size, timestamp):
           """Execute sell order in paper trading"""
           if size > self.positions.get("BTCUSDT", 0):
               size = self.positions["BTCUSDT"]
           
           revenue = price * size
           self.balance += revenue
           self.positions["BTCUSDT"] -= size
           
           self.trade_id += 1
           self.trades.append({
               "id": self.trade_id,
               "type": "sell",
               "price": price,
               "size": size,
               "revenue": revenue,
               "timestamp": timestamp
           })
           
           print(f"🔴 SELL: {size:.6f} BTC @ ${price:.2f} (Revenue: ${revenue:.2f})")
       
       def calculate_portfolio_value(self, current_price):
           """Calculate total portfolio value"""
           btc_value = self.positions.get("BTCUSDT", 0) * current_price
           return self.balance + btc_value

   # Usage
   async def run_paper_trading():
       config = WeexConfig.from_env()
       engine = PaperTradingEngine(initial_balance=10000)
       await engine.simulate_trading(config)

Connection Management
---------------------

Error Handling and Reconnection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def robust_websocket_client():
       """WebSocket client with robust error handling"""
       config = WeexConfig.from_env()
       
       max_reconnect_attempts = 5
       reconnect_delay = 5  # seconds
       
       for attempt in range(max_reconnect_attempts):
           try:
               async with WeexWebSocketClient(config) as ws_client:
                   print(f"🔌 Connected (attempt {attempt + 1})")
                   
                   async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
                       price = ticker_message.data.get("last")
                       print(f"Price: ${price}")
           
           except Exception as e:
               print(f"❌ Connection error: {e}")
               if attempt < max_reconnect_attempts - 1:
                   print(f"🔄 Reconnecting in {reconnect_delay} seconds...")
                   await asyncio.sleep(reconnect_delay)
                   # Increase delay for next attempt
                   reconnect_delay *= 2
               else:
                   print("💥 Max reconnection attempts reached")
                   raise

Message Filtering and Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def filtered_streaming():
       """Process only relevant messages"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("📊 Starting filtered streaming...")
           
           async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
               data = ticker_message.data
               
               # Filter by price changes > 0.1%
               price_change = float(data.get("change", 0))
               if abs(price_change) > 0.1:
                   price = data.get("last", "N/A")
                   volume = data.get("volume", "N/A")
                   
                   print(f"📈 Significant move: {price_change}% | Price: ${price} | Volume: {volume}")

Performance Optimization
------------------------

Memory Management
~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def memory_efficient_streaming():
       """Stream without accumulating data in memory"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("📊 Memory-efficient streaming...")
           
           async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
               # Process data immediately, don't store it
               price = float(ticker_message.data.get("last", 0))
               
               # Only keep what you need
               if price > 50000:  # Example filter
                   print(f"High price alert: ${price}")
               
               # No accumulation - memory stays constant

Batch Processing
~~~~~~~~~~~~~~~

.. code-block:: python

   async def batch_stream_processing():
       """Process messages in batches for efficiency"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("📊 Batch processing...")
           
           batch_size = 10
           batch = []
           
           async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
               batch.append(ticker_message.data)
               
               if len(batch) >= batch_size:
                   # Process batch
                   await process_ticker_batch(batch)
                   batch = []  # Clear batch
           
           # Process remaining messages
           if batch:
               await process_ticker_batch(batch)

   async def process_ticker_batch(ticker_batch):
       """Process a batch of ticker messages"""
       prices = [float(t.get("last", 0)) for t in ticker_batch]
       avg_price = sum(prices) / len(prices)
       max_price = max(prices)
       min_price = min(prices)
       
       print(f"Batch: Avg: ${avg_price:.2f} | Max: ${max_price:.2f} | Min: ${min_price:.2f}")

Common WebSocket Patterns
------------------------

Heartbeat and Health Checks
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def websocket_with_heartbeat():
       """WebSocket client with heartbeat monitoring"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           print("💓 Starting heartbeat...")
           
           last_message_time = time.time()
           heartbeat_interval = 30  # seconds
           
           async def heartbeat_checker():
               while True:
                   await asyncio.sleep(heartbeat_interval)
                   if time.time() - last_message_time > heartbeat_interval:
                       print("💔 No messages received - potential connection issue")
           
           heartbeat_task = asyncio.create_task(heartbeat_checker())
           
           try:
               async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
                   last_message_time = time.time()
                   print(f"💓 Message received: {ticker_message.data.get('last')}")
           
           finally:
               heartbeat_task.cancel()

Data Storage
~~~~~~~~~~~~

.. code-block:: python

   import aiosqlite
   import json

   async def store_stream_data():
       """Store WebSocket data to database"""
       config = WeexConfig.from_env()
       
       async with WeexWebSocketClient(config) as ws_client:
           async with aiosqlite.connect("ticker_data.db") as db:
               await db.execute("""
                   CREATE TABLE IF NOT EXISTS tickers (
                       timestamp REAL,
                       symbol TEXT,
                       price REAL,
                       volume REAL,
                       change REAL
                   )
               """)
               
               print("💾 Storing ticker data...")
               
               async for ticker_message in ws_client.stream_tickers(["BTCUSDT"]):
                   data = ticker_message.data
                   timestamp = ticker_message.timestamp
                   
                   await db.execute("""
                       INSERT INTO tickers (timestamp, symbol, price, volume, change)
                       VALUES (?, ?, ?, ?, ?)
                   """, (
                       timestamp,
                       "BTCUSDT",
                       float(data.get("last", 0)),
                       float(data.get("volume", 0)),
                       float(data.get("change", 0))
                   ))
                   
                   await db.commit()