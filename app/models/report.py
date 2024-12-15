from app import db
from datetime import datetime

class DailyReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, reviewed
