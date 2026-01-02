#!/usr/bin/env python3
"""Example: Monitor EGLD price with alerts."""

from pyautokit.blockchain_monitor import BlockchainMonitor
from pyautokit.logger import setup_logger

logger = setup_logger("MonitorEGLD")


def main():
    """Monitor EGLD and other crypto prices."""
    monitor = BlockchainMonitor()
    
    # Get current prices for multiple coins
    coins = ["EGLD", "BTC", "ETH", "BNB"]
    
    logger.info("Fetching current prices...")
    prices = monitor.get_multiple_prices(coins)
    
    print("\n=== Current Crypto Prices ===")
    for price_data in prices:
        coin = price_data['coin']
        price = price_data['price']
        change = price_data['change_24h']
        
        change_symbol = "📈" if change > 0 else "📉"
        print(f"{coin:5} ${price:10,.2f}  {change_symbol} {change:+.2f}%")
    
    # Get trending coins
    print("\n=== Trending Coins ===")
    trending = monitor.get_trending_coins()
    if trending:
        for coin in trending[:5]:
            print(f"#{coin['market_cap_rank']:3} {coin['name']:20} ({coin['symbol']})")
    
    # Optional: Start continuous monitoring
    # Uncomment to enable:
    # logger.info("\nStarting continuous monitoring (Ctrl+C to stop)")
    # monitor.monitor_price("EGLD", interval=60, alert_threshold=5.0)


if __name__ == "__main__":
    main()
