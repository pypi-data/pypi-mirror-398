Paper Trading Scenarios
======================

Practice trading strategies without risking real money. Paper trading helps you learn market dynamics, test strategies, and build confidence before using real funds.

🎯 **Goal**: Build trading skills safely
🛡️ **Safety**: Zero financial risk
📊 **Scenarios**: Market making, trend following, mean reversion, grid trading

Getting Started with Paper Trading
---------------------------------

1. **Environment Setup**
```bash
# Always use development environment
export WEEX_ENVIRONMENT=development

# Test configuration
make safety-check
```

2. **Create Paper Trading Class**
```python
from weex_client import WeexAsyncClient, WeexConfig

class PaperTrader:
    def __init__(self, initial_balance=10000):
        self.balance = initial_balance
        self.positions = {}
        self.trades = []
        self.trade_id = 0
        self.commission_rate = 0.001  # 0.1% commission
        
    def get_portfolio_value(self, current_prices):
        """Calculate total portfolio value"""
        portfolio_value = self.balance
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                portfolio_value += position["size"] * current_price
        
        return portfolio_value
    
    def calculate_unrealized_pnl(self, current_prices):
        """Calculate unrealized profit/loss"""
        total_pnl = 0.0
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                entry_price = position["entry_price"]
                pnl = (current_price - entry_price) * position["size"]
                total_pnl += pnl
        
        return total_pnl
```

Scenario 1: Market Making
--------------------------

**Concept**: Place limit orders on both sides of the order book to profit from the bid-ask spread.

**Strategy**: 
- Buy slightly below best bid
- Sell slightly above best ask
- Manage inventory risk
- Profit from small price differences

