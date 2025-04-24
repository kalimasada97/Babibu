from app import db
from datetime import datetime

class Signal(db.Model):
    __tablename__ = 'signals'
    
    id = db.Column(db.Integer, primary_key=True)
    pair = db.Column(db.String(20), nullable=False)
    direction = db.Column(db.String(10), nullable=False)  # LONG or SHORT
    entry = db.Column(db.Float, nullable=False)
    tp1 = db.Column(db.Float, nullable=False)  # Take profit 1
    tp2 = db.Column(db.Float, nullable=True)   # Take profit 2 (optional)
    sl = db.Column(db.Float, nullable=False)   # Stop loss
    timestamp = db.Column(db.DateTime, default=datetime.now)
    outcome = db.Column(db.String(10), nullable=True)  # WIN, LOSS or None if not closed
    closed_at = db.Column(db.Float, nullable=True)  # Price at which the trade was closed
    duration = db.Column(db.Integer, nullable=True)  # Duration in minutes
    
    def __repr__(self):
        return f"<Signal {self.id}: {self.pair} {self.direction}>"
    
    @property
    def risk_reward_ratio(self):
        if self.direction == 'LONG':
            reward = self.tp1 - self.entry
            risk = self.entry - self.sl
        else:  # SHORT
            reward = self.entry - self.tp1
            risk = self.sl - self.entry
            
        if risk == 0:
            return 0
        return reward / risk
    
    @property
    def profit_loss(self):
        if not self.closed_at:
            return None
            
        if self.direction == 'LONG':
            return (self.closed_at - self.entry) / self.entry * 100
        else:  # SHORT
            return (self.entry - self.closed_at) / self.entry * 100
    
    @property
    def is_win(self):
        if not self.outcome:
            return None
        return self.outcome == 'WIN'
