# Babibu - Crypto Trading Signal Tracker

A 24/7 crypto trading signal tracker with Telegram bot integration and Binance API access for performance analysis.

## Features

- Dashboard with performance metrics and statistics
- Signal tracking and history
- Trading pair performance analysis
- Backtesting functionality
- Telegram bot integration for mobile management
- PostgreSQL database integration

## Setup

1. Install requirements: `pip install -r requirements.txt`
2. Configure environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `TELEGRAM_CHAT_ID`: Your chat ID for notifications
   - `BINANCE_API_KEY`: Binance API key
   - `BINANCE_API_SECRET`: Binance API secret
3. Run the application: `python main.py`

## Usage

- Web interface available at http://localhost:5000
- Use Telegram commands to interact with the bot:
  - `/stats` - View performance statistics
  - `/signal <pair> <direction> <entry> <tp1> <sl>` - Log a new signal
  - `/log <signal_id> <price>` - Update signal outcome