```python
class MarketMaker(PaperTrader):
    def __init__(self, initial_balance=10000, spread_pct=0.001):
        super().__init__(initial_balance)
        self.spread_pct = spread_pct  # 0.1% spread
        self.max_inventory_ratio = 0.3  # Max 30% in inventory
        self.min_order_size = 10  # Minimum $10 order
        
    async def market_make_simulation(self, symbol="BTCUSDT", duration=300):
        """Run market making simulation"""
        
        config = WeexConfig.from_env()
        
        async with WeexAsyncClient(config) as client:
            print(f"🏪 Starting market making for {symbol}")
            print(f"📊 Spread: {self.spread_pct*100:.2f}%")
            print(f"💰 Initial balance: ${self.balance:.2f}")
            
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    # Get real market data
                    ticker_data = await client.get_ticker(symbol)
                    order_book_data = await client.get_order_book(symbol, limit=1)
                    
                    current_price = float(ticker_data["data"]["last"])
                    best_bid = float(order_book_data["data"]["bids"][0][0]) if order_book_data["data"]["bids"] else current_price * 0.999
                    best_ask = float(order_book_data["data"]["asks"][0][0]) if order_book_data["data"]["asks"] else current_price * 1.001
                    
                    # Calculate our quotes
                    our_bid = best_bid * (1 - self.spread_pct)
                    our_ask = best_ask * (1 + self.spread_pct)
                    
                    # Check inventory constraints
                    current_inventory = self.positions.get(symbol, {}).get("size", 0)
                    inventory_value = abs(current_inventory) * current_price
                    max_inventory = self.balance * self.max_inventory_ratio
                    
                    # Place orders based on inventory
                    await self.manage_inventory(
                        client, symbol, current_price, 
                        our_bid, our_ask, current_inventory,
                        inventory_value, max_inventory
                    )
                    
                    # Show status
                    portfolio_value = self.get_portfolio_value({symbol: current_price})
                    unrealized_pnl = self.calculate_unrealized_pnl({symbol: current_price})
                    
                    print(f"📊 Price: ${current_price:.2f} | Bid: ${our_bid:.2f} | Ask: ${our_ask:.2f}")
                    print(f"📦 Inventory: {current_inventory:.6f} | Value: ${inventory_value:.2f}")
                    print(f"💼 Portfolio: ${portfolio_value:.2f} | PnL: ${unrealized_pnl:.2f}")
                    print("-" * 60)
                    
                    await asyncio.sleep(10)  # Update every 10 seconds
                    
                except Exception as e:
                    print(f"❌ Market making error: {e}")
                    await asyncio.sleep(5)
            
            # End of simulation
            await self.close_all_positions(client, symbol)
            final_value = self.get_portfolio_value({symbol: current_price})
            total_pnl = final_value - self.initial_balance
            
            print(f"🏪 Market making complete!")
            print(f"💰 Final portfolio: ${final_value:.2f}")
            print(f"📈 Total PnL: ${total_pnl:.2f} ({total_pnl/self.initial_balance*100:+.2f}%)")
            print(f"📊 Total trades: {len(self.trades)}")
    
    async def manage_inventory(self, client, symbol, current_price, 
                           our_bid, our_ask, current_inventory,
                           inventory_value, max_inventory):
        """Manage positions based on inventory constraints"""
        
        # Calculate position sizes
        max_risk_per_side = self.balance * 0.01  # 1% rule per side
        
        if current_inventory >= 0:  # Long or neutral bias
            # More willing to sell, less willing to buy
            ask_size = min(max_risk_per_side / our_ask, 
                          current_inventory + max_risk_per_side / our_ask)
            bid_size = min(max_risk_per_side / our_bid,
                         max_risk_per_side / our_bid / 2)
        else:  # Short bias
            # More willing to buy, less willing to sell
            bid_size = min(max_risk_per_side / our_bid,
                         abs(current_inventory) + max_risk_per_side / our_bid)
            ask_size = min(max_risk_per_side / our_ask,
                         max_risk_per_side / our_ask / 2)
        
        # Place paper orders (simulated)
        await self.simulate_order_fill(
            "buy", our_bid, bid_size, current_price, symbol
        )
        await self.simulate_order_fill(
            "sell", our_ask, ask_size, current_price, symbol
        )
    
    async def simulate_order_fill(self, side, price, size, current_price, symbol):
        """Simulate order fill based on price movement"""
        
        # Simple fill simulation - random chance based on how close we are to market
        import random
        price_diff = abs(current_price - price) / current_price
        
        if side == "buy" and current_price <= price:
            fill_probability = max(0.1, 0.9 - price_diff * 100)
        elif side == "sell" and current_price >= price:
            fill_probability = max(0.1, 0.9 - price_diff * 100)
        else:
            fill_probability = 0.0
        
        if random.random() < fill_probability * 0.3:  # Reduce fill rate for realism
            await self.execute_paper_trade(side, price, size, symbol)
    
    async def execute_paper_trade(self, side, price, size, symbol):
        """Execute a paper trade"""
        
        commission = size * price * self.commission_rate
        
        if side == "buy":
            cost = size * price + commission
            if self.balance >= cost:
                self.balance -= cost
                current_pos = self.positions.get(symbol, {"size": 0, "entry_price": price})
                
                # Update weighted average entry price
                old_size = current_pos["size"]
                new_size = old_size + size
                if new_size != 0:
                    current_pos["entry_price"] = (
                        (current_pos["entry_price"] * old_size + price * size) / new_size
                    )
                current_pos["size"] = new_size
                self.positions[symbol] = current_pos
                
                self.trade_id += 1
                self.trades.append({
                    "id": self.trade_id,
                    "side": "buy",
                    "symbol": symbol,
                    "price": price,
                    "size": size,
                    "commission": commission,
                    "timestamp": time.time()
                })
                
                print(f"🟢 PAPER BUY: {size:.6f} {symbol} @ ${price:.2f}")
        
        elif side == "sell":
            current_pos = self.positions.get(symbol, {"size": 0, "entry_price": 0})
            if current_pos["size"] >= size:
                revenue = size * price - commission
                self.balance += revenue
                
                # Calculate realized PnL
                realized_pnl = (price - current_pos["entry_price"]) * size - commission
                current_pos["size"] -= size
                
                if current_pos["size"] == 0:
                    del self.positions[symbol]
                else:
                    self.positions[symbol] = current_pos
                
                self.trade_id += 1
                self.trades.append({
                    "id": self.trade_id,
                    "side": "sell",
                    "symbol": symbol,
                    "price": price,
                    "size": size,
                    "commission": commission,
                    "realized_pnl": realized_pnl,
                    "timestamp": time.time()
                })
                
                print(f"🔴 PAPER SELL: {size:.6f} {symbol} @ ${price:.2f} | PnL: ${realized_pnl:.2f}")

# Run market making simulation
async def run_market_making():
    market_maker = MarketMaker(initial_balance=10000, spread_pct=0.001)
    await market_maker.market_make_simulation(duration=300)  # 5 minutes

if __name__ == "__main__":
    print("🏪 Market Making Paper Trading")
    print("💡 This strategy profits from bid-ask spread")
    print("⚠️  Requires careful inventory management")
    asyncio.run(run_market_making())
```

