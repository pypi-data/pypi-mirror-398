Trading Examples
=================

Real-world trading examples focused on safety, risk management, and best practices. All examples follow the 1% risk rule and start with paper trading.

🎯 **Focus**: Safe trading with proper risk management
🛡️ **Safety**: 1% balance limit, paper trading first
📊 **Scenarios**: Market making, trend following, mean reversion, grid trading

Basic Trading Workflow
---------------------

1. **Account Setup & Balance Check**
2. **Market Data Analysis**
3. **Risk Calculation (1% Rule)**
4. **Order Placement**
5. **Position Monitoring**
6. **Risk Management**

Example 1: Safe Market Order with 1% Rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   import time
   from weex_client import WeexAsyncClient, WeexConfig
   from weex_client.models import PlaceOrderRequest

   async def safe_market_order(symbol: str = "BTCUSDT"):
       """Place a safe market order using 1% risk management"""
       
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           print(f"🎯 Placing safe market order for {symbol}...")
           
           # Step 1: Get account balance
           balance_data = await client.get_account_balance()
           available_balance = float(balance_data["data"]["balance"])
           print(f"💰 Available balance: ${available_balance:.2f}")
           
           # Step 2: Apply 1% risk rule
           max_risk_amount = available_balance * 0.01
           print(f"🛡️ Max risk (1%): ${max_risk_amount:.2f}")
           
           # Step 3: Get current market price
           ticker_data = await client.get_ticker(symbol)
           current_price = float(ticker_data["data"]["last"])
           print(f"📊 Current {symbol} price: ${current_price:.2f}")
           
           # Step 4: Calculate safe position size
           safe_size = max_risk_amount / current_price
           print(f"📏 Safe position size: {safe_size:.6f} {symbol.replace('USDT', '')}")
           
           # Step 5: Create market order
           order = PlaceOrderRequest(
               symbol=symbol,
               client_oid=f"safe_market_{int(time.time())}",
               size=str(safe_size),
               type="1",           # Open position
               order_type="0",      # Market order
               match_price="1"      # Use current market price
           )
           
           try:
               # Step 6: Place order
               result = await client.place_order(order)
               order_id = result["data"]["orderId"]
               print(f"✅ Order placed successfully!")
               print(f"📋 Order ID: {order_id}")
               print(f"📊 Position: {safe_size:.6f} at ${current_price:.2f}")
               
               # Step 7: Monitor for a moment then cancel for demo
               await asyncio.sleep(3)
               await client.cancel_order(order_id)
               print(f"✅ Order cancelled - demo complete!")
               
               return {
                   "order_id": order_id,
                   "size": safe_size,
                   "price": current_price,
                   "risk_amount": max_risk_amount
               }
               
           except Exception as e:
               print(f"❌ Order failed: {e}")
               return None

   # Run example
   if __name__ == "__main__":
       asyncio.run(safe_market_order())

