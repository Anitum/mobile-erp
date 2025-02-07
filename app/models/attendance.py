# models/attendance.py
from app import db
from datetime import datetime
from sqlalchemy import func
from app.models.user import User
import pytz
from datetime import timedelta
from pytz import timezone

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
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).date()
        return Attendance.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
    @staticmethod
    def mark_check_in(user_id, location):
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)  # Get current IST time
        today = now.date()
        utc_now = now
        
        attendance = Attendance.query.filter_by(
            user_id=user_id,
            date=today
        ).first()

        if not attendance:
            attendance = Attendance(
                user_id=user_id,
                date=today,
                status='present',
                check_in_time=utc_now,
                check_in_location=location
            )
            db.session.add(attendance)
        db.session.commit()
        return attendance

    @staticmethod
    def mark_check_out(user_id, location):
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)  # Get current IST time
        today = now.date()
        utc_now = now

        attendance = Attendance.query.filter_by(
            user_id=user_id,
            date=today
        ).first()

        if attendance:
            attendance.check_out_time = utc_now
            attendance.check_out_location = location
            db.session.commit()
        return attendance

    @property
    def formatted_check_in_time(self):
        if not self.check_in_time:
            return '-'
        ist = pytz.timezone('Asia/Kolkata')
        utc_time = pytz.UTC.localize(self.check_in_time) if not self.check_in_time.tzinfo else self.check_in_time
        ist_time = utc_time.astimezone(ist)
        return ist_time.strftime('%I:%M %p')

    @property
    def formatted_check_out_time(self):
        if not self.check_out_time:
            return '-'
        ist = pytz.timezone('Asia/Kolkata')
        utc_time = pytz.UTC.localize(self.check_out_time) if not self.check_out_time.tzinfo else self.check_out_time
        ist_time = utc_time.astimezone(ist)
        return ist_time.strftime('%I:%M %p')

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


    @classmethod
    def get_weekly_attendance_stats(cls):
        """Get attendance statistics for the past 7 days"""
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)  # Last 7 days
        
        stats = []
        current_date = start_date
        
        while current_date <= end_date:
            # Get total users
            total_users = User.query.filter_by(is_active=True).count()
            
            # Get attendance for current date
            day_attendance = cls.query.filter_by(date=current_date).all()
            
            # Count present users
            present_count = len([a for a in day_attendance if a.status == 'present'])
            late_count = len([a for a in day_attendance if a.status == 'late'])
            absent_count = total_users - (present_count + late_count)
            
            # Calculate percentages
            present_percentage = round((present_count / total_users * 100) if total_users > 0 else 0, 1)
            absent_percentage = round((absent_count / total_users * 100) if total_users > 0 else 0, 1)
            late_percentage = round((late_count / total_users * 100) if total_users > 0 else 0, 1)
            
            stats.append({
                'date': current_date,
                'date_label': current_date.strftime('%b %d'),  # Format: Jan 01
                'day_name': current_date.strftime('%A'),       # Format: Monday
                'present': present_percentage,
                'absent': absent_percentage,
                'late': late_percentage,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'total': total_users
            })
            
            current_date += timedelta(days=1)
        
        return stats
    
    def get_daily_attendance_details(cls, date):
        """Get detailed attendance information for a specific date"""
        attendance_records = cls.query.filter_by(date=date)\
            .join(User)\
            .add_columns(
                User.first_name,
                User.last_name,
                User.role
            ).all()
        
        details = {
            'present': [],
            'absent': [],
            'late': []
        }
        
        for record, first_name, last_name, role in attendance_records:
            user_detail = {
                'name': f"{first_name} {last_name}",
                'role': role,
                'check_in': record.check_in_time.strftime('%H:%M') if record.check_in_time else None,
                'check_out': record.check_out_time.strftime('%H:%M') if record.check_out_time else None,
            }
            details[record.status].append(user_detail)
        
        return details