Scenario 2: Trend Following with Leverage
----------------------------------------

**Concept**: Follow market trends using technical indicators and leverage for enhanced returns.

**Strategy**:
- Use moving averages for trend direction
- Apply controlled leverage (1x, 2x, 3x)
- Implement stop-loss and take-profit
- Risk management with position sizing

```python
class TrendFollower(PaperTrader):
    def __init__(self, initial_balance=10000, leverage=2):
        super().__init__(initial_balance)
        self.leverage = leverage
        self.short_ma = 10
        self.long_ma = 30
        self.stop_loss_pct = 0.02  # 2% stop loss
        self.take_profit_pct = 0.06  # 6% take profit
        
    async def trend_following_simulation(self, symbol="BTCUSDT", duration=600):
        """Run trend following with leverage"""
        
        config = WeexConfig.from_env()
        
        async with WeexAsyncClient(config) as client:
            print(f"📈 Starting trend following for {symbol}")
            print(f"⚡ Leverage: {self.leverage}x")
            print(f"📊 MA: {self.short_ma}/{self.long_ma}")
            print(f"🛡️ Stop Loss: {self.stop_loss_pct*100:.1f}% | Take Profit: {self.take_profit_pct*100:.1f}%")
            print(f"💰 Initial balance: ${self.balance:.2f}")
            
            price_history = []
            position = None
            entry_price = None
            stop_loss = None
            take_profit = None
            
            # Collect initial data
            print("📊 Collecting initial market data...")
            for _ in range(self.long_ma + 10):
                ticker_data = await client.get_ticker(symbol)
                price = float(ticker_data["data"]["last"])
                price_history.append(price)
                await asyncio.sleep(2)
            
            print("✅ Initial data collected, starting strategy...")
            
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    # Get latest price
                    ticker_data = await client.get_ticker(symbol)
                    current_price = float(ticker_data["data"]["last"])
                    price_history.append(current_price)
                    
                    if len(price_history) > self.long_ma + 10:
                        price_history.pop(0)
                    
                    # Calculate moving averages
                    short_ma = sum(price_history[-self.short_ma:]) / self.short_ma
                    long_ma = sum(price_history[-self.long_ma:]) / self.long_ma
                    
                    # Generate signals
                    if short_ma > long_ma and position != "long":
                        signal = "buy"
                    elif short_ma < long_ma and position != "short":
                        signal = "sell"
                    else:
                        signal = "hold"
                    
                    print(f"📊 Price: ${current_price:.2f} | Short MA: ${short_ma:.2f} | Long MA: ${long_ma:.2f}")
                    print(f"📈 Signal: {signal.upper()} | Position: {position or 'none'}")
                    
                    # Check stop loss and take profit
                    if position == "long":
                        if current_price <= stop_loss:
                            print(f"🛡️ STOP LOSS triggered at ${current_price:.2f}")
                            await self.close_position(client, symbol, current_price, "stop_loss")
                            position = None
                            entry_price = None
                            stop_loss = None
                            take_profit = None
                        elif current_price >= take_profit:
                            print(f"🎯 TAKE PROFIT triggered at ${current_price:.2f}")
                            await self.close_position(client, symbol, current_price, "take_profit")
                            position = None
                            entry_price = None
                            stop_loss = None
                            take_profit = None
                    
                    elif position == "short":
                        if current_price >= stop_loss:
                            print(f"🛡️ STOP LOSS triggered at ${current_price:.2f}")
                            await self.close_position(client, symbol, current_price, "stop_loss")
                            position = None
                            entry_price = None
                            stop_loss = None
                            take_profit = None
                        elif current_price <= take_profit:
                            print(f"🎯 TAKE PROFIT triggered at ${current_price:.2f}")
                            await self.close_position(client, symbol, current_price, "take_profit")
                            position = None
                            entry_price = None
                            stop_loss = None
                            take_profit = None
                    
                    # Execute new positions
                    if signal == "buy" and position != "long":
                        position_size = await self.calculate_leveraged_position_size(
                            client, current_price, "long"
                        )
                        
                        if position_size > 0:
                            await self.open_position(
                                client, symbol, current_price, position_size, "long"
                            )
                            position = "long"
                            entry_price = current_price
                            stop_loss = current_price * (1 - self.stop_loss_pct)
                            take_profit = current_price * (1 + self.take_profit_pct)
                            
                            print(f"🟢 LONG position opened: {position_size:.6f} @ ${current_price:.2f}")
                            print(f"🛡️ Stop Loss: ${stop_loss:.2f} | 🎯 Take Profit: ${take_profit:.2f}")
                    
                    elif signal == "sell" and position != "short":
                        position_size = await self.calculate_leveraged_position_size(
                            client, current_price, "short"
                        )
                        
                        if position_size > 0:
                            await self.open_position(
                                client, symbol, current_price, position_size, "short"
                            )
                            position = "short"
                            entry_price = current_price
                            stop_loss = current_price * (1 + self.stop_loss_pct)
                            take_profit = current_price * (1 - self.take_profit_pct)
                            
                            print(f"🔴 SHORT position opened: {position_size:.6f} @ ${current_price:.2f}")
                            print(f"🛡️ Stop Loss: ${stop_loss:.2f} | 🎯 Take Profit: ${take_profit:.2f}")
                    
                    # Show portfolio status
                    portfolio_value = self.get_portfolio_value({symbol: current_price})
                    unrealized_pnl = self.calculate_unrealized_pnl({symbol: current_price})
                    leverage_ratio = self.calculate_leverage_ratio(current_price)
                    
                    print(f"💼 Portfolio: ${portfolio_value:.2f} | PnL: ${unrealized_pnl:.2f}")
                    print(f"⚡ Leverage ratio: {leverage_ratio:.2f}x")
                    print("-" * 70)
                    
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    print(f"❌ Trend following error: {e}")
                    await asyncio.sleep(5)
            
            # Close any remaining positions
            if position:
                ticker_data = await client.get_ticker(symbol)
                final_price = float(ticker_data["data"]["last"])
                await self.close_position(client, symbol, final_price, "end_simulation")
            
            # Final summary
            final_value = self.get_portfolio_value({symbol: current_price})
            total_pnl = final_value - self.initial_balance
            return_pct = (total_pnl / self.initial_balance) * 100
            
            print(f"📈 Trend following complete!")
            print(f"💰 Final portfolio: ${final_value:.2f}")
            print(f"📈 Total PnL: ${total_pnl:.2f} ({return_pct:+.2f}%)")
            print(f"📊 Total trades: {len(self.trades)}")
            print(f"⚡ Max leverage used: {self.leverage}x")
    
    async def calculate_leveraged_position_size(self, client, current_price, direction):
        """Calculate position size with leverage and 1% rule"""
        
        # Available balance for margin
        available_balance = self.balance
        
        # Calculate position size with leverage
        max_position_value = available_balance * self.leverage
        
        # Apply 1% rule to actual risk (not leveraged amount)
        max_risk_amount = available_balance * 0.01
        max_position_size = max_risk_amount / current_price
        
        # Take minimum of leverage constraint and risk rule
        leveraged_size = max_position_value / current_price
        final_size = min(leveraged_size, max_position_size)
        
        return final_size
    
    async def open_position(self, client, symbol, price, size, direction):
        """Open leveraged position"""
        
        # Calculate margin requirement
        margin = (size * price) / self.leverage
        
        if self.balance >= margin:
            self.balance -= margin
            
            self.positions[symbol] = {
                "size": size if direction == "long" else -size,
                "entry_price": price,
                "leverage": self.leverage,
                "margin": margin,
                "direction": direction
            }
            
            self.trade_id += 1
            self.trades.append({
                "id": self.trade_id,
                "type": "open",
                "direction": direction,
                "symbol": symbol,
                "price": price,
                "size": size,
                "margin": margin,
                "leverage": self.leverage,
                "timestamp": time.time()
            })
    
    async def close_position(self, client, symbol, current_price, reason):
        """Close leveraged position"""
        
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position_size = abs(position["size"])
        margin = position["margin"]
        entry_price = position["entry_price"]
        leverage = position["leverage"]
        
        # Calculate PnL
        if position["size"] > 0:  # Long position
            pnl = (current_price - entry_price) * position_size
        else:  # Short position
            pnl = (entry_price - current_price) * position_size
        
        # Return margin + PnL
        self.balance += margin + pnl
        
        self.trade_id += 1
        self.trades.append({
            "id": self.trade_id,
            "type": "close",
            "symbol": symbol,
            "entry_price": entry_price,
            "close_price": current_price,
            "size": position_size,
            "pnl": pnl,
            "margin_returned": margin,
            "leverage": leverage,
            "reason": reason,
            "timestamp": time.time()
        })
        
        # Remove position
        del self.positions[symbol]
        
        print(f"✅ Position closed: {position_size:.6f} @ ${current_price:.2f}")
        print(f"📊 PnL: ${pnl:.2f} | Margin returned: ${margin:.2f}")
    
    def calculate_leverage_ratio(self, current_price):
        """Calculate current leverage ratio"""
        
        total_position_value = 0.0
        for symbol, position in self.positions.items():
            position_value = abs(position["size"]) * current_prices.get(symbol, current_price)
            total_position_value += position_value
        
        if self.balance > 0:
            return total_position_value / self.balance
        return 0.0

# Run trend following with different leverage levels
async def run_trend_following():
    print("📈 Trend Following Paper Trading")
    print("⚡ Test different leverage levels:")
    
    leverage_levels = [1, 2, 3]
    
    for leverage in leverage_levels:
        print(f"\n--- Testing {leverage}x Leverage ---")
        trader = TrendFollower(initial_balance=10000, leverage=leverage)
        await trader.trend_following_simulation(duration=300)  # 5 minutes each
        
        # Wait between tests
        if leverage < max(leverage_levels):
            print("⏳ Waiting 30 seconds before next test...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    print("📈 Trend Following with Leverage")
    print("⚠️  Higher leverage = Higher risk AND higher potential returns")
    print("🛡️  Always use stop losses with leverage!")
    asyncio.run(run_trend_following())
```

