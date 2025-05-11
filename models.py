from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.orm import validates

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    hourly_rate = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    total_earned = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sessions = db.relationship('WorkSession', backref='user', lazy=True)

    @validates('hourly_rate')
    def validate_rate(self, key, rate):
        rate = float(rate)
        if rate < 0:
            raise ValueError("Ставка не может быть отрицательной")
        return round(rate, 2)

    @validates('username')
    def validate_username(self, key, username):
        if len(username) < 3:
            raise ValueError("Логин слишком короткий")
        return username

class WorkSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)

    @property
    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        return 0