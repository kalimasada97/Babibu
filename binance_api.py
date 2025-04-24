import os
import logging
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define timeframe interval constants for demo
class DemoIntervals:
    KLINE_INTERVAL_1MINUTE = '1m'
    KLINE_INTERVAL_5MINUTE = '5m'
    KLINE_INTERVAL_15MINUTE = '15m'
    KLINE_INTERVAL_30MINUTE = '30m'
    KLINE_INTERVAL_1HOUR = '1h'
    KLINE_INTERVAL_2HOUR = '2h'
    KLINE_INTERVAL_4HOUR = '4h'
    KLINE_INTERVAL_6HOUR = '6h'
    KLINE_INTERVAL_12HOUR = '12h'
    KLINE_INTERVAL_1DAY = '1d'
    KLINE_INTERVAL_3DAY = '3d'
    KLINE_INTERVAL_1WEEK = '1w'

class BinanceAPI:
    def __init__(self):
        # Get API keys from environment
        self.api_key = os.environ.get("BINANCE_API_KEY", "K4imTSPtLipPhOEQP1BXKCSmshiEldyMhZtHxxP4fGqEHsSeskglltZqE9DGE44g")
        self.api_secret = os.environ.get("BINANCE_API_SECRET", "DFWScLQ83OpMCqmtj6pJrs2Z36OdMXzNWudwVimbRR9AJL46X3yHynG7t6traHrf")
        
        # For demo purposes, using simulated methods
        try:
            logger.info("Initializing simulated API client for demo purposes")
            self.client = True
        except Exception as e:
            logger.error(f"Failed to initialize API client: {e}")
            self.client = None
    
    def get_current_price(self, symbol):
        """Get current price and 24h change for a symbol - Simulated for demo"""
        try:
            # Format symbol properly (remove / if present)
            symbol = symbol.replace('/', '')
            
            # Generate random price based on symbol for demo purposes
            if 'BTC' in symbol:
                price = round(random.uniform(50000, 60000), 2)
            elif 'ETH' in symbol:
                price = round(random.uniform(3000, 4000), 2)
            else:
                price = round(random.uniform(1, 1000), 2)
            
            # Generate random 24h change
            change_24h = round(random.uniform(-5, 5), 2)
            
            return {
                'symbol': symbol,
                'price': price,
                'change_24h': change_24h
            }
        
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None
    
    def get_historical_data(self, pair, timeframe='4h', days=90):
        """
        Get simulated historical OHLCV data
        
        Parameters:
        - pair: Trading pair (e.g., 'BTC/USDT')
        - timeframe: Candle interval (e.g., '1h', '4h', '1d')
        - days: Number of days of historical data to fetch
        
        Returns:
        - Pandas DataFrame with OHLCV data
        """
        try:
            # Format pair correctly 
            symbol = pair.replace('/', '')
            
            # Map timeframe to interval
            interval_map = {
                '1m': DemoIntervals.KLINE_INTERVAL_1MINUTE,
                '5m': DemoIntervals.KLINE_INTERVAL_5MINUTE,
                '15m': DemoIntervals.KLINE_INTERVAL_15MINUTE,
                '30m': DemoIntervals.KLINE_INTERVAL_30MINUTE,
                '1h': DemoIntervals.KLINE_INTERVAL_1HOUR,
                '2h': DemoIntervals.KLINE_INTERVAL_2HOUR,
                '4h': DemoIntervals.KLINE_INTERVAL_4HOUR,
                '6h': DemoIntervals.KLINE_INTERVAL_6HOUR,
                '12h': DemoIntervals.KLINE_INTERVAL_12HOUR,
                '1d': DemoIntervals.KLINE_INTERVAL_1DAY,
                '3d': DemoIntervals.KLINE_INTERVAL_3DAY,
                '1w': DemoIntervals.KLINE_INTERVAL_1WEEK,
            }
            
            interval = interval_map.get(timeframe, DemoIntervals.KLINE_INTERVAL_4HOUR)
            
            # For demo purposes, generate simulated price data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Generate timestamps
            if timeframe.endswith('m'):
                # Minutes
                freq = f"{timeframe[:-1]}min"
            elif timeframe.endswith('h'):
                # Hours
                freq = f"{timeframe[:-1]}H"
            elif timeframe.endswith('d'):
                # Days
                freq = f"{timeframe[:-1]}D"
            elif timeframe.endswith('w'):
                # Weeks
                freq = f"{timeframe[:-1]}W"
            else:
                freq = '4H'  # Default
                
            timestamps = pd.date_range(start=start_date, end=end_date, freq=freq)
            
            # Base price and volatility based on pair
            if 'BTC' in symbol:
                base_price = 50000
                volatility = 2000
            elif 'ETH' in symbol:
                base_price = 3000
                volatility = 150
            else:
                base_price = 100
                volatility = 5
            
            # Generate simulated OHLCV data
            data = []
            prev_close = base_price
            
            for timestamp in timestamps:
                # Generate candle data with realistic relationships
                # (open near previous close, high > open and close, low < open and close)
                open_price = prev_close * (1 + random.uniform(-0.005, 0.005))
                change = random.uniform(-0.02, 0.02)
                close = open_price * (1 + change)
                high = max(open_price, close) * (1 + random.uniform(0.001, 0.01))
                low = min(open_price, close) * (1 - random.uniform(0.001, 0.01))
                volume = random.uniform(base_price * 10, base_price * 100)
                
                row = [
                    timestamp,
                    open_price,
                    high,
                    low,
                    close,
                    volume,
                    timestamp,  # close_time
                    volume * close,  # quote_asset_volume
                    random.randint(100, 1000),  # number_of_trades
                    volume * 0.7,  # taker_buy_base_asset_volume
                    volume * close * 0.7,  # taker_buy_quote_asset_volume
                    0  # ignore
                ]
                
                data.append(row)
                prev_close = close
            
            # Create DataFrame
            columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                      'close_time', 'quote_asset_volume', 'number_of_trades',
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
            
            df = pd.DataFrame(data, columns=columns)
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Generated {len(df)} candles for {symbol} {timeframe}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error generating historical data: {e}")
            return None
    
    def get_account_balance(self):
        """Get simulated account balance information"""
        try:
            # Generate simulated balance data
            balances = [
                {'asset': 'BTC', 'free': 0.5, 'locked': 0.1},
                {'asset': 'ETH', 'free': 5.0, 'locked': 0.0},
                {'asset': 'USDT', 'free': 10000.0, 'locked': 5000.0},
                {'asset': 'BNB', 'free': 50.0, 'locked': 10.0},
                {'asset': 'SOL', 'free': 100.0, 'locked': 20.0}
            ]
            
            return balances
            
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return None

    def get_exchange_info(self, symbol=None):
        """Get simulated exchange information about symbols"""
        try:
            # Generate simulated exchange info
            common_info = {
                'timezone': 'UTC',
                'serverTime': int(datetime.now().timestamp() * 1000)
            }
            
            symbols = [
                {'symbol': 'BTCUSDT', 'status': 'TRADING', 'baseAsset': 'BTC', 'quoteAsset': 'USDT'},
                {'symbol': 'ETHUSDT', 'status': 'TRADING', 'baseAsset': 'ETH', 'quoteAsset': 'USDT'},
                {'symbol': 'BNBUSDT', 'status': 'TRADING', 'baseAsset': 'BNB', 'quoteAsset': 'USDT'},
                {'symbol': 'SOLUSDT', 'status': 'TRADING', 'baseAsset': 'SOL', 'quoteAsset': 'USDT'},
                {'symbol': 'ADAUSDT', 'status': 'TRADING', 'baseAsset': 'ADA', 'quoteAsset': 'USDT'}
            ]
            
            if symbol:
                # Return info for specific symbol
                for s in symbols:
                    if s['symbol'] == symbol:
                        return s
                return None
            else:
                # Return all symbols
                return {**common_info, 'symbols': symbols}
            
        except Exception as e:
            logger.error(f"Error getting exchange info: {e}")
            return None
