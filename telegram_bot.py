import os
import logging
import asyncio
import time
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from tracker import WinrateTracker
import binance_api

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7747406899:AAGTcw4NK2oYRH27M-PHR1GIc7rpfGKe0EE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5125770095")

# Create WinrateTracker instance
tracker = WinrateTracker()
binance = binance_api.BinanceAPI()

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    await update.message.reply_text(
        "👋 Welcome to the Crypto Signal Tracker Bot!\n\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with all available commands."""
    help_text = (
        "📚 **Available Commands:**\n\n"
        "/stats - View overall performance statistics\n"
        "/signal <pair> <direction> <entry> <tp1> <sl> - Log a new signal\n"
        "/log <signal_id> <price> - Update signal outcome\n"
        "/pair <pair_name> - View performance for a specific pair\n"
        "/backtest <pair> <days> - Run backtest on a pair\n"
        "/price <symbol> - Get current price of a crypto\n"
    )
    await update.message.reply_text(help_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show performance statistics."""
    global_stats = tracker.calculate_winrate(days=30)
    
    response = f"""
📊 **Performance Report (Last 30 Days)** 📊

✅ **Winrate:** {global_stats['winrate']:.1f}%
📈 **Total Trades:** {global_stats['total_trades']}
⏳ **Avg Duration:** {global_stats['avg_duration_mins']:.1f} mins
🔥 **Current Win Streak:** {global_stats['recent_win_streak']}
⚖️ **Weighted Winrate:** {global_stats['weighted_winrate']:.1f}%

Use /pair <name> to see performance by pair
    """
    await update.message.reply_text(response)

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log a new trading signal."""
    try:
        args = context.args
        
        if len(args) < 5:
            await update.message.reply_text(
                "❌ Format error. Use:\n"
                "/signal <pair> <direction> <entry> <tp1> <sl> [tp2]"
            )
            return
        
        pair = args[0].upper()
        direction = args[1].upper()
        entry = float(args[2])
        tp1 = float(args[3])
        sl = float(args[4])
        tp2 = float(args[5]) if len(args) > 5 else None
        
        # Validate direction
        if direction not in ['LONG', 'SHORT']:
            await update.message.reply_text("❌ Direction must be LONG or SHORT")
            return
        
        # Create signal dictionary
        signal = {
            'pair': pair,
            'direction': direction,
            'entry': entry,
            'tp1': tp1,
            'tp2': tp2,
            'sl': sl
        }
        
        # Log the signal
        signal_id = await tracker.log_signal(signal)
        
        # Calculate risk-reward ratio
        if direction == 'LONG':
            risk = entry - sl
            reward = tp1 - entry
        else:  # SHORT
            risk = sl - entry
            reward = entry - tp1
            
        rr = reward / risk if risk > 0 else 0
        
        response = f"""
🔔 **New Signal #{signal_id} Logged** 🔔

📊 **{pair} {direction}**
📉 Entry: {entry}
🎯 TP1: {tp1}
🛑 SL: {sl}
⚖️ R:R Ratio: {rr:.2f}

Use /log {signal_id} <price> to update outcome
        """
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error logging signal: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update signal outcome."""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Format error. Use: /log <signal_id> <price>")
            return
        
        signal_id = int(context.args[0])
        closed_price = float(context.args[1])
        
        # Update the signal outcome
        success = await tracker.update_outcome(signal_id, closed_price)
        
        if success:
            await update.message.reply_text(f"✅ Trade #{signal_id} updated at price {closed_price}!")
        else:
            await update.message.reply_text(f"❌ Could not find signal with ID {signal_id}")
            
    except Exception as e:
        logger.error(f"Error updating signal: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def pair_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show performance for a specific pair."""
    if len(context.args) < 1:
        await update.message.reply_text("❌ Please specify a trading pair. Example: /pair BTCUSDT")
        return
    
    pair = context.args[0].upper()
    stats = tracker.calculate_winrate(days=30, pair=pair)
    
    response = f"""
📊 **{pair} Performance (30 Days)** 📊

✅ **Winrate:** {stats['winrate']:.1f}%
📈 **Total Trades:** {stats['total_trades']}
⏳ **Avg Duration:** {stats['avg_duration_mins']:.1f} mins

Use /backtest {pair} 90 to see backtest results
    """
    
    await update.message.reply_text(response)

async def backtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run a backtest on a specific pair."""
    try:
        if len(context.args) < 1:
            await update.message.reply_text("❌ Please specify a trading pair. Example: /backtest BTCUSDT 90")
            return
        
        pair = context.args[0].upper()
        days = int(context.args[1]) if len(context.args) > 1 else 90
        timeframe = context.args[2] if len(context.args) > 2 else '4h'
        
        await update.message.reply_text(f"⏳ Running backtest for {pair} over {days} days on {timeframe} timeframe...")
        
        # Run backtest
        result = tracker.backtest_strategy(pair, timeframe, days)
        
        if result is None or 'error' in result:
            error = result.get('error', 'Unknown error') if result else 'Failed to get data'
            await update.message.reply_text(f"❌ Backtest failed: {error}")
            return
        
        response = f"""
🧪 **Backtest Results** 🧪

📊 **{result['pair']} ({result['timeframe']} - {result['period']})**
✅ **Winrate:** {result['winrate']:.1f}%
⚖️ **Avg Risk/Reward:** {result['avg_rr']:.2f}
🔥 **Best Return:** {result['best_case']:.2f}%
💧 **Worst Return:** {result['worst_case']:.2f}%
🔢 **Total Signals:** {result['total_signals']}
        """
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current price of a cryptocurrency."""
    if len(context.args) < 1:
        await update.message.reply_text("❌ Please specify a symbol. Example: /price BTCUSDT")
        return
    
    symbol = context.args[0].upper()
    
    try:
        price_info = binance.get_current_price(symbol)
        
        if price_info:
            price = price_info['price']
            change = price_info.get('change_24h', 0)
            response = f"""
💰 **{symbol} Price** 💰

Current: {price}
24h Change: {change:.2f}%
            """
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f"❌ Could not get price for {symbol}")
    
    except Exception as e:
        logger.error(f"Error getting price: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

def run_telegram_bot():
    """
    Start the Telegram bot in a way that works with threading.
    This will work correctly when running in a separate thread.
    """
    logger.info("Starting telegram bot...")
    
    while True:
        try:
            # Must create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create application
            application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            
            # Register command handlers
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("stats", stats_command))
            application.add_handler(CommandHandler("signal", signal_command))
            application.add_handler(CommandHandler("log", log_command))
            application.add_handler(CommandHandler("pair", pair_command))
            application.add_handler(CommandHandler("backtest", backtest_command))
            application.add_handler(CommandHandler("price", price_command))
            
            # Run the application with our own event loop
            # Disable signal handlers which cause issues in threads
            logger.info("Starting Telegram bot with custom polling")
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False,
                stop_signals=None  # Disable signal handling
            )
            
            # If we get here, the bot exited normally, just break the loop
            break
            
        except Exception as e:
            logger.error(f"Error in Telegram bot: {str(e)}")
            logger.info("Waiting 60 seconds before retrying...")
            time.sleep(60)
            
    logger.info("Telegram bot stopped")

if __name__ == "__main__":
    run_telegram_bot()