Scenario 3: Mean Reversion Strategy
----------------------------------

**Concept**: Bet on prices returning to their historical average after extreme movements.

**Strategy**:
- Calculate Bollinger Bands
- Buy when price hits lower band
- Sell when price hits upper band
- Use leverage for enhanced returns
- Implement risk management

```python
class MeanReversionTrader(PaperTrader):
    def __init__(self, initial_balance=10000, leverage=1.5):
        super().__init__(initial_balance)
        self.leverage = leverage
        self.bb_period = 20
        self.bb_std = 2.0  # 2 standard deviations
        self.position_size_pct = 0.8  # Use 80% of available margin
        
    async def mean_reversion_simulation(self, symbol="BTCUSDT", duration=600):
        """Run mean reversion strategy"""
        
        config = WeexConfig.from_env()
        
        async with WeexAsyncClient(config) as client:
            print(f"📊 Starting mean reversion for {symbol}")
            print(f"⚡ Leverage: {self.leverage}x")
            print(f"📈 Bollinger Bands: {self.bb_period} period, {self.bb_std} std")
            print(f"💰 Initial balance: ${self.balance:.2f}")
            
            price_history = []
            position = None
            entry_price = None
            entry_time = None
            
            # Collect initial data
            print("📊 Collecting initial market data...")
            for _ in range(self.bb_period + 10):
                ticker_data = await client.get_ticker(symbol)
                price = float(ticker_data["data"]["last"])
                price_history.append(price)
                await asyncio.sleep(2)
            
            print("✅ Initial data collected, starting strategy...")
            
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    # Get latest price
                    ticker_data = await client.get_ticker(symbol)
                    current_price = float(ticker_data["data"]["last"])
                    price_history.append(current_price)
                    
                    if len(price_history) > self.bb_period + 10:
                        price_history.pop(0)
                    
                    # Calculate Bollinger Bands
                    recent_prices = price_history[-self.bb_period:]
                    sma = sum(recent_prices) / len(recent_prices)
                    
                    # Calculate standard deviation
                    variance = sum((price - sma) ** 2 for price in recent_prices) / len(recent_prices)
                    std = variance ** 0.5
                    
                    upper_band = sma + (self.bb_std * std)
                    lower_band = sma - (self.bb_std * std)
                    
                    # Calculate position within bands
                    if upper_band != lower_band:
                        band_position = (current_price - lower_band) / (upper_band - lower_band)
                    else:
                        band_position = 0.5
                    
                    # Generate signals
                    if current_price <= lower_band and position != "long":
                        signal = "buy"
                    elif current_price >= upper_band and position != "short":
                        signal = "sell"
                    elif position and abs(band_position - 0.5) < 0.1:
                        signal = "close"  # Close when near middle
                    else:
                        signal = "hold"
                    
                    print(f"📊 Price: ${current_price:.2f} | SMA: ${sma:.2f}")
                    print(f"📈 Bands: ${lower_band:.2f} - ${upper_band:.2f}")
                    print(f"📍 Band Position: {band_position:.2f} (0=lower, 1=upper)")
                    print(f"🎯 Signal: {signal.upper()} | Position: {position or 'none'}")
                    
                    # Execute trades
                    if signal == "buy" and position != "long":
                        position_size = await self.calculate_position_size(
                            client, current_price
                        )
                        
                        if position_size > 0:
                            await self.open_position(
                                client, symbol, current_price, position_size, "long"
                            )
                            position = "long"
                            entry_price = current_price
                            entry_time = time.time()
                            
                            print(f"🟢 LONG position: {position_size:.6f} @ ${current_price:.2f}")
                            print(f"📍 At lower band: ${lower_band:.2f}")
                    
                    elif signal == "sell" and position != "short":
                        position_size = await self.calculate_position_size(
                            client, current_price
                        )
                        
                        if position_size > 0:
                            await self.open_position(
                                client, symbol, current_price, position_size, "short"
                            )
                            position = "short"
                            entry_price = current_price
                            entry_time = time.time()
                            
                            print(f"🔴 SHORT position: {position_size:.6f} @ ${current_price:.2f}")
                            print(f"📍 At upper band: ${upper_band:.2f}")
                    
                    elif signal == "close" and position:
                        # Close position when price returns to mean
                        await self.close_position(
                            client, symbol, current_price, "mean_reversion"
                        )
                        
                        if entry_time:
                            duration = time.time() - entry_time
                            pnl = self.calculate_position_pnl(symbol, current_price)
                            print(f"✅ Position closed after {duration:.0f}s")
                            print(f"📊 PnL: ${pnl:.2f}")
                        
                        position = None
                        entry_price = None
                        entry_time = None
                    
                    # Show portfolio status
                    portfolio_value = self.get_portfolio_value({symbol: current_price})
                    unrealized_pnl = self.calculate_unrealized_pnl({symbol: current_price})
                    
                    print(f"💼 Portfolio: ${portfolio_value:.2f} | PnL: ${unrealized_pnl:.2f}")
                    print("-" * 60)
                    
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    print(f"❌ Mean reversion error: {e}")
                    await asyncio.sleep(5)
            
            # Close any remaining positions
            if position:
                ticker_data = await client.get_ticker(symbol)
                final_price = float(ticker_data["data"]["last"])
                await self.close_position(client, symbol, final_price, "end_simulation")
            
            # Final summary
            final_value = self.get_portfolio_value({symbol: current_price})
            total_pnl = final_value - self.initial_balance
            return_pct = (total_pnl / self.initial_balance) * 100
            
            print(f"📊 Mean reversion complete!")
            print(f"💰 Final portfolio: ${final_value:.2f}")
            print(f"📈 Total PnL: ${total_pnl:.2f} ({return_pct:+.2f}%)")
            print(f"📊 Total trades: {len(self.trades)}")
            
            # Analyze performance
            winning_trades = [t for t in self.trades if t.get("pnl", 0) > 0]
            losing_trades = [t for t in self.trades if t.get("pnl", 0) < 0]
            
            if winning_trades or losing_trades:
                win_rate = len(winning_trades) / (len(winning_trades) + len(losing_trades)) * 100
                avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
                avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
                
                print(f"📊 Win Rate: {win_rate:.1f}%")
                print(f"📈 Avg Win: ${avg_win:.2f}")
                print(f"📉 Avg Loss: ${avg_loss:.2f}")
    
    async def calculate_position_size(self, client, current_price):
        """Calculate position size with leverage and risk management"""
        
        available_balance = self.balance
        margin_available = available_balance * self.position_size_pct
        
        # Calculate position size
        max_position_value = margin_available * self.leverage
        position_size = max_position_value / current_price
        
        return position_size
    
    async def open_position(self, client, symbol, price, size, direction):
        """Open mean reversion position"""
        
        margin = (size * price) / self.leverage
        
        if self.balance >= margin:
            self.balance -= margin
            
            self.positions[symbol] = {
                "size": size if direction == "long" else -size,
                "entry_price": price,
                "leverage": self.leverage,
                "margin": margin,
                "direction": direction,
                "strategy": "mean_reversion"
            }
            
            self.trade_id += 1
            self.trades.append({
                "id": self.trade_id,
                "type": "open",
                "direction": direction,
                "symbol": symbol,
                "price": price,
                "size": size,
                "margin": margin,
                "leverage": self.leverage,
                "timestamp": time.time()
            })
    
    async def close_position(self, client, symbol, current_price, reason):
        """Close mean reversion position"""
        
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position_size = abs(position["size"])
        margin = position["margin"]
        entry_price = position["entry_price"]
        
        # Calculate PnL
        if position["size"] > 0:  # Long position
            pnl = (current_price - entry_price) * position_size
        else:  # Short position
            pnl = (entry_price - current_price) * position_size
        
        # Return margin + PnL
        self.balance += margin + pnl
        
        self.trade_id += 1
        self.trades.append({
            "id": self.trade_id,
            "type": "close",
            "symbol": symbol,
            "entry_price": entry_price,
            "close_price": current_price,
            "size": position_size,
            "pnl": pnl,
            "margin_returned": margin,
            "reason": reason,
            "timestamp": time.time()
        })
        
        del self.positions[symbol]
    
    def calculate_position_pnl(self, symbol, current_price):
        """Calculate unrealized PnL for open position"""
        
        if symbol not in self.positions:
            return 0.0
        
        position = self.positions[symbol]
        entry_price = position["entry_price"]
        position_size = abs(position["size"])
        
        if position["size"] > 0:  # Long
            return (current_price - entry_price) * position_size
        else:  # Short
            return (entry_price - current_price) * position_size

# Run mean reversion strategy
async def run_mean_reversion():
    print("📊 Mean Reversion Paper Trading")
    print("💡 Strategy: Buy low, sell high based on statistical analysis")
    print("⚠️  Works best in ranging markets, less effective in strong trends")
    
    trader = MeanReversionTrader(initial_balance=10000, leverage=1.5)
    await trader.mean_reversion_simulation(duration=600)  # 10 minutes

if __name__ == "__main__":
    asyncio.run(run_mean_reversion())
```