Example 2: Limit Order with Stop Loss
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def limit_order_with_stop_loss(symbol: str = "BTCUSDT"):
       """Place limit order with built-in stop loss"""
       
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           print(f"🎯 Placing limit order with stop loss for {symbol}...")
           
           # Get account and market data
           balance_data = await client.get_account_balance()
           ticker_data = await client.get_ticker(symbol)
           order_book_data = await client.get_order_book(symbol, limit=5)
           
           available_balance = float(balance_data["data"]["balance"])
           current_price = float(ticker_data["data"]["last"])
           best_bid = float(order_book_data["data"]["bids"][0][0]) if order_book_data["data"]["bids"] else current_price * 0.999
           
           # Calculate position size (1% rule)
           max_risk = available_balance * 0.01
           position_size = max_risk / current_price
           
           # Set limit order slightly below market for better price
           limit_price = best_bid * 0.999  # 0.1% below best bid
           
           # Set stop loss at 2% below entry
           stop_loss_price = limit_price * 0.98
           
           print(f"📊 Market price: ${current_price:.2f}")
           print(f"💎 Limit price: ${limit_price:.2f} (0.1% below market)")
           print(f"🛡️ Stop loss: ${stop_loss_price:.2f} (2% below entry)")
           print(f"📏 Position size: {position_size:.6f}")
           
           # Create limit order with stop loss
           order = PlaceOrderRequest(
               symbol=symbol,
               client_oid=f"limit_with_sl_{int(time.time())}",
               size=str(position_size),
               type="1",           # Open position
               order_type="1",      # Limit order
               match_price="0",      # Use specified price
               price=str(limit_price),
               preset_stop_loss_price=str(stop_loss_price)
           )
           
           try:
               result = await client.place_order(order)
               order_id = result["data"]["orderId"]
               
               print(f"✅ Limit order placed with stop loss!")
               print(f"📋 Order ID: {order_id}")
               print(f"💎 Limit price: ${limit_price:.2f}")
               print(f"🛡️ Stop loss: ${stop_loss_price:.2f}")
               
               return order_id
               
           except Exception as e:
               print(f"❌ Order failed: {e}")
               return None

Example 3: Paper Trading Market Making
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class PaperMarketMaker:
       def __init__(self, initial_balance=10000):
           self.balance = initial_balance
           self.positions = {}
           self.orders = []
           self.trade_id = 0
           
       async def market_make_simulation(self, symbol: str = "BTCUSDT", duration: int = 120):
           """Paper trading market making simulation"""
           
           config = WeexConfig.from_env()
           
           async with WeexAsyncClient(config) as client:
               print(f"🏪 Starting market making simulation for {symbol}...")
               print(f"💰 Initial balance: ${self.balance:.2f}")
               
               start_time = time.time()
               spread_pct = 0.001  # 0.1% spread
               
               while time.time() - start_time < duration:
                   
                   # Get real market data
                   ticker_data = await client.get_ticker(symbol)
                   order_book_data = await client.get_order_book(symbol, limit=1)
                   
                   current_price = float(ticker_data["data"]["last"])
                   
                   # Get best bid/ask from order book
                   best_bid = float(order_book_data["data"]["bids"][0][0]) if order_book_data["data"]["bids"] else current_price * 0.999
                   best_ask = float(order_book_data["data"]["asks"][0][0]) if order_book_data["data"]["asks"] else current_price * 1.001
                   
                   # Calculate our quotes (0.1% spread)
                   our_bid = best_bid * (1 - spread_pct)
                   our_ask = best_ask * (1 + spread_pct)
                   
                   # Calculate position sizes (1% of balance each side)
                   max_risk_per_side = self.balance * 0.01
                   bid_size = max_risk_per_side / our_bid
                   ask_size = max_risk_per_side / our_ask
                   
                   print(f"📊 Current: ${current_price:.2f} | Our Bid: ${our_bid:.2f} | Our Ask: ${our_ask:.2f}")
                   print(f"📏 Bid Size: {bid_size:.6f} | Ask Size: {ask_size:.6f}")
                   
                   # Simulate order fills
                   await self.simulate_fills(client, symbol, our_bid, our_ask, bid_size, ask_size, current_price)
                   
                   # Show portfolio status
                   portfolio_value = self.calculate_portfolio_value(symbol, current_price)
                   print(f"💼 Portfolio: ${portfolio_value:.2f} | Balance: ${self.balance:.2f}")
                   print("-" * 50)
                   
                   await asyncio.sleep(10)  # Update every 10 seconds
               
               print("🏪 Market making simulation complete!")
               
       async def simulate_fills(self, client, symbol, bid_price, ask_price, bid_size, ask_size, current_price):
           """Simulate order fills based on market movements"""
           
           # Simple fill simulation - if price moves across our quotes
           if current_price <= bid_price:
               # Our bid filled (we bought)
               cost = bid_size * bid_price
               if self.balance >= cost:
                   self.balance -= cost
                   self.positions[symbol] = self.positions.get(symbol, 0) + bid_size
                   
                   self.trade_id += 1
                   self.trades.append({
                       "id": self.trade_id,
                       "type": "buy",
                       "price": bid_price,
                       "size": bid_size,
                       "cost": cost,
                       "timestamp": time.time()
                   })
                   
                   print(f"🟢 BID FILLED: Bought {bid_size:.6f} @ ${bid_price:.2f}")
           
           elif current_price >= ask_price:
               # Our ask filled (we sold)
               if symbol in self.positions and self.positions[symbol] > 0:
                   sell_size = min(self.positions[symbol], ask_size)
                   revenue = sell_size * ask_price
                   self.balance += revenue
                   self.positions[symbol] -= sell_size
                   
                   pnl = (ask_price - self.get_average_price(symbol)) * sell_size
                   
                   self.trade_id += 1
                   self.trades.append({
                       "id": self.trade_id,
                       "type": "sell",
                       "price": ask_price,
                       "size": sell_size,
                       "revenue": revenue,
                       "pnl": pnl,
                       "timestamp": time.time()
                   })
                   
                   print(f"🔴 ASK FILLED: Sold {sell_size:.6f} @ ${ask_price:.2f} | PnL: ${pnl:.2f}")
       
       def get_average_price(self, symbol):
           """Calculate average entry price (simplified)"""
           buys = [t for t in self.trades if t["type"] == "buy"]
           if not buys:
               return 0
           return sum(t["price"] * t["size"] for t in buys) / sum(t["size"] for t in buys)
       
       def calculate_portfolio_value(self, symbol, current_price):
           """Calculate total portfolio value"""
           position_value = self.positions.get(symbol, 0) * current_price
           return self.balance + position_value

   # Run market making simulation
   async def run_market_making():
       market_maker = PaperMarketMaker(initial_balance=10000)
       await market_maker.market_make_simulation(duration=120)  # 2 minutes

   if __name__ == "__main__":
       asyncio.run(run_market_making())

