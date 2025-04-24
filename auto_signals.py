import logging
import time
import threading
import random
from datetime import datetime, timedelta
import requests
import os
from binance_api import BinanceAPI
from tracker import WinrateTracker

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7747406899:AAGTcw4NK2oYRH27M-PHR1GIc7rpfGKe0EE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5125770095")

class SignalGenerator:
    def __init__(self):
        self.binance_api = BinanceAPI()
        self.tracker = WinrateTracker()
        self.running = False
        self.thread = None
        self.pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"]
        
    def start(self):
        """Start the signal generator in a separate thread"""
        if self.running:
            logger.info("Signal generator already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Signal generator started")
        
    def stop(self):
        """Stop the signal generator"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("Signal generator stopped")
        
    def _run(self):
        """Main loop for generating signals"""
        while self.running:
            try:
                # Generate a random signal every 1-12 hours
                sleep_time = random.randint(1800, 7200)  # 30 min to 2 hours for testing
                logger.info(f"Sleeping for {sleep_time} seconds before next signal")
                
                # Sleep in small chunks to allow for clean shutdown
                for _ in range(sleep_time // 10):
                    if not self.running:
                        break
                    time.sleep(10)
                
                if not self.running:
                    break
                    
                # Generate and send a random signal
                self._generate_random_signal()
                
            except Exception as e:
                logger.error(f"Error in signal generator: {e}")
                time.sleep(60)  # Wait a minute if there's an error
    
    def _generate_random_signal(self):
        """Generate a random trading signal and send it to Telegram"""
        try:
            # Select a random pair
            pair = random.choice(self.pairs)
            
            # Get current price
            price_info = self.binance_api.get_current_price(pair)
            if not price_info:
                logger.error(f"Could not get price for {pair}")
                return
                
            current_price = price_info['price']
            
            # Randomly choose direction
            direction = random.choice(["LONG", "SHORT"])
            
            # Calculate entry, stop loss, and take profit based on direction
            if direction == "LONG":
                entry = current_price
                sl = entry * 0.97  # 3% below entry
                tp1 = entry * 1.05  # 5% above entry
                tp2 = entry * 1.08  # 8% above entry
            else:  # SHORT
                entry = current_price
                sl = entry * 1.03  # 3% above entry
                tp1 = entry * 0.95  # 5% below entry
                tp2 = entry * 0.92  # 8% below entry
                
            # Create signal dict
            signal = {
                'pair': pair,
                'direction': direction,
                'entry': entry,
                'tp1': tp1,
                'tp2': tp2,
                'sl': sl
            }
            
            # Log to database async
            self._log_signal_to_db(signal)
            
            # Send to Telegram
            self._send_to_telegram(signal)
            
        except Exception as e:
            logger.error(f"Error generating random signal: {e}")
    
    def _log_signal_to_db(self, signal):
        """Log the signal to the database"""
        try:
            # Since we can't use async in this context, use the synchronous method
            from app import db
            from models import Signal
            
            # Create the signal record
            new_signal = Signal(
                pair=signal['pair'],
                direction=signal['direction'],
                entry=signal['entry'],
                tp1=signal['tp1'],
                tp2=signal.get('tp2'),
                sl=signal['sl'],
                timestamp=datetime.now()
            )
            
            # Add to database
            db.session.add(new_signal)
            db.session.commit()
            
            logger.info(f"Signal logged to database with ID {new_signal.id}")
            return new_signal.id
        except Exception as e:
            logger.error(f"Error logging signal to database: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    def _send_to_telegram(self, signal):
        """Send the signal to Telegram"""
        try:
            pair = signal['pair']
            direction = signal['direction']
            entry = signal['entry']
            tp1 = signal['tp1']
            tp2 = signal.get('tp2')
            sl = signal['sl']
            
            # Calculate risk-reward ratio
            if direction == 'LONG':
                risk = entry - sl
                reward = tp1 - entry
            else:  # SHORT
                risk = sl - entry
                reward = entry - tp1
                
            rr = reward / risk if risk > 0 else 0
            
            # Format message
            message = f"""
🔔 **New Signal Generated** 🔔

📊 **{pair} {direction}**
📉 Entry: {entry:.4f}
🎯 TP1: {tp1:.4f}
"""
            
            if tp2:
                message += f"🎯 TP2: {tp2:.4f}\n"
                
            message += f"""🛑 SL: {sl:.4f}
⚖️ R:R Ratio: {rr:.2f}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
            
            # Send message
            self._send_telegram_message(message)
            logger.info(f"Signal sent to Telegram: {pair} {direction}")
            
        except Exception as e:
            logger.error(f"Error sending signal to Telegram: {e}")
    
    def _send_telegram_message(self, message):
        """Send a message to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
            else:
                logger.info("Telegram message sent successfully")
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")

# Global instance
signal_generator = SignalGenerator()

def start_signal_generator():
    """Start the signal generator"""
    signal_generator.start()
    
def stop_signal_generator():
    """Stop the signal generator"""
    signal_generator.stop()

# For testing
if __name__ == "__main__":
    start_signal_generator()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_signal_generator()