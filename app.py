import os
import logging

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trades.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with app
db.init_app(app)

# Import models and create tables
with app.app_context():
    from models import Signal
    from tracker import WinrateTracker
    db.create_all()

# Routes
@app.route('/')
def index():
    tracker = WinrateTracker()
    global_stats = tracker.calculate_winrate(days=30)
    recent_signals = Signal.query.order_by(Signal.timestamp.desc()).limit(5).all()
    pair_performance = tracker.pair_performance()
    
    # Get top 3 performing pairs with at least 5 trades
    top_pairs = []
    for pair, data in pair_performance.items():
        if data['trades'] >= 5:
            top_pairs.append({'pair': pair, 'winrate': data['winrate'] * 100, 'trades': data['trades']})
    
    top_pairs = sorted(top_pairs, key=lambda x: x['winrate'], reverse=True)[:3]
    
    return render_template('index.html', 
                          global_stats=global_stats, 
                          recent_signals=recent_signals,
                          top_pairs=top_pairs)

@app.route('/signals')
def signals():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    signals = Signal.query.order_by(Signal.timestamp.desc()).paginate(page=page, per_page=per_page)
    return render_template('signals.html', signals=signals)

@app.route('/pairs')
def pairs():
    tracker = WinrateTracker()
    pair_stats = tracker.pair_performance()
    
    # Convert to list for template
    pair_list = []
    for pair, data in pair_stats.items():
        pair_list.append({
            'pair': pair,
            'trades': data['trades'],
            'winrate': data['winrate'] * 100
        })
    
    # Sort by trade count
    pair_list = sorted(pair_list, key=lambda x: x['trades'], reverse=True)
    
    return render_template('pairs.html', pairs=pair_list)

@app.route('/backtest', methods=['GET', 'POST'])
def backtest():
    result = None
    
    if request.method == 'POST':
        pair = request.form.get('pair')
        days = int(request.form.get('days', 90))
        timeframe = request.form.get('timeframe', '4h')
        
        tracker = WinrateTracker()
        try:
            result = tracker.backtest_strategy(pair, timeframe, days)
        except Exception as e:
            flash(f"Backtest error: {str(e)}", "danger")
            logger.error(f"Backtest error: {str(e)}")
    
    return render_template('backtest.html', result=result)

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """API endpoint to get signals for AJAX requests"""
    signals = Signal.query.order_by(Signal.timestamp.desc()).limit(50).all()
    signals_data = []
    
    for signal in signals:
        signals_data.append({
            'id': signal.id,
            'pair': signal.pair,
            'direction': signal.direction,
            'entry': signal.entry,
            'tp1': signal.tp1,
            'tp2': signal.tp2,
            'sl': signal.sl,
            'timestamp': signal.timestamp.isoformat(),
            'outcome': signal.outcome,
            'closed_at': signal.closed_at,
            'duration': signal.duration
        })
    
    return jsonify(signals_data)

@app.route('/api/winrate', methods=['GET'])
def get_winrate():
    """API endpoint to get winrate statistics for charts"""
    days = request.args.get('days', 30, type=int)
    tracker = WinrateTracker()
    stats = tracker.calculate_winrate(days=days)
    
    return jsonify(stats)

@app.route('/api/pairs', methods=['GET'])
def get_pairs():
    """API endpoint to get pair performance statistics"""
    tracker = WinrateTracker()
    pairs = tracker.pair_performance()
    
    return jsonify(pairs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
