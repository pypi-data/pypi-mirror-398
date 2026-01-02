"""Blockchain price monitoring for EGLD and other cryptocurrencies."""

import argparse
import time
from typing import Dict, List, Optional
from datetime import datetime
from .logger import setup_logger
from .config import Config
from .api_client import APIClient
from .utils import save_json

logger = setup_logger("BlockchainMonitor", level=Config.LOG_LEVEL)


class BlockchainMonitor:
    """Monitor cryptocurrency prices and blockchain data."""

    # CoinGecko coin IDs
    COIN_IDS = {
        "EGLD": "elrond-erd-2",
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
    }

    def __init__(self, api_url: str = Config.EGLD_PRICE_API):
        """Initialize blockchain monitor.
        
        Args:
            api_url: CoinGecko API base URL
        """
        self.client = APIClient(base_url=api_url)

    def get_price(
        self,
        coin: str,
        vs_currency: str = "usd"
    ) -> Optional[Dict]:
        """Get current price for coin.
        
        Args:
            coin: Coin symbol (EGLD, BTC, ETH, etc.)
            vs_currency: Fiat currency (usd, eur, etc.)
            
        Returns:
            Price data dict or None
        """
        coin_id = self.COIN_IDS.get(coin.upper())
        if not coin_id:
            logger.error(f"Unknown coin: {coin}")
            return None
        
        endpoint = f"/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": vs_currency,
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
        }
        
        data = self.client.get(endpoint, params=params)
        
        if data and coin_id in data:
            result = {
                "coin": coin.upper(),
                "timestamp": datetime.now().isoformat(),
                "price": data[coin_id].get(vs_currency),
                "market_cap": data[coin_id].get(f"{vs_currency}_market_cap"),
                "volume_24h": data[coin_id].get(f"{vs_currency}_24h_vol"),
                "change_24h": data[coin_id].get(f"{vs_currency}_24h_change"),
            }
            logger.info(f"{coin.upper()}: ${result['price']} ({result['change_24h']:.2f}%)")
            return result
        
        return None

    def get_multiple_prices(
        self,
        coins: List[str],
        vs_currency: str = "usd"
    ) -> List[Dict]:
        """Get prices for multiple coins.
        
        Args:
            coins: List of coin symbols
            vs_currency: Fiat currency
            
        Returns:
            List of price data dicts
        """
        results = []
        for coin in coins:
            price_data = self.get_price(coin, vs_currency)
            if price_data:
                results.append(price_data)
            time.sleep(1)  # Rate limiting
        return results

    def get_historical_data(
        self,
        coin: str,
        days: int = 7,
        vs_currency: str = "usd"
    ) -> Optional[Dict]:
        """Get historical price data.
        
        Args:
            coin: Coin symbol
            days: Number of days of history
            vs_currency: Fiat currency
            
        Returns:
            Historical data dict or None
        """
        coin_id = self.COIN_IDS.get(coin.upper())
        if not coin_id:
            logger.error(f"Unknown coin: {coin}")
            return None
        
        endpoint = f"/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days,
        }
        
        data = self.client.get(endpoint, params=params)
        
        if data:
            logger.info(f"Retrieved {days} days of data for {coin.upper()}")
            return {
                "coin": coin.upper(),
                "days": days,
                "prices": data.get("prices", []),
                "market_caps": data.get("market_caps", []),
                "total_volumes": data.get("total_volumes", []),
            }
        
        return None

    def monitor_price(
        self,
        coin: str,
        interval: int = Config.BLOCKCHAIN_MONITOR_INTERVAL,
        alert_threshold: Optional[float] = None
    ) -> None:
        """Monitor price with periodic updates.
        
        Args:
            coin: Coin symbol to monitor
            interval: Check interval in seconds
            alert_threshold: Alert if change exceeds threshold %
        """
        logger.info(f"Monitoring {coin.upper()} every {interval}s")
        
        try:
            while True:
                price_data = self.get_price(coin)
                
                if price_data and alert_threshold:
                    change = price_data.get("change_24h", 0)
                    if abs(change) >= alert_threshold:
                        logger.warning(
                            f"ALERT: {coin.upper()} changed {change:.2f}% in 24h!"
                        )
                
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped")

    def get_trending_coins(self) -> Optional[List[Dict]]:
        """Get trending coins.
        
        Returns:
            List of trending coin dicts
        """
        endpoint = "/search/trending"
        data = self.client.get(endpoint)
        
        if data and "coins" in data:
            trending = [
                {
                    "name": coin["item"]["name"],
                    "symbol": coin["item"]["symbol"],
                    "market_cap_rank": coin["item"]["market_cap_rank"],
                }
                for coin in data["coins"]
            ]
            logger.info(f"Retrieved {len(trending)} trending coins")
            return trending
        
        return None


def main() -> None:
    """CLI for blockchain monitor."""
    parser = argparse.ArgumentParser(description="Blockchain monitoring utility")
    parser.add_argument(
        "--coin",
        default="EGLD",
        help="Coin symbol (EGLD, BTC, ETH, etc.)"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Continuous monitoring mode"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=Config.BLOCKCHAIN_MONITOR_INTERVAL,
        help="Monitoring interval in seconds"
    )
    parser.add_argument(
        "--alert",
        type=float,
        help="Alert threshold for 24h change %"
    )
    parser.add_argument(
        "--history",
        type=int,
        help="Get historical data for N days"
    )
    parser.add_argument(
        "--trending",
        action="store_true",
        help="Show trending coins"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save output to JSON file"
    )
    
    args = parser.parse_args()
    monitor = BlockchainMonitor()
    
    if args.trending:
        trending = monitor.get_trending_coins()
        if trending:
            for coin in trending:
                print(f"#{coin['market_cap_rank']} {coin['name']} ({coin['symbol']})")
            if args.output:
                save_json(trending, Config.DATA_DIR / args.output)
    
    elif args.history:
        data = monitor.get_historical_data(args.coin, args.history)
        if data:
            print(f"Retrieved {len(data['prices'])} price points")
            if args.output:
                save_json(data, Config.DATA_DIR / args.output)
    
    elif args.monitor:
        monitor.monitor_price(args.coin, args.interval, args.alert)
    
    else:
        price_data = monitor.get_price(args.coin)
        if price_data:
            print(f"{price_data['coin']}: ${price_data['price']}")
            print(f"24h Change: {price_data['change_24h']:.2f}%")
            print(f"Market Cap: ${price_data['market_cap']:,.0f}")
            if args.output:
                save_json(price_data, Config.DATA_DIR / args.output)


if __name__ == "__main__":
    main()