#!/usr/bin/env python3
"""
Paper Trading Demo Script for Weex Client

This script demonstrates safe paper trading with comprehensive risk management.

Usage:
    python examples/paper_trading_demo.py [strategy] [duration]

Strategies:
    market_making   - Market making with bid-ask spread
    trend_following - Trend following with moving averages

Examples:
    python examples/paper_trading_demo.py market_making 300
    python examples/paper_trading_demo.py trend_following 600
"""

from __future__ import annotations

import asyncio
import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path for local development
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent))

# Import Weex Client components
try:
    from weex_client import WeexAsyncClient
    from weex_client.config import load_config

    print("✅ Weex Client imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure you're running from the project root")
    sys.exit(1)


class PaperTrader:
    """Simplified paper trading engine with safety validation"""

    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trades = []
        self.trade_id = 0
        self.commission_rate = 0.001  # 0.1% commission

        # Safety parameters
        self.max_risk_per_trade = 0.01  # 1% rule

    def validate_parameters(self) -> bool:
        """Validate trading parameters for safety"""

        print("🛡️ Safety Validation:")

        # Check balance
        if self.initial_balance <= 0:
            print("❌ Initial balance must be positive")
            return False

        print(f"✅ Initial balance: ${self.initial_balance:.2f}")

        # Calculate risk metrics
        max_risk_amount = self.initial_balance * self.max_risk_per_trade
        print(f"✅ Max risk per trade: ${max_risk_amount:.2f} (1% rule)")

        return True

    def calculate_safe_position_size(self, current_price: float) -> float:
        """Calculate position size following 1% rule"""

        # Calculate 1% risk amount
        risk_amount = self.balance * self.max_risk_per_trade
        position_size = risk_amount / current_price

        return position_size

    def calculate_commission(self, value: float) -> float:
        """Calculate trading commission"""

        return value * self.commission_rate

    def update_performance_metrics(self, current_time: float) -> dict:
        """Update performance metrics"""

        # Track peak balance
        peak_balance = max(self.initial_balance, self.balance)

        # Calculate current drawdown
        current_drawdown = (
            (peak_balance - self.balance) / peak_balance if peak_balance > 0 else 0
        )

        # Update portfolio value
        portfolio_value = self.balance  # Simplified for demo

        total_return = (portfolio_value - self.initial_balance) / self.initial_balance

        return {
            "current_balance": self.balance,
            "portfolio_value": portfolio_value,
            "total_return": total_return * 100,  # Convert to percentage
            "time_elapsed": current_time - self.start_time if self.start_time else 0,
        }

    def get_performance_summary(self) -> dict:
        """Get comprehensive performance summary"""

        if not self.trades:
            return {"message": "No trades executed"}

        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in self.trades if t.get("pnl", 0) < 0]

        if total_trades > 0:
            win_rate = len(winning_trades) / total_trades * 100
            total_pnl = sum(t.get("pnl", 0) for t in self.trades)
            total_commission = sum(t.get("commission", 0) for t in self.trades)
        else:
            win_rate = 0
            total_pnl = 0
            total_commission = 0

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_commission": total_commission,
            "net_pnl": total_pnl - total_commission,
            "current_balance": self.balance,
            "initial_balance": self.initial_balance,
            "return_pct": ((self.balance - self.initial_balance) / self.initial_balance)
            * 100,
        }

    def show_final_summary(self):
        """Display final trading summary"""

        print("\n" + "=" * 70)
        print("📊 PAPER TRADING SUMMARY")
        print("=" * 70)

        summary = self.get_performance_summary()

        if "message" in summary:
            print(summary["message"])
            return

        print(f"📊 Total Trades: {summary['total_trades']}")
        print(f"🎯 Win Rate: {summary['win_rate']:.1f}%")
        print(f"📈 Net PnL: ${summary['net_pnl']:.2f}")
        print(f"💰 Total Return: {summary['return_pct']:+.2f}%")
        print(f"💸 Total Commission: ${summary['total_commission']:.2f}")
        print(f"📉 Max Drawdown: N/A (simplified)")
        print(f"💰 Final Balance: ${summary['current_balance']:.2f}")
        print(f"💵 Initial Balance: ${summary['initial_balance']:.2f}")


