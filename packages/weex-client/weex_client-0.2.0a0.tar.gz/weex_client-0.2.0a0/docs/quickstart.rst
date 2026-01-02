Quick Start Guide
=================

Welcome to the Weex Client! This guide will get you trading safely in 10 minutes. We'll focus on **paper trading** and **risk management** to help you learn without risking real money.

🎯 **Goal**: Set up your first safe trading environment and practice with paper trading.

⏱️ **Time**: 10 minutes

🛡️ **Safety**: Start with 1% risk rule and paper trading

Step 1: Environment Setup (2 minutes)
-------------------------------------

1. **Install Dependencies**

```bash
# Clone or navigate to the project
cd weex-client

# Install development environment
make install-dev
# Or manually:
# uv sync --dev --with docs
```

2. **Configure API Credentials**

```bash
# Copy example configuration
cp weex_client/.env.example weex_client/.env
```

3. **Edit Configuration File**

```bash
# Edit your credentials
nano weex_client/.env
```

Add your Weex API credentials:

```env
# Required - Get from https://weex.com/api
WEEX_API_KEY=your_weex_api_key_here
WEEX_SECRET_KEY=your_weex_secret_key_here  
WEEX_PASSPHRASE=your_weex_passphrase_here

# Recommended - Always start with development
WEEX_ENVIRONMENT=development

# Optional - API timeout
WEEX_TIMEOUT=30
```

🔐 **Getting API Credentials**:

1. Log into [Weex](https://weex.com)
2. Go to **API Management** → **Create API Key**
3. Set permissions: **Read + Trade** (disable withdrawals)
4. Copy the three values to your `.env` file
5. Enable **IP Whitelist** for additional security

Step 2: Verify Setup (1 minute)
---------------------------------

Run the safety validation:

```bash
make safety-check
```

You should see:
```
✅ Safety configuration validated
✅ Safety checks passed!
```

Test basic connectivity:

```bash
make demo
```

This runs safe examples without making real trades.

Step 3: Your First Safe Trade (5 minutes)
------------------------------------------

We'll use the **1% rule**: never risk more than 1% of your account balance on a single trade.

.. code-block:: python

   import asyncio
   import time
   from weex_client import WeexAsyncClient, WeexConfig
   from weex_client.models import PlaceOrderRequest

   async def place_first_safe_order():
       """Place your first order with 1% risk management"""
       
       # Load configuration
       config = WeexConfig.from_env()
       
       print("🎯 Placing first safe order...")
       
       async with WeexAsyncClient(config) as client:
           
           # Step 1: Check your balance
           balance_data = await client.get_account_balance()
           available_balance = float(balance_data["data"]["balance"])
           print(f"💰 Available balance: ${available_balance:.2f}")
           
           # Step 2: Apply 1% rule
           max_risk_amount = available_balance * 0.01
           print(f"🛡️ Max risk (1%): ${max_risk_amount:.2f}")
           
           # Step 3: Get current market price
           ticker_data = await client.get_ticker("BTCUSDT")
           current_price = float(ticker_data["data"]["last"])
           print(f"📊 BTC/USDT price: ${current_price:.2f}")
           
           # Step 4: Calculate safe position size
           safe_size = max_risk_amount / current_price
           print(f"📏 Safe position size: {safe_size:.6f} BTC")
           
           # Step 5: Place a very small test order
           order = PlaceOrderRequest(
               symbol="BTCUSDT",
               client_oid=f"first_trade_{int(time.time())}",
               size=str(min(safe_size, 0.001)),  # Cap at 0.001 BTC for testing
               type="1",           # Open position
               order_type="0",      # Market order
               match_price="1"      # Use current price
           )
           
           try:
               result = await client.place_order(order)
               order_id = result["data"]["orderId"]
               print(f"✅ Order placed successfully!")
               print(f"📋 Order ID: {order_id}")
               
               # Step 6: Immediately cancel for learning
               await asyncio.sleep(2)  # Wait a moment
               await client.cancel_order(order_id)
               print(f"✅ Order cancelled - learning complete!")
               
               return result
               
           except Exception as e:
               print(f"❌ Order failed: {e}")
               return None

   # Run the example
   if __name__ == "__main__":
       asyncio.run(place_first_safe_order())

```

**Save this as** ``my_first_trade.py`` **and run**:

```bash
python my_first_trade.py
```

Expected output:
```
🎯 Placing first safe order...
💰 Available balance: $1000.00
🛡️ Max risk (1%): $10.00
📊 BTC/USDT price: $50000.00
📏 Safe position size: 0.000200 BTC
✅ Order placed successfully!
📋 Order ID: 123456789
✅ Order cancelled - learning complete!
```

Step 4: Paper Trading Practice (2 minutes)
-----------------------------------------

Now let's set up paper trading to practice without real money:

.. code-block:: python

   class PaperTrader:
       def __init__(self, initial_balance=10000):
           self.balance = initial_balance
           self.positions = {}
           self.trades = []
           self.paper_trading = True
       
       async def paper_trade_simulation(self, symbol="BTCUSDT", duration=60):
           """Run paper trading simulation for specified duration"""
           
           config = WeexConfig.from_env()
           
           async with WeexAsyncClient(config) as client:
               print(f"🎯 Starting {duration}s paper trading simulation...")
               print(f"💰 Paper balance: ${self.balance:.2f}")
               
               start_time = time.time()
               
               while time.time() - start_time < duration:
                   
                   # Get real market data
                   ticker_data = await client.get_ticker(symbol)
                   current_price = float(ticker_data["data"]["last"])
                   
                   # Simple paper trading logic
                   decision = self.make_trading_decision(current_price, symbol)
                   
                   if decision == "buy" and self.balance > 100:
                       # Buy with 1% rule
                       position_size = self.calculate_position_size(current_price)
                       
                       self.positions[symbol] = {
                           "size": position_size,
                           "entry_price": current_price,
                           "entry_time": time.time()
                       }
                       
                       cost = position_size * current_price
                       self.balance -= cost
                       
                       self.trades.append({
                           "type": "buy",
                           "symbol": symbol,
                           "price": current_price,
                           "size": position_size,
                           "timestamp": time.time()
                       })
                       
                       print(f"🟢 PAPER BUY: {position_size:.6f} {symbol} @ ${current_price:.2f}")
                   
                   elif decision == "sell" and symbol in self.positions:
                       # Sell position
                       position = self.positions[symbol]
                       revenue = position["size"] * current_price
                       
                       self.balance += revenue
                       
                       pnl = (current_price - position["entry_price"]) * position["size"]
                       
                       self.trades.append({
                           "type": "sell",
                           "symbol": symbol,
                           "price": current_price,
                           "size": position["size"],
                           "pnl": pnl,
                           "timestamp": time.time()
                       })
                       
                       del self.positions[symbol]
                       
                       emoji = "📈" if pnl > 0 else "📉"
                           print(f"{emoji} PAPER SELL: {position['size']:.6f} {symbol} @ ${current_price:.2f} | PnL: ${pnl:.2f}")
                   
                   # Show portfolio status
                   portfolio_value = self.calculate_portfolio_value(current_price)
                   print(f"💼 Portfolio: ${portfolio_value:.2f} | Balance: ${self.balance:.2f}")
                   
                   await asyncio.sleep(5)  # Check every 5 seconds
       
       def make_trading_decision(self, price, symbol):
           """Simple trading decision logic - replace with your strategy"""
           import random
           return random.choice(["buy", "sell", "hold"])
       
       def calculate_position_size(self, price):
           """Calculate position size using 1% rule"""
           risk_amount = self.balance * 0.01
           return risk_amount / price
       
       def calculate_portfolio_value(self, current_price):
           """Calculate total portfolio value"""
           value = self.balance
           
           for symbol, position in self.positions.items():
               if symbol == "BTCUSDT":
                   value += position["size"] * current_price
           
           return value

   # Run paper trading
   async def run_paper_trading():
       trader = PaperTrader(initial_balance=10000)
       await trader.paper_trade_simulation(duration=60)  # 1 minute demo
       
       print("\n📊 Paper Trading Summary:")
       print(f"Final balance: ${trader.balance:.2f}")
       print(f"Total trades: {len(trader.trades)}")

   if __name__ == "__main__":
       asyncio.run(run_paper_trading())

```

Run this example:
```bash
python my_first_trade.py
```

Safety Checklist ✅
-------------------

Before trading with real money, verify:

- [ ] **Development Environment**: Set ``WEEX_ENVIRONMENT=development``
- [ ] **API Permissions**: Read + Trade only (no withdrawals)
- [ ] **1% Rule**: Never risk more than 1% per trade
- [ ] **Position Size**: Start with very small amounts (≤ 0.001 BTC)
- [ ] **Stop Loss**: Always consider stop-loss levels
- [ ] **Paper Trading**: Practice first with simulation

Common First Steps
------------------

1. **Check Balance**: Always know your available funds
2. **Get Market Data**: Understand current price and conditions
3. **Calculate Risk**: Apply 1% rule strictly
4. **Place Small Order**: Start with minimum position size
5. **Monitor**: Watch order execution and portfolio impact
6. **Review**: Analyze results and learn

Troubleshooting
---------------

**Issue**: "Missing API credentials"
```bash
# Check .env file exists
ls -la weex_client/.env

# Test configuration
make validate-config
```

**Issue**: "Connection error"
```bash
# Check network connectivity
ping api.weex.com

# Verify environment
echo $WEEX_ENVIRONMENT
```

**Issue**: "Rate limit exceeded"
- Wait a few minutes before trying again
- Reduce request frequency
- Use WebSocket for real-time data instead of polling

**Issue**: "Authentication failed"
- Double-check API credentials in .env
- Verify API key is enabled
- Check IP whitelist settings

Next Steps
-----------

🎓 **Continue Learning**:

1. **Read Trading Basics**: ``docs/trading/trading-basics.rst``
2. **Practice Paper Trading**: ``docs/trading/paper-trading.rst``
3. **Learn Leverage**: ``docs/trading/leverage-guide.rst``
4. **Safety Guidelines**: ``docs/trading/safety-guide.rst``

🛠️ **Useful Commands**:

```bash
# View all available commands
make help

# Get trader-specific help
make help-beginner
make help-safety
make help-paper

# Build and view documentation
make docs
make docs-serve

# Run tests (no API calls)
make test-safe
```

📚 **Documentation Resources**:

- **API Reference**: Check the ``api/`` directory for detailed method documentation
- **Examples**: Look in ``examples/`` for more trading patterns
- **WebSocket Guide**: Learn real-time data streaming
- **Error Handling**: Understand how to handle API errors gracefully

🎯 **Practice Path**:

1. **Week 1**: Paper trading with basic strategies
2. **Week 2**: Add risk management and stop losses
3. **Week 3**: Implement leverage (cautiously)
4. **Week 4**: Develop your own trading strategy

Remember: **Start small, stay safe, and always use the 1% rule!** 🛡️

---

**Need Help?**
- Check the documentation: ``make docs``
- Run safety checks: ``make safety-check``
- View examples: ``make demo``
- Test configuration: ``make validate-config``

Happy and safe trading! 🚀