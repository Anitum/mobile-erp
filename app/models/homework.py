from app import db
from datetime import datetime
from enum import Enum
class SubjectEnum(str, Enum):
    MATHEMATICS = "Mathematics"
    SCIENCE = "Science"
    ENGLISH = "English"
    HISTORY = "History"
    GEOGRAPHY = "Geography"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"
    COMPUTER_SCIENCE = "Computer Science"
    PHYSICAL_EDUCATION = "Physical Education"
    ART = "Art"
    MUSIC = "Music"

class Homework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    subject = db.Column(db.Enum(SubjectEnum), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HomeworkSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255))
    comments = db.Column(db.Text)
    status = db.Column(db.String(20), default='submitted')  # submitted, graded
