from app import db
from datetime import datetime

class AdminAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=False)
    assigned_to = db.Column(db.String(20))  # 'all', 'teachers', 'students'