class MarketMakingStrategy(PaperTrader):
    """Market making paper trading strategy"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.spread_pct = 0.001  # 0.1% spread

    async def run(self, symbol: str = "BTCUSDT", duration: int = 300):
        """Run market making simulation"""

        print(f"\n🏪 Market Making Strategy")
        print(f"📊 Spread: {self.spread_pct * 100:.2f}%")

        config = load_config()

        try:
            async with WeexAsyncClient(config) as client:
                print(f"🎯 Starting market making for {symbol} ({duration}s)...")
                self.start_time = time.time()

                while time.time() - self.start_time < duration:
                    try:
                        # Get real market data
                        ticker_data = await client.get_ticker(symbol)
                        order_book_data = await client.get_order_book(symbol, limit=1)

                        # Simple data access
                        if hasattr(ticker_data, "data") and ticker_data.data:
                            ticker_dict = (
                                ticker_data.data
                                if isinstance(ticker_data.data, dict)
                                else {}
                            )
                            current_price = float(ticker_dict.get("last", 0))
                        else:
                            current_price = 50000.0  # Mock price if no data

                        if hasattr(order_book_data, "data") and order_book_data.data:
                            order_dict = (
                                order_book_data.data
                                if isinstance(order_book_data.data, dict)
                                else {}
                            )
                            bids = order_dict.get("bids", [])
                            asks = order_dict.get("asks", [])
                        else:
                            bids = []
                            asks = []

                        if bids and len(bids) > 0:
                            best_bid = float(bids[0][0])
                        else:
                            best_bid = current_price * 0.999

                        if asks and len(asks) > 0:
                            best_ask = float(asks[0][0])
                        else:
                            best_ask = current_price * 1.001

                        # Calculate our quotes
                        our_bid = best_bid * (1 - self.spread_pct)
                        our_ask = best_ask * (1 + self.spread_pct)

                        # Calculate position sizes with 1% rule
                        bid_size = self.calculate_safe_position_size(our_bid)
                        ask_size = self.calculate_safe_position_size(our_ask)

                        # Simulate fills (simplified)
                        if current_price <= our_bid:
                            await self.execute_paper_buy(
                                symbol, our_bid, bid_size, current_price
                            )
                        elif current_price >= our_ask:
                            await self.execute_paper_sell(
                                symbol, our_ask, ask_size, current_price
                            )

                        # Show status
                        metrics = self.update_performance_metrics(time.time())

                        print(
                            f"📊 Price: ${current_price:.2f} | Bid: ${our_bid:.2f} | Ask: ${our_ask:.2f}"
                        )
                        print(f"📏 Sizes: {bid_size:.6f} | {ask_size:.6f}")
                        print(f"💼 Portfolio: ${metrics['portfolio_value']:.2f}")
                        print(f"📈 Return: {metrics['total_return']:+.2f}%")
                        print("-" * 60)

                        await asyncio.sleep(10)  # Update every 10 seconds

                    except Exception as e:
                        print(f"❌ Market making error: {e}")
                        await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ Market making failed: {e}")

        # Show final summary
        self.show_final_summary()

    async def execute_paper_buy(
        self, symbol: str, price: float, size: float, current_price: float
    ):
        """Execute paper buy order"""

        commission = self.calculate_commission(size * price)
        cost = size * price + commission

        if self.balance >= cost:
            self.balance -= cost

            self.trade_id += 1
            self.trades.append(
                {
                    "id": self.trade_id,
                    "type": "buy",
                    "symbol": symbol,
                    "price": price,
                    "size": size,
                    "commission": commission,
                    "timestamp": time.time(),
                }
            )

            print(f"🟢 PAPER BUY: {size:.6f} {symbol} @ ${price:.2f}")

    async def execute_paper_sell(
        self, symbol: str, price: float, size: float, current_price: float
    ):
        """Execute paper sell order"""

        commission = self.calculate_commission(size * price)
        revenue = size * price - commission

        self.balance += revenue

        # Calculate realized PnL
        pnl = (price - current_price) * size - commission  # Simplified

        self.trade_id += 1
        self.trades.append(
            {
                "id": self.trade_id,
                "type": "sell",
                "symbol": symbol,
                "price": price,
                "size": size,
                "commission": commission,
                "pnl": pnl,
                "timestamp": time.time(),
            }
        )

        print(f"🔴 PAPER SELL: {size:.6f} {symbol} @ ${price:.2f} | PnL: ${pnl:.2f}")


class TrendFollowingStrategy(PaperTrader):
    """Trend following paper trading strategy"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.short_ma = 10
        self.long_ma = 30
        self.stop_loss_pct = 0.02  # 2% stop loss
        self.take_profit_pct = 0.06  # 6% take profit

    async def run(self, symbol: str = "BTCUSDT", duration: int = 600):
        """Run trend following simulation"""

        print(f"\n📈 Trend Following Strategy")
        print(f"📊 Moving Averages: {self.short_ma}/{self.long_ma}")
        print(
            f"🛡️ Stop Loss: {self.stop_loss_pct * 100:.1f}% | Take Profit: {self.take_profit_pct * 100:.1f}%"
        )

        config = load_config()
        price_history = []
        position = None
        entry_price = None
        stop_loss = None
        take_profit = None

        try:
            async with WeexAsyncClient(config) as client:
                print(f"🎯 Starting trend following for {symbol} ({duration}s)...")
                self.start_time = time.time()

                # Collect initial data
                print("📊 Collecting initial market data...")
                for _ in range(self.long_ma + 10):
                    try:
                        ticker_data = await client.get_ticker(symbol)
                        if hasattr(ticker_data, "data") and ticker_data.data:
                            ticker_dict = (
                                ticker_data.data
                                if isinstance(ticker_data.data, dict)
                                else {}
                            )
                            price = float(ticker_dict.get("last", 0))
                            price_history.append(price)
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"⚠️ Data collection error: {e}")
                        await asyncio.sleep(1)

                print("✅ Initial data collected, starting strategy...")

                start_time = time.time()

                while time.time() - start_time < duration:
                    try:
                        # Get latest price
                        ticker_data = await client.get_ticker(symbol)
                        if hasattr(ticker_data, "data") and ticker_data.data:
                            ticker_dict = (
                                ticker_data.data
                                if isinstance(ticker_data.data, dict)
                                else {}
                            )
                            current_price = float(ticker_dict.get("last", 0))
                            price_history.append(current_price)
                        else:
                            current_price = (
                                price_history[-1] if price_history else 50000.0
                            )

                        if len(price_history) > self.long_ma + 10:
                            price_history.pop(0)

                        # Calculate moving averages
                        short_ma_value = (
                            sum(price_history[-self.short_ma :]) / self.short_ma
                        )
                        long_ma_value = (
                            sum(price_history[-self.long_ma :]) / self.long_ma
                        )

                        # Generate signals
                        if short_ma_value > long_ma_value and position != "long":
                            signal = "buy"
                        elif short_ma_value < long_ma_value and position != "short":
                            signal = "sell"
                        else:
                            signal = "hold"

                        # Check stop loss and take profit
                        if position == "long":
                            if current_price <= stop_loss:
                                print(f"🛡️ STOP LOSS triggered at ${current_price:.2f}")
                                await self.close_position(
                                    symbol, current_price, "stop_loss"
                                )
                                position = None
                                entry_price = None
                                stop_loss = None
                                take_profit = None
                            elif current_price >= take_profit:
                                print(
                                    f"🎯 TAKE PROFIT triggered at ${current_price:.2f}"
                                )
                                await self.close_position(
                                    symbol, current_price, "take_profit"
                                )
                                position = None
                                entry_price = None
                                stop_loss = None
                                take_profit = None

                        # Execute new positions
                        if signal == "buy" and position != "long":
                            position_size = self.calculate_safe_position_size(
                                current_price
                            )
                            if position_size > 0:
                                await self.open_position(
                                    symbol, current_price, position_size, "long"
                                )
                                position = "long"
                                entry_price = current_price
                                stop_loss = current_price * (1 - self.stop_loss_pct)
                                take_profit = current_price * (1 + self.take_profit_pct)
                                print(
                                    f"🟢 LONG: {position_size:.6f} @ ${current_price:.2f}"
                                )

                        # Show status
                        metrics = self.update_performance_metrics(time.time())

                        print(
                            f"📊 Price: ${current_price:.2f} | Short MA: ${short_ma_value:.2f} | Long MA: ${long_ma_value:.2f}"
                        )
                        print(
                            f"📈 Signal: {signal.upper()} | Position: {position or 'none'}"
                        )
                        print(f"💼 Portfolio: ${metrics['portfolio_value']:.2f}")
                        print(f"📈 Return: {metrics['total_return']:+.2f}%")
                        print("-" * 70)

                        await asyncio.sleep(5)  # Check every 5 seconds

                    except Exception as e:
                        print(f"❌ Trend following error: {e}")
                        await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ Trend following failed: {e}")

        # Show final summary
        self.show_final_summary()

    async def open_position(
        self, symbol: str, price: float, size: float, direction: str
    ):
        """Open leveraged position"""

        commission = self.calculate_commission(size * price)
        total_cost = size * price + commission

        if self.balance >= total_cost:
            self.balance -= total_cost

            self.trade_id += 1
            self.trades.append(
                {
                    "id": self.trade_id,
                    "type": "open",
                    "direction": direction,
                    "symbol": symbol,
                    "price": price,
                    "size": size,
                    "commission": commission,
                    "timestamp": time.time(),
                }
            )

            print(f"🟢 OPEN {direction.upper()}: {size:.6f} {symbol} @ ${price:.2f}")

    async def close_position(self, symbol: str, current_price: float, reason: str):
        """Close position"""

        # Simplified closing logic for demo
        if not self.trades:
            return

        # Find last open position
        open_trades = [t for t in self.trades if t["type"] == "open"]
        if not open_trades:
            return

        last_trade = open_trades[-1]

        commission = self.calculate_commission(last_trade["size"] * current_price)

        # Calculate PnL
        pnl = (current_price - last_trade["price"]) * last_trade["size"] - commission

        self.balance += last_trade["size"] * last_trade["price"] + pnl

        self.trade_id += 1
        self.trades.append(
            {
                "id": self.trade_id,
                "type": "close",
                "symbol": symbol,
                "entry_price": last_trade["price"],
                "close_price": current_price,
                "size": last_trade["size"],
                "pnl": pnl,
                "commission": commission,
                "reason": reason,
                "timestamp": time.time(),
            }
        )

        print(f"✅ Position closed: {last_trade['size']:.6f} @ ${current_price:.2f}")
        print(f"📊 PnL: ${pnl:.2f} | Reason: {reason}")