Example 4: Trend Following Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def trend_following_strategy(symbol: str = "BTCUSDT", short_ma: int = 10, long_ma: int = 30):
       """Simple moving average crossover strategy"""
       
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           print(f"📈 Starting trend following strategy for {symbol}...")
           print(f"📊 Short MA: {short_ma} periods | Long MA: {long_ma} periods")
           
           price_history = []
           position = None
           last_signal = None
           
           # Collect initial data
           print("📊 Collecting initial market data...")
           for _ in range(long_ma + 10):  # Get extra data for stability
               ticker_data = await client.get_ticker(symbol)
               price = float(ticker_data["data"]["last"])
               price_history.append(price)
               await asyncio.sleep(2)  # 2 seconds between readings
           
           print("✅ Initial data collected, starting strategy...")
           
           while True:
               # Get latest price
               ticker_data = await client.get_ticker(symbol)
               current_price = float(ticker_data["data"]["last"])
               price_history.append(current_price)
               
               # Keep only required history
               if len(price_history) > long_ma + 10:
                   price_history.pop(0)
               
               # Calculate moving averages
               short_ma_value = sum(price_history[-short_ma:]) / short_ma
               long_ma_value = sum(price_history[-long_ma:]) / long_ma
               
               # Generate signal
               if short_ma_value > long_ma_value and last_signal != "buy":
                   signal = "buy"
               elif short_ma_value < long_ma_value and last_signal != "sell":
                   signal = "sell"
               else:
                   signal = "hold"
               
               print(f"📊 Price: ${current_price:.2f} | Short MA: ${short_ma_value:.2f} | Long MA: ${long_ma_value:.2f}")
               print(f"📈 Signal: {signal.upper()}")
               
               # Execute trades based on signal
               if signal == "buy" and position != "long":
                   # Place buy order
                   balance_data = await client.get_account_balance()
                   available_balance = float(balance_data["data"]["balance"])
                   
                   max_risk = available_balance * 0.01
                   position_size = max_risk / current_price
                   
                   order = PlaceOrderRequest(
                       symbol=symbol,
                       client_oid=f"trend_buy_{int(time.time())}",
                       size=str(position_size),
                       type="1",
                       order_type="0",  # Market order
                       match_price="1"
                   )
                   
                   try:
                       result = await client.place_order(order)
                       position = "long"
                       last_signal = "buy"
                       print(f"🟢 BUY signal executed: {position_size:.6f} @ ${current_price:.2f}")
                   except Exception as e:
                       print(f"❌ Buy order failed: {e}")
               
               elif signal == "sell" and position == "long":
                   # Close position
                   position_data = await client.get_position(symbol)
                   current_position_size = float(position_data["data"].get("size", 0))
                   
                   if current_position_size > 0:
                       order = PlaceOrderRequest(
                           symbol=symbol,
                           client_oid=f"trend_sell_{int(time.time())}",
                           size=str(current_position_size),
                           type="2",  # Close position
                           order_type="0",
                           match_price="1"
                       )
                       
                       try:
                           result = await client.place_order(order)
                           position = None
                           last_signal = "sell"
                           print(f"🔴 SELL signal executed: {current_position_size:.6f} @ ${current_price:.2f}")
                       except Exception as e:
                           print(f"❌ Sell order failed: {e}")
               
               else:
                   print("💤 HOLD - no action needed")
               
               print("-" * 60)
               await asyncio.sleep(10)  # Check every 10 seconds

   # Run trend following (use with paper trading!)
   async def run_trend_following():
       await trend_following_strategy()

   if __name__ == "__main__":
       print("⚠️  WARNING: This is a demonstration strategy.")
       print("🎯 Use paper trading first before real money!")
       asyncio.run(run_trend_following())

