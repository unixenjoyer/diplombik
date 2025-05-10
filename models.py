from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    hourly_rate = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    total_earned = db.Column(db.Float, default=0.0)
    sessions = db.relationship('WorkSession', backref='user', lazy=True)

class WorkSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)