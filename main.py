from app import app  # noqa: F401
import os
import logging
import threading
import time
from telegram_bot import run_telegram_bot
from keep_alive import keep_alive

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Start Telegram bot in a separate thread
def start_telegram_bot():
    logger.info("Starting Telegram bot")
    run_telegram_bot()

if __name__ == "__main__":
    # Start keep-alive server
    logger.info("Starting keep-alive server")
    keep_alive()
    
    # Start Telegram bot in background thread
    bot_thread = threading.Thread(target=start_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask app
    logger.info("Starting web application")
    app.run(host='0.0.0.0', port=5000, debug=True)