Example 5: Grid Trading Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class GridTrader:
       def __init__(self, symbol: str, grid_size: float = 0.02, grid_levels: int = 5):
           self.symbol = symbol
           self.grid_size = grid_size  # 2% grid spacing
           self.grid_levels = grid_levels
           self.center_price = None
           self.grid_orders = {}
           self.balance = 10000  # Paper balance
           self.positions = {}
           
       async def initialize_grid(self, client):
           """Initialize grid around current market price"""
           
           # Get current price
           ticker_data = await client.get_ticker(self.symbol)
           current_price = float(ticker_data["data"]["last"])
           self.center_price = current_price
           
           print(f"🎯 Initializing grid around ${current_price:.2f}")
           print(f"📏 Grid size: {self.grid_size*100:.1f}% | Levels: {self.grid_levels}")
           
           # Calculate grid levels
           for i in range(-self.grid_levels, self.grid_levels + 1):
               if i == 0:  # Skip center price
                   continue
               
               grid_price = current_price * (1 + i * self.grid_size)
               
               # Determine order type (buy below center, sell above)
               if i < 0:
                   # Buy orders below center
                   order_type = "1"  # Open position
                   size = self.calculate_position_size(grid_price)
                   
                   order = PlaceOrderRequest(
                       symbol=self.symbol,
                       client_oid=f"grid_buy_{i}_{int(time.time())}",
                       size=str(size),
                       type=order_type,
                       order_type="1",  # Limit order
                       match_price="0",
                       price=str(grid_price)
                   )
                   
                   print(f"🟢 Grid Buy ${grid_price:.2f} | Size: {size:.6f}")
               
               else:
                   # Sell orders above center
                   order_type = "2"  # Close position
                   
                   order = PlaceOrderRequest(
                       symbol=self.symbol,
                       client_oid=f"grid_sell_{i}_{int(time.time())}",
                       size="0.001",  # Will be adjusted based on position
                       type=order_type,
                       order_type="1",
                       match_price="0",
                       price=str(grid_price)
                   )
                   
                   print(f"🔴 Grid Sell ${grid_price:.2f}")
               
               # Store grid order info
               self.grid_orders[i] = {
                   "price": grid_price,
                   "order": order,
                   "filled": False
               }
           
           print(f"✅ Grid initialized with {len(self.grid_orders)} levels")
       
       def calculate_position_size(self, price):
           """Calculate position size using 1% rule"""
           max_risk = self.balance * 0.01
           return max_risk / price
       
       async def monitor_grid(self, client):
           """Monitor grid and replace filled orders"""
           
           print("🔍 Monitoring grid...")
           
           while True:
               # Check positions and order status
               try:
                   position_data = await client.get_position(self.symbol)
                   current_position = float(position_data["data"].get("size", 0))
                   
                   print(f"📊 Current position: {current_position:.6f}")
                   print(f"💰 Available balance: ${self.balance:.2f}")
                   
                   # Monitor for grid fills (simplified - in real implementation,
                   # you'd track actual order fills and replace them)
                   await asyncio.sleep(15)  # Check every 15 seconds
                   
               except Exception as e:
                   print(f"❌ Grid monitoring error: {e}")
                   await asyncio.sleep(30)

   async def run_grid_trading():
       """Run grid trading strategy"""
       
       symbol = "BTCUSDT"
       grid_trader = GridTrader(symbol, grid_size=0.02, grid_levels=3)
       
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           await grid_trader.initialize_grid(client)
           await grid_trader.monitor_grid(client)

   if __name__ == "__main__":
       print("🎯 Grid Trading Strategy")
       print("⚠️  This creates multiple orders at different price levels")
       print("🛡️  Make sure to understand grid trading risks!")
       asyncio.run(run_grid_trading())

