from app import app  # noqa: F401
import os
import logging
import threading
import time
from telegram_bot import run_telegram_bot
from keep_alive import keep_alive
from auto_signals import start_signal_generator
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--scan', action='store_true')
args = parser.parse_args()

if args.scan:
    # Jalankan scan tanpa polling
    asyncio.run(scan_all())
else:
    # Mode normal
    application.run_polling()
# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Start Telegram bot in a separate thread
def start_telegram_bot():
    logger.info("Starting Telegram bot")
    run_telegram_bot()

# Start the keep-alive server
logger.info("Starting keep-alive server")
keep_alive()

# Start Telegram bot in background thread
logger.info("Starting Telegram bot thread")
bot_thread = threading.Thread(target=start_telegram_bot)
bot_thread.daemon = True
bot_thread.start()

# Start the signal generator
logger.info("Starting signal generator")
start_signal_generator()

# When running with gunicorn, this part won't execute
# But when running directly, it will start the Flask app
if __name__ == "__main__":
    logger.info("Starting web application directly")
    app.run(host='0.0.0.0', port=5000, debug=True)