Risk Management for Paper Trading
--------------------------------

**Position Sizing with Leverage**:
```python
def calculate_safe_position_size(balance, leverage, current_price):
    """Calculate position size respecting 1% rule"""
    
    # 1% of account balance at risk
    max_risk_amount = balance * 0.01
    
    # Position size with leverage
    max_position_value = balance * leverage
    position_size = min(
        max_position_value / current_price,
        max_risk_amount / current_price
    )
    
    return position_size

# Examples
balance = 1000
price = 50000

for leverage in [1, 2, 5, 10]:
    size = calculate_safe_position_size(balance, leverage, price)
    position_value = size * price
    margin_required = position_value / leverage
    
    print(f"{leverage}x: {size:.6f} BTC = ${position_value:.2f} position, ${margin_required:.2f} margin")
```

**Leverage Risk Analysis**:
```python
def analyze_leverage_risk(initial_balance, leverage_levels):
    """Analyze risk at different leverage levels"""
    
    print("🛡️ Leverage Risk Analysis")
    print("=" * 50)
    
    for leverage in leverage_levels:
        max_position = initial_balance * leverage
        margin_requirement = initial_balance
        liquidation_move = 1.0 / leverage  # Price move to liquidate
        
        print(f"\n{leverage}x Leverage:")
        print(f"  Max Position: ${max_position:,.2f}")
        print(f"  Margin Required: ${margin_requirement:,.2f}")
        print(f"  Liquidation at: {liquidation_move*100:.1f}% move")
        print(f"  Risk Level: {'⚠️ High' if leverage > 3 else '🟡 Medium' if leverage > 1 else '🟢 Low'}")

# Usage
analyze_leverage_risk(10000, [1, 2, 5, 10])
```

