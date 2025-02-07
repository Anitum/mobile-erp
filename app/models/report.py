from app import db
from datetime import datetime
from pytz import timezone
class DailyReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    cleanliness_rating = db.Column(db.Integer)  # Add this line
    is_read = db.Column(db.Boolean, default=False)  # Add is_read field
    # Cleanliness Ratings
    floor_rating = db.Column(db.Integer)  # 1-5 stars
    floor_photo = db.Column(db.String(255))
    floor_remarks = db.Column(db.Text)
    
    bench_rating = db.Column(db.Integer)  # 1-5 stars
    bench_photo = db.Column(db.String(255))
    bench_remarks = db.Column(db.Text)

    whiteboard_rating = db.Column(db.Integer)  # 1-5 stars
    whiteboard_photo = db.Column(db.String(255))
    whiteboard_remarks = db.Column(db.Text)
    def formatted_date(self):
        if self.date:
            utc_date = self.date.replace(tzinfo=timezone('UTC'))
            local_date = utc_date.astimezone(timezone('Asia/Kolkata'))  # or your timezone
            return local_date.strftime('%Y-%m-%d %H:%M:%S %Z')
        return ''
    door_rating = db.Column(db.Integer)  # 1-5 stars
    door_photo = db.Column(db.String(255))
    door_remarks = db.Column(db.Text)
    
    walls_rating = db.Column(db.Integer)  # 1-5 stars
    walls_photo = db.Column(db.String(255))
    walls_remarks = db.Column(db.Text)
    
    dustbin_rating = db.Column(db.Integer)  # 1-5 stars
    dustbin_photo = db.Column(db.String(255))
    dustbin_remarks = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, reviewed
