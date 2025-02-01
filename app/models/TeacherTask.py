from app import db
from datetime import datetime

class TeacherTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    completion_notes = db.Column(db.Text)
    completion_image = db.Column(db.String(255))
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    task_file = db.Column(db.String(255))  # Add this line in TeacherTask model

    # Relationships
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref='created_tasks')
