import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from models import Signal
from app import db
from binance_api import BinanceAPI

class WinrateTracker:
    def __init__(self):
        self.binance_api = BinanceAPI()
        self.logger = logging.getLogger(__name__)
    
    async def log_signal(self, signal):
        """Log a new trading signal to the database"""
        try:
            new_signal = Signal(
                pair=signal['pair'],
                direction=signal['direction'],
                entry=signal['entry'],
                tp1=signal['tp1'],
                tp2=signal.get('tp2'),
                sl=signal['sl'],
                timestamp=datetime.now()
            )
            
            db.session.add(new_signal)
            db.session.commit()
            
            return new_signal.id
        except Exception as e:
            self.logger.error(f"Error logging signal: {e}")
            db.session.rollback()
            raise
    
    async def update_outcome(self, signal_id, closed_price):
        """Update the outcome of a signal after it has been closed"""
        try:
            signal = Signal.query.get(signal_id)
            
            if not signal:
                self.logger.error(f"Signal with ID {signal_id} not found")
                return False
            
            # Determine if WIN or LOSS
            if signal.direction == 'LONG':
                outcome = 'WIN' if closed_price >= signal.tp1 else 'LOSS'
            else:  # SHORT
                outcome = 'WIN' if closed_price <= signal.tp1 else 'LOSS'
            
            # Calculate duration in minutes
            duration_minutes = int((datetime.now() - signal.timestamp).total_seconds() / 60)
            
            # Update signal with outcome
            signal.outcome = outcome
            signal.closed_at = closed_price
            signal.duration = duration_minutes
            
            db.session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating outcome: {e}")
            db.session.rollback()
            raise
    
    def calculate_winrate(self, days=30, pair=None):
        """Calculate winrate statistics over a given period"""
        try:
            query = Signal.query.filter(
                Signal.timestamp >= (datetime.now() - timedelta(days=days))
            )
            
            if pair:
                query = query.filter(Signal.pair == pair)
            
            # Only include signals with outcomes
            query = query.filter(Signal.outcome.isnot(None))
            
            signals = query.all()
            
            total = len(signals)
            if total == 0:
                return {
                    'winrate': 0,
                    'total_trades': 0,
                    'avg_duration_mins': 0,
                    'recent_win_streak': 0,
                    'weighted_winrate': 0
                }
            
            wins = sum(1 for s in signals if s.outcome == 'WIN')
            
            # Calculate average duration
            durations = [s.duration for s in signals if s.duration is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Calculate recent win streak
            recent_signals = sorted(signals, key=lambda x: x.timestamp, reverse=True)
            streak = 0
            for s in recent_signals:
                if s.outcome == 'WIN':
                    streak += 1
                else:
                    break
            
            # Calculate weighted winrate (more weight to recent trades)
            weighted_total = 0
            weighted_wins = 0
            now = datetime.now()
            
            for s in signals:
                days_ago = (now - s.timestamp).days + 1  # +1 to avoid division by zero
                weight = 1 / days_ago  # More recent = higher weight
                
                weighted_total += weight
                if s.outcome == 'WIN':
                    weighted_wins += weight
            
            weighted_winrate = (weighted_wins / weighted_total) * 100 if weighted_total > 0 else 0
            
            return {
                'winrate': (wins / total) * 100,
                'total_trades': total,
                'avg_duration_mins': avg_duration,
                'recent_win_streak': streak,
                'weighted_winrate': weighted_winrate
            }
        
        except Exception as e:
            self.logger.error(f"Error calculating winrate: {e}")
            return {
                'winrate': 0,
                'total_trades': 0,
                'avg_duration_mins': 0,
                'recent_win_streak': 0,
                'weighted_winrate': 0,
                'error': str(e)
            }
    
    def pair_performance(self):
        """Get performance statistics by trading pair"""
        try:
            # Get all signals grouped by pair
            pairs = {}
            signals = Signal.query.all()
            
            for signal in signals:
                pair = signal.pair
                if pair not in pairs:
                    pairs[pair] = {'trades': 0, 'wins': 0}
                
                pairs[pair]['trades'] += 1
                
                if signal.outcome == 'WIN':
                    pairs[pair]['wins'] += 1
            
            # Calculate winrate for each pair
            for pair in pairs:
                if pairs[pair]['trades'] > 0:
                    pairs[pair]['winrate'] = pairs[pair]['wins'] / pairs[pair]['trades']
                else:
                    pairs[pair]['winrate'] = 0
            
            return pairs
            
        except Exception as e:
            self.logger.error(f"Error getting pair performance: {e}")
            return {}
    
    def backtest_strategy(self, pair, timeframe='4h', days=90):
        """Backtest a trading strategy on historical data"""
        try:
            # Fetch historical data from Binance
            data = self.binance_api.get_historical_data(pair, timeframe, days)
            
            if data is None or len(data) == 0:
                self.logger.error(f"No historical data available for {pair}")
                return None
            
            # Generate signals based on historical data
            signals = self._generate_historical_signals(data, pair)
            
            if not signals:
                return {
                    'pair': pair,
                    'period': f'{days} days',
                    'winrate': 0,
                    'avg_rr': 0,
                    'best_case': 0,
                    'worst_case': 0,
                    'total_signals': 0,
                    'error': 'No signals generated'
                }
            
            # Simulate each trade
            results = []
            for signal in signals:
                outcome = self._simulate_trade(signal, data)
                results.append(outcome)
            
            # Calculate backtest statistics
            total = len(results)
            wins = sum(1 for r in results if r['outcome'] == 'WIN')
            
            winrate = (wins / total) * 100 if total > 0 else 0
            avg_rr = sum(r['rr'] for r in results) / total if total > 0 else 0
            returns = [r['return'] for r in results]
            
            return {
                'pair': pair,
                'period': f'{days} days',
                'timeframe': timeframe,
                'winrate': winrate,
                'avg_rr': avg_rr,
                'best_case': max(returns) if returns else 0,
                'worst_case': min(returns) if returns else 0,
                'total_signals': total
            }
            
        except Exception as e:
            self.logger.error(f"Backtest error: {e}")
            return {
                'pair': pair,
                'period': f'{days} days',
                'error': str(e)
            }
    
    def _generate_historical_signals(self, data, pair):
        """Generate trading signals from historical data"""
        # This is a simple example - in a real system, you'd implement your trading strategy
        # Here we'll use a simple moving average crossover
        signals = []
        
        # Add moving averages for signal generation
        data['ma_short'] = data['close'].rolling(window=20).mean()
        data['ma_long'] = data['close'].rolling(window=50).mean()
        
        # Skip rows with NaN values (start of moving averages)
        data = data.dropna()
        
        for i in range(1, len(data)):
            # Detect crossovers
            prev_row = data.iloc[i-1]
            curr_row = data.iloc[i]
            
            # LONG signal: short MA crosses above long MA
            if prev_row['ma_short'] <= prev_row['ma_long'] and curr_row['ma_short'] > curr_row['ma_long']:
                entry = curr_row['close']
                sl = entry * 0.95  # 5% stop loss
                tp1 = entry * 1.05  # 5% take profit
                tp2 = entry * 1.08  # 8% take profit (optional)
                
                signal = {
                    'pair': pair,
                    'direction': 'LONG',
                    'entry': entry,
                    'sl': sl,
                    'tp1': tp1,
                    'tp2': tp2,
                    'index': i,
                    'timestamp': curr_row.name
                }
                signals.append(signal)
            
            # SHORT signal: short MA crosses below long MA
            elif prev_row['ma_short'] >= prev_row['ma_long'] and curr_row['ma_short'] < curr_row['ma_long']:
                entry = curr_row['close']
                sl = entry * 1.05  # 5% stop loss
                tp1 = entry * 0.95  # 5% take profit
                tp2 = entry * 0.92  # 8% take profit (optional)
                
                signal = {
                    'pair': pair,
                    'direction': 'SHORT',
                    'entry': entry,
                    'sl': sl,
                    'tp1': tp1,
                    'tp2': tp2,
                    'index': i,
                    'timestamp': curr_row.name
                }
                signals.append(signal)
        
        return signals
    
    def _simulate_trade(self, signal, data):
        """Simulate a trade to determine outcome"""
        start_idx = signal['index']
        direction = signal['direction']
        entry = signal['entry']
        sl = signal['sl']
        tp1 = signal['tp1']
        
        # Look at future price action
        future_data = data.iloc[start_idx:]
        
        outcome = 'PENDING'
        exit_price = None
        exit_idx = None
        
        for idx, row in future_data.iterrows():
            high = row['high']
            low = row['low']
            
            if direction == 'LONG':
                # Check if stop loss hit
                if low <= sl:
                    outcome = 'LOSS'
                    exit_price = sl
                    exit_idx = idx
                    break
                
                # Check if take profit hit
                if high >= tp1:
                    outcome = 'WIN'
                    exit_price = tp1
                    exit_idx = idx
                    break
            
            elif direction == 'SHORT':
                # Check if stop loss hit
                if high >= sl:
                    outcome = 'LOSS'
                    exit_price = sl
                    exit_idx = idx
                    break
                
                # Check if take profit hit
                if low <= tp1:
                    outcome = 'WIN'
                    exit_price = tp1
                    exit_idx = idx
                    break
        
        # If no exit found (end of data), use last price
        if outcome == 'PENDING':
            exit_price = future_data.iloc[-1]['close']
            exit_idx = future_data.index[-1]
            
            # Determine outcome based on price movement
            if direction == 'LONG':
                outcome = 'WIN' if exit_price > entry else 'LOSS'
            else:  # SHORT
                outcome = 'WIN' if exit_price < entry else 'LOSS'
        
        # Calculate return
        if direction == 'LONG':
            ret = (exit_price - entry) / entry * 100
            risk = (entry - sl) / entry * 100
            reward = (tp1 - entry) / entry * 100
        else:  # SHORT
            ret = (entry - exit_price) / entry * 100
            risk = (sl - entry) / entry * 100
            reward = (entry - tp1) / entry * 100
        
        # Calculate risk-reward ratio
        rr = reward / risk if risk > 0 else 0
        
        # Calculate duration
        duration = (exit_idx - start_idx) if exit_idx is not None else 0
        
        return {
            'outcome': outcome,
            'entry': entry,
            'exit': exit_price,
            'return': ret,
            'duration': duration,
            'rr': rr
        }