**Paper Trading Best Practices**:

1. **Start with 1x leverage** before increasing
2. **Use 1% rule** for position sizing
3. **Track performance metrics** (win rate, avg win/loss)
4. **Test different market conditions** (trending, ranging, volatile)
5. **Practice risk management** (stop losses, position limits)
6. **Keep detailed records** of all trades and decisions
7. **Review and refine** strategies regularly

**Performance Metrics to Track**:

```python
def analyze_paper_trading_performance(trades):
    """Analyze paper trading performance"""
    
    if not trades:
        print("No trades to analyze")
        return
    
    # Basic metrics
    total_trades = len(trades)
    winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
    losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
    
    win_rate = len(winning_trades) / total_trades * 100
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    
    # Advanced metrics
    avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    max_drawdown = calculate_max_drawdown(trades)
    sharpe_ratio = calculate_sharpe_ratio(trades)
    
    print(f"📊 Performance Analysis")
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Total PnL: ${total_pnl:.2f}")
    print(f"Avg Win: ${avg_win:.2f}")
    print(f"Avg Loss: ${avg_loss:.2f}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

def calculate_max_drawdown(trades):
    """Calculate maximum drawdown from trades"""
    # Implementation for drawdown calculation
    pass

def calculate_sharpe_ratio(trades):
    """Calculate Sharpe ratio for risk-adjusted returns"""
    # Implementation for Sharpe ratio calculation
    pass
```

Remember: **Paper trading builds skills and confidence, but real trading involves emotional pressures not present in simulation. Always start with small position sizes when moving to real money!** 🛡️