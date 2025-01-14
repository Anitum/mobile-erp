from app import db
from datetime import datetime

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    remarks = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships with explicit foreign keys
    user = db.relationship('User', 
                         foreign_keys=[user_id],
                         backref=db.backref('attendances', lazy=True))
    recorder = db.relationship('User',
                            foreign_keys=[recorded_by],
                            backref=db.backref('recorded_attendances', lazy=True))


    @staticmethod
    def get_attendance_by_date(date, role=None):
        from app.models.user import User  # Import here to avoid circular imports
        query = Attendance.query
        if role:
            # Explicitly join with User using the user_id foreign key
            query = query.join(User, Attendance.user_id == User.id)
            query = query.filter(User.role == role)
        query = query.filter(Attendance.date == date)
        return query.all()
    @staticmethod
    def get_user_attendance(user_id, start_date=None, end_date=None):
        query = Attendance.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        return query.order_by(Attendance.date.desc()).all()
