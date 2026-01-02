"""Tests for blockchain_monitor module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import json

from pyautokit.blockchain_monitor import BlockchainMonitor, main


@pytest.fixture
def monitor():
    """Create BlockchainMonitor instance."""
    return BlockchainMonitor()


@pytest.fixture
def mock_price_response():
    """Mock CoinGecko price API response."""
    return {
        "elrond-erd-2": {
            "usd": 45.67,
            "usd_market_cap": 1234567890,
            "usd_24h_vol": 98765432,
            "usd_24h_change": 5.23,
        }
    }


@pytest.fixture
def mock_trending_response():
    """Mock trending coins API response."""
    return {
        "coins": [
            {
                "item": {
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "market_cap_rank": 1,
                }
            },
            {
                "item": {
                    "name": "Ethereum",
                    "symbol": "ETH",
                    "market_cap_rank": 2,
                }
            },
        ]
    }


@pytest.fixture
def mock_historical_response():
    """Mock historical data API response."""
    return {
        "prices": [
            [1609459200000, 40.5],
            [1609545600000, 41.2],
            [1609632000000, 42.1],
        ],
        "market_caps": [
            [1609459200000, 1000000000],
            [1609545600000, 1100000000],
            [1609632000000, 1200000000],
        ],
        "total_volumes": [
            [1609459200000, 50000000],
            [1609545600000, 55000000],
            [1609632000000, 60000000],
        ],
    }


class TestBlockchainMonitor:
    """Test BlockchainMonitor class."""

    def test_init(self, monitor):
        """Test monitor initialization."""
        assert monitor is not None
        assert monitor.client is not None
        assert "EGLD" in monitor.COIN_IDS
        assert "BTC" in monitor.COIN_IDS
        assert "ETH" in monitor.COIN_IDS

    def test_coin_ids_mapping(self, monitor):
        """Test coin ID mappings."""
        assert monitor.COIN_IDS["EGLD"] == "elrond-erd-2"
        assert monitor.COIN_IDS["BTC"] == "bitcoin"
        assert monitor.COIN_IDS["ETH"] == "ethereum"
        assert monitor.COIN_IDS["BNB"] == "binancecoin"
        assert monitor.COIN_IDS["SOL"] == "solana"

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_price_success(self, mock_get, monitor, mock_price_response):
        """Test successful price retrieval."""
        mock_get.return_value = mock_price_response

        result = monitor.get_price("EGLD")

        assert result is not None
        assert result["coin"] == "EGLD"
        assert result["price"] == 45.67
        assert result["market_cap"] == 1234567890
        assert result["volume_24h"] == 98765432
        assert result["change_24h"] == 5.23
        assert "timestamp" in result

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_price_unknown_coin(self, mock_get, monitor):
        """Test price retrieval with unknown coin."""
        result = monitor.get_price("UNKNOWN")

        assert result is None
        mock_get.assert_not_called()

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_price_api_failure(self, mock_get, monitor):
        """Test price retrieval when API fails."""
        mock_get.return_value = None

        result = monitor.get_price("EGLD")

        assert result is None

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_price_case_insensitive(self, mock_get, monitor, mock_price_response):
        """Test price retrieval is case insensitive."""
        mock_get.return_value = mock_price_response

        result1 = monitor.get_price("egld")
        result2 = monitor.get_price("EGLD")
        result3 = monitor.get_price("Egld")

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        assert result1["coin"] == "EGLD"
        assert result2["coin"] == "EGLD"
        assert result3["coin"] == "EGLD"

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    @patch("time.sleep")
    def test_get_multiple_prices(self, mock_sleep, mock_get, monitor, mock_price_response):
        """Test multiple price retrieval."""
        mock_get.return_value = mock_price_response

        coins = ["EGLD", "BTC", "ETH"]
        results = monitor.get_multiple_prices(coins)

        assert len(results) == 3
        assert all(r["coin"] in coins for r in results)
        # Should sleep between requests for rate limiting
        assert mock_sleep.call_count == 3

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    @patch("time.sleep")
    def test_get_multiple_prices_with_failures(self, mock_sleep, mock_get, monitor):
        """Test multiple prices with some failures."""
        # First call succeeds, second fails, third succeeds
        mock_get.side_effect = [
            {"elrond-erd-2": {"usd": 45.67, "usd_24h_change": 5.23}},
            None,
            {"ethereum": {"usd": 3000, "usd_24h_change": 2.5}},
        ]

        coins = ["EGLD", "BTC", "ETH"]
        results = monitor.get_multiple_prices(coins)

        # Only 2 results (BTC failed)
        assert len(results) == 2
        assert results[0]["coin"] == "EGLD"
        assert results[1]["coin"] == "ETH"

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_historical_data_success(self, mock_get, monitor, mock_historical_response):
        """Test successful historical data retrieval."""
        mock_get.return_value = mock_historical_response

        result = monitor.get_historical_data("EGLD", days=7)

        assert result is not None
        assert result["coin"] == "EGLD"
        assert result["days"] == 7
        assert len(result["prices"]) == 3
        assert len(result["market_caps"]) == 3
        assert len(result["total_volumes"]) == 3

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_historical_data_unknown_coin(self, mock_get, monitor):
        """Test historical data with unknown coin."""
        result = monitor.get_historical_data("UNKNOWN", days=7)

        assert result is None
        mock_get.assert_not_called()

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_historical_data_api_failure(self, mock_get, monitor):
        """Test historical data when API fails."""
        mock_get.return_value = None

        result = monitor.get_historical_data("EGLD", days=7)

        assert result is None

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_trending_coins_success(self, mock_get, monitor, mock_trending_response):
        """Test successful trending coins retrieval."""
        mock_get.return_value = mock_trending_response

        result = monitor.get_trending_coins()

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Bitcoin"
        assert result[0]["symbol"] == "BTC"
        assert result[0]["market_cap_rank"] == 1
        assert result[1]["name"] == "Ethereum"

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_trending_coins_api_failure(self, mock_get, monitor):
        """Test trending coins when API fails."""
        mock_get.return_value = None

        result = monitor.get_trending_coins()

        assert result is None

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    def test_get_trending_coins_empty_response(self, mock_get, monitor):
        """Test trending coins with empty response."""
        mock_get.return_value = {"coins": []}

        result = monitor.get_trending_coins()

        assert result is not None
        assert len(result) == 0

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    @patch("time.sleep")
    def test_monitor_price_keyboard_interrupt(self, mock_sleep, mock_get, monitor, mock_price_response):
        """Test monitor price stops on keyboard interrupt."""
        mock_get.return_value = mock_price_response
        mock_sleep.side_effect = KeyboardInterrupt()

        # Should not raise exception, just stop
        monitor.monitor_price("EGLD", interval=1)

        assert mock_get.called

    @patch("pyautokit.blockchain_monitor.APIClient.get")
    @patch("time.sleep")
    def test_monitor_price_with_alert(self, mock_sleep, mock_get, monitor):
        """Test monitor price with alert threshold."""
        # Return high change to trigger alert
        mock_get.return_value = {
            "elrond-erd-2": {
                "usd": 45.67,
                "usd_24h_change": 10.5,  # Above 5% threshold
            }
        }
        mock_sleep.side_effect = KeyboardInterrupt()

        with patch("pyautokit.blockchain_monitor.logger") as mock_logger:
            monitor.monitor_price("EGLD", interval=1, alert_threshold=5.0)

            # Should log warning for high change
            assert any(
                "ALERT" in str(call) for call in mock_logger.warning.call_args_list
            )


class TestCLI:
    """Test CLI functionality."""

    @patch("pyautokit.blockchain_monitor.BlockchainMonitor.get_price")
    @patch("sys.argv", ["blockchain_monitor", "--coin", "EGLD"])
    def test_cli_get_price(self, mock_get_price, capsys):
        """Test CLI price retrieval."""
        mock_get_price.return_value = {
            "coin": "EGLD",
            "price": 45.67,
            "change_24h": 5.23,
            "market_cap": 1234567890,
        }

        main()

        captured = capsys.readouterr()
        assert "EGLD" in captured.out
        assert "45.67" in captured.out
        assert "5.23%" in captured.out

    @patch("pyautokit.blockchain_monitor.BlockchainMonitor.get_trending_coins")
    @patch("sys.argv", ["blockchain_monitor", "--trending"])
    def test_cli_trending(self, mock_trending, capsys):
        """Test CLI trending coins."""
        mock_trending.return_value = [
            {"name": "Bitcoin", "symbol": "BTC", "market_cap_rank": 1},
            {"name": "Ethereum", "symbol": "ETH", "market_cap_rank": 2},
        ]

        main()

        captured = capsys.readouterr()
        assert "Bitcoin" in captured.out
        assert "Ethereum" in captured.out

    @patch("pyautokit.blockchain_monitor.BlockchainMonitor.get_historical_data")
    @patch("sys.argv", ["blockchain_monitor", "--coin", "EGLD", "--history", "7"])
    def test_cli_historical(self, mock_history, capsys):
        """Test CLI historical data."""
        mock_history.return_value = {
            "coin": "EGLD",
            "days": 7,
            "prices": [[1609459200000, 40.5], [1609545600000, 41.2]],
        }

        main()

        captured = capsys.readouterr()
        assert "2 price points" in captured.out

    @patch("pyautokit.blockchain_monitor.BlockchainMonitor.monitor_price")
    @patch("sys.argv", ["blockchain_monitor", "--coin", "EGLD", "--monitor", "--interval", "60"])
    def test_cli_monitor(self, mock_monitor):
        """Test CLI monitoring mode."""
        main()

        mock_monitor.assert_called_once()
        args = mock_monitor.call_args[0]
        assert args[0] == "EGLD"
        assert args[1] == 60

    @patch("pyautokit.blockchain_monitor.BlockchainMonitor.get_price")
    @patch("pyautokit.blockchain_monitor.save_json")
    @patch("sys.argv", ["blockchain_monitor", "--coin", "EGLD", "--output", "price.json"])
    def test_cli_output_file(self, mock_save, mock_get_price):
        """Test CLI with output file."""
        mock_get_price.return_value = {
            "coin": "EGLD",
            "price": 45.67,
            "change_24h": 5.23,
            "market_cap": 1234567890,
        }

        main()

        mock_save.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