def show_banner():
    """Display welcome banner"""

    print("🎯" + "=" * 70)
    print("🎯     PAPER TRADING DEMO - Weex Client")
    print("🎯" + "=" * 70)
    print("🛡️  Safety Features:")
    print("   • 1% balance rule (never risk more than 1% per trade)")
    print("   • Comprehensive risk management")
    print("   • Real-time performance tracking")
    print("   • Paper trading only (NO real money)")
    print("=" * 74)


async def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description="Paper Trading Demo with Safety Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s market_making 300    # 5-minute market making
  %(prog)s trend_following 600  # 10-minute trend following
  %(prog)s --help                  # Show this help message
        """,
    )

    parser.add_argument(
        "strategy",
        choices=["market_making", "trend_following"],
        help="Trading strategy to run",
    )

    parser.add_argument(
        "duration",
        type=int,
        nargs="?",
        default=300,
        help="Duration in seconds (default: 300)",
    )

    parser.add_argument(
        "--balance",
        type=float,
        default=10000.0,
        help="Initial balance in USD (default: 10000.0)",
    )

    args = parser.parse_args()

    # Show banner
    show_banner()

    # Validate arguments
    if args.duration <= 0:
        print("❌ Duration must be positive")
        return

    if args.balance <= 0:
        print("❌ Balance must be positive")
        return

    # Create strategy instance
    try:
        if args.strategy == "market_making":
            strategy = MarketMakingStrategy(initial_balance=args.balance)
        elif args.strategy == "trend_following":
            strategy = TrendFollowingStrategy(initial_balance=args.balance)
        else:
            print(f"❌ Unknown strategy: {args.strategy}")
            return

        # Validate safety parameters
        if not strategy.validate_parameters():
            print("❌ Safety validation failed")
            return

        # Run strategy
        print(f"\n🚀 Starting {args.strategy.replace('_', ' ').title()} Strategy...")
        print(f"⏱️  Duration: {args.duration} seconds")
        print(f"💰 Initial Balance: ${args.balance:.2f}")
        print("=" * 50)

        await strategy.run(duration=args.duration)

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Demo failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