Example 6: Risk Management Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def risk_management_dashboard():
       """Comprehensive risk management monitoring"""
       
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           while True:
               print("\n" + "="*60)
               print("🛡️ RISK MANAGEMENT DASHBOARD")
               print("="*60)
               
               try:
                   # Get account balance
                   balance_data = await client.get_account_balance()
                   available_balance = float(balance_data["data"]["balance"])
                   total_balance = float(balance_data["data"].get("total", available_balance))
                   frozen_balance = total_balance - available_balance
                   
                   print(f"💰 Total Balance: ${total_balance:.2f}")
                   print(f"💵 Available: ${available_balance:.2f}")
                   print(f"🧊 Frozen: ${frozen_balance:.2f}")
                   
                   # Get all positions
                   positions_data = await client.get_all_positions()
                   positions = positions_data.get("data", [])
                   
                   if positions:
                       print(f"\n📊 OPEN POSITIONS ({len(positions)}):")
                       total_exposure = 0
                       total_unrealized_pnl = 0
                       
                       for pos in positions:
                           symbol = pos.get("symbol", "Unknown")
                           size = float(pos.get("size", 0))
                           side = pos.get("side", "unknown")
                           entry_price = float(pos.get("entry_price", 0))
                           mark_price = float(pos.get("mark_price", 0))
                           unrealized_pnl = float(pos.get("unrealized_pnl", 0))
                           
                           exposure = abs(size * mark_price)
                           total_exposure += exposure
                           total_unrealized_pnl += unrealized_pnl
                           
                           # Risk metrics for this position
                           risk_pct = (exposure / total_balance) * 100 if total_balance > 0 else 0
                           pnl_pct = (unrealized_pnl / (size * entry_price)) * 100 if size > 0 and entry_price > 0 else 0
                           
                           status_emoji = "📈" if unrealized_pnl > 0 else "📉" if unrealized_pnl < 0 else "➡️"
                           
                           print(f"  {status_emoji} {symbol}: {side} {size:.6f} @ ${entry_price:.2f}")
                           print(f"     Current: ${mark_price:.2f} | PnL: ${unrealized_pnl:.2f} ({pnl_pct:+.2f}%)")
                           print(f"     Exposure: ${exposure:.2f} | Risk: {risk_pct:.2f}%")
                           print()
                       
                       # Portfolio risk summary
                       print(f"📈 TOTAL EXPOSURE: ${total_exposure:.2f}")
                       print(f"📊 EXPOSURE RATIO: {(total_exposure/total_balance)*100:.2f}%")
                       print(f"💹 TOTAL UNREALIZED PnL: ${total_unrealized_pnl:.2f}")
                       
                       # Risk alerts
                       exposure_ratio = total_exposure / total_balance if total_balance > 0 else 0
                       if exposure_ratio > 0.5:
                           print("⚠️  HIGH EXPOSURE WARNING: >50% of balance")
                       if total_unrealized_pnl < -total_balance * 0.1:
                           print("🚨 HIGH LOSS WARNING: >10% portfolio loss")
                       
                   else:
                       print("📊 No open positions")
                   
                   # Calculate 1% rule limits
                   one_percent_risk = total_balance * 0.01
                   max_position_size = one_percent_risk / 50000  # Assuming $50k BTC price
                   
                   print(f"\n🛡️ RISK LIMITS (1% Rule):")
                   print(f"💸 Max risk per trade: ${one_percent_risk:.2f}")
                   print(f"📏 Max position size: {max_position_size:.6f} BTC")
                   
                   # Get recent market data for context
                   ticker_data = await client.get_ticker("BTCUSDT")
                   btc_price = float(ticker_data["data"]["last"])
                   btc_change = float(ticker_data["data"].get("change", 0))
                   
                   print(f"\n📊 MARKET CONTEXT:")
                   print(f"₿ BTC Price: ${btc_price:.2f} ({btc_change:+.2f}%)")
                   
                   # Safety score
                   safety_score = calculate_safety_score(
                       total_balance, total_exposure, total_unrealized_pnl, len(positions)
                   )
                   print(f"🛡️ SAFETY SCORE: {safety_score}/100")
                   
                   print("\n" + "="*60)
                   
               except Exception as e:
                   print(f"❌ Dashboard error: {e}")
               
               # Update every 30 seconds
               await asyncio.sleep(30)

   def calculate_safety_score(balance, exposure, unrealized_pnl, position_count):
       """Calculate a safety score (0-100)"""
       score = 100
       
       # Exposure penalty
       exposure_ratio = exposure / balance if balance > 0 else 0
       if exposure_ratio > 0.3:
           score -= (exposure_ratio - 0.3) * 100
       
       # Loss penalty
       loss_ratio = abs(unrealized_pnl) / balance if balance > 0 and unrealized_pnl < 0 else 0
       if loss_ratio > 0.05:
           score -= loss_ratio * 50
       
       # Position concentration penalty
       if position_count > 5:
           score -= (position_count - 5) * 5
       
       return max(0, min(100, int(score)))

   # Run risk dashboard
   async def run_dashboard():
       await risk_management_dashboard()

   if __name__ == "__main__":
       print("🛡️ Starting Risk Management Dashboard")
       print("Press Ctrl+C to stop")
       asyncio.run(run_dashboard())

Key Trading Principles
---------------------

1. **1% Rule**: Never risk more than 1% of your balance on a single trade
2. **Stop Losses**: Always know your exit point before entering
3. **Position Sizing**: Adjust size based on volatility and confidence
4. **Paper Trading**: Practice strategies without real money
5. **Risk Monitoring**: Continuously monitor portfolio exposure
6. **Market Context**: Understand current market conditions

Common Trading Mistakes to Avoid
-------------------------------

1. **Overleveraging**: Using too much leverage
2. **No Stop Loss**: Trading without exit plans
3. **Revenge Trading**: Trying to win back losses quickly
4. **Ignoring Risk**: Not calculating position sizes properly
5. **Emotional Trading**: Making decisions based on fear/greed
6. **No Strategy**: Trading without a clear plan

Remember: **Start small, stay safe, and always use the 1% rule!** 🛡️