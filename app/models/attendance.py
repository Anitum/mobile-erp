# models/attendance.py
from app import db
from datetime import datetime
from sqlalchemy import func
from app.models.user import User

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    check_in_time = db.Column(db.DateTime)
    check_in_location = db.Column(db.String(255))
    check_out_time = db.Column(db.DateTime)
    check_out_location = db.Column(db.String(255))
    remarks = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id],
                         backref=db.backref('attendances', lazy=True))

    recorder = db.relationship('User', foreign_keys=[recorded_by],
                            backref=db.backref('recorded_attendances', lazy=True))
    @staticmethod
    def get_today_attendance(user_id):
        today = datetime.utcnow().date()
        return Attendance.query.filter_by(
            user_id=user_id,
            date=today
        ).first()

    @staticmethod
    def mark_check_in(user_id, location):
        today = datetime.utcnow().date()
        attendance = Attendance.query.filter_by(
            user_id=user_id,
            date=today
        ).first()

        if not attendance:
            attendance = Attendance(
                user_id=user_id,
                date=today,
                status='present',
                check_in_time=datetime.utcnow(),
                check_in_location=location
            )
            db.session.add(attendance)
        db.session.commit()
    @classmethod
    def get_attendance_by_date(cls, date, role='all'):
        """
        Get attendance records for a specific date, optionally filtered by role
        
        Args:
            date: The date to get attendance for
            role: User role to filter by ('all', 'teacher', 'student', etc.)
        """
        query = cls.query.filter_by(date=date)
        if role != 'all':
            # Join with User model to filter by role
            query = query.join(cls.user).filter(User.role == role)
        return query.all()
    @staticmethod
    def mark_check_out(user_id, location):
        today = datetime.utcnow().date()
        attendance = Attendance.query.filter_by(
            user_id=user_id,
            date=today
        ).first()

        if attendance:
            attendance.check_out_time = datetime.utcnow()
            attendance.check_out_location = location
            db.session.commit()
        return attendance
